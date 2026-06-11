#!/bin/bash
# ============================================================
#  setup-wig.sh — Marcador WIG en Lenovo PGX (DGX OS / Ubuntu)
#  Instala: Samba (carpeta compartida) + nginx (marcador web)
#           + timer que valida y publica el Excel cada 5 min
#  Uso:  sudo bash setup-wig.sh
# ============================================================
set -euo pipefail

# ---------- CONFIGURACIÓN (editar si hace falta) ----------
SHARE_DIR=/srv/wig                       # carpeta compartida por red
WEB_DIR=/var/www/html/wig                # carpeta servida por nginx
XLSX_NAME="Tablero_WIG_4DX_GBM_v2_compartido.xlsx"
SMB_USER=tablero                         # usuario para mapear la unidad
PUBLISH_EVERY=5min                       # frecuencia de publicación
INSTALL_TAILSCALE=no                     # yes = instalar Tailscale (acceso remoto dueños)
# -----------------------------------------------------------

[ "$EUID" -eq 0 ] || { echo "Ejecutar con sudo"; exit 1; }

echo "==> Instalando paquetes..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq samba nginx python3 >/dev/null

echo "==> Creando carpetas..."
mkdir -p "$SHARE_DIR" "$WEB_DIR"
groupadd -f wig
chgrp wig "$SHARE_DIR"
chmod 2775 "$SHARE_DIR"

echo "==> Configurando Samba..."
if ! grep -q '^\[WIG\]' /etc/samba/smb.conf; then
cat >> /etc/samba/smb.conf <<EOF

[WIG]
   path = $SHARE_DIR
   writable = yes
   valid users = @wig
   create mask = 0664
   directory mask = 2775
EOF
fi
if ! id "$SMB_USER" &>/dev/null; then
  useradd -M -s /usr/sbin/nologin -G wig "$SMB_USER"
  echo ">>> Defina la contraseña de red para el usuario '$SMB_USER':"
  smbpasswd -a "$SMB_USER"
else
  usermod -aG wig "$SMB_USER"
fi
systemctl restart smbd && systemctl enable -q smbd

echo "==> Script de publicación (valida el archivo antes de servirlo)..."
cat > /usr/local/bin/wig-publish.sh <<EOF
#!/bin/bash
SRC="$SHARE_DIR/$XLSX_NAME"
DST="$WEB_DIR/tablero.xlsx"
[ -f "\$SRC" ] || exit 0
if python3 -c "import zipfile;zipfile.ZipFile('\$SRC').testzip()" 2>/dev/null; then
  cp "\$SRC" "\$DST.tmp" && mv "\$DST.tmp" "\$DST"
fi
EOF
chmod +x /usr/local/bin/wig-publish.sh

cat > /etc/systemd/system/wig-publish.service <<EOF
[Unit]
Description=Publica el tablero WIG validado hacia nginx
[Service]
Type=oneshot
ExecStart=/usr/local/bin/wig-publish.sh
EOF

cat > /etc/systemd/system/wig-publish.timer <<EOF
[Unit]
Description=Timer de publicación del tablero WIG
[Timer]
OnBootSec=1min
OnUnitActiveSec=$PUBLISH_EVERY
[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable -q --now wig-publish.timer
systemctl enable -q nginx && systemctl restart nginx

if [ "$INSTALL_TAILSCALE" = "yes" ]; then
  echo "==> Instalando Tailscale..."
  curl -fsSL https://tailscale.com/install.sh | sh
  echo ">>> Ejecute 'sudo tailscale up' para unir el PGX al tailnet."
fi

IP=$(hostname -I | awk '{print $1}')
echo
echo "============================================================"
echo " Listo. Pasos finales:"
echo " 1. Copie marcador.html (Marcador_WIG_TV_v4.html) a: $WEB_DIR/marcador.html"
echo "    y en su CONFIG ponga: DATA_URL: 'tablero.xlsx'"
echo " 2. Copie el Excel inicial a: $SHARE_DIR/$XLSX_NAME"
echo " 3. Dueños mapean la unidad:  \\\\$IP\\WIG   (usuario: $SMB_USER)"
echo " 4. TV en kiosko:  chrome --kiosk http://$IP/wig/marcador.html"
echo " Verificar publicación:  systemctl status wig-publish.timer"
echo "============================================================"
