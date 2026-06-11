# Marcador WIG 4DX — GBM

Scoreboard 4DX: Excel compartido (datos) + marcador HTML para TV (visual) +
PGX (Samba + nginx) como servidor. Ver **CLAUDE.md** para la arquitectura,
el contrato Excel↔parser y los flujos de trabajo.

## Inicio rápido
```
pip install openpyxl            # y LibreOffice para recalc
make build                      # construye el tablero
make demo && open dist/demo.html  # ver el marcador con datos dummy
make test                       # validar el contrato
```

## Producción
1. `deploy/setup-wig.sh` en el PGX (Samba + nginx + timer).
2. `make deploy PGX=usuario@ip` para publicar marcador.html.
3. El tablero compartido vive en `\\PGX\WIG`; los dueños digitan cada lunes.

## Publicación en Azure (acceso fuera de la LAN)

Además del PGX, el marcador se publica en Azure Static Web Apps (plan Free,
cubierto por el crédito de Azure). Cada push a `main` que toque `web/`
redeploya el sitio automáticamente.

**Decisión de seguridad:** el sitio se publica **en modo arrastrar-y-soltar**
— `tablero.xlsx` NO se sube a Azure porque contiene datos financieros
internos y el sitio aún no tiene login. Para ver el marcador fuera de la LAN:
abrir la URL del sitio y arrastrar el Excel (copia de `\\PGX\WIG`) sobre la
página. El archivo debe venir guardado desde Excel (valores calculados; ver
la nota de recalc en CLAUDE.md).

**Configuración inicial (una vez):**
1. En el portal de Azure crear una **Static Web App** (plan Free), fuente
   GitHub → repo `dchamorro/wigs`, rama `main`, preset *Custom*.
2. Azure agrega el secret `AZURE_STATIC_WEB_APPS_API_TOKEN` al repo. Si Azure
   genera su propio workflow, borrarlo — ya existe
   `.github/workflows/azure-static-web-apps.yml`.

**Pendiente (decidir):** habilitar login en el sitio (Entra ID con usuarios
invitados — el plan Free permite hasta 25) y entonces sí publicar
`tablero.xlsx` automáticamente para que el marcador cargue solo.
