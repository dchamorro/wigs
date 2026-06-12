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

## Publicación en Azure (pantallas de la oficina)

El marcador se publica en Azure Static Web Apps con los datos incluidos.
**Decisión de seguridad:** el sitio está restringido por IP a la red de la
oficina (`networking.allowedIpRanges` en `web/staticwebapp.config.json`) —
solo las pantallas/equipos en la oficina pueden verlo. Es la misma frontera
de confianza que el PGX en la LAN. Requiere el tier **Standard** (~$9/mes,
cubierto por el crédito de Azure).

**Ritual del lunes (1 persona, Plans & Controls):**
```
make publicar DATOS=/ruta/al/tablero_con_datos.xlsx
```
Valida el archivo (pruebas de contrato + chequeo de recalc — un tablero roto
o sin valores calculados NO se publica), lo copia a `web/tablero.xlsx`, hace
commit y push — Azure redeploya solo en ~1 minuto. El archivo debe venir
guardado desde Excel (la copia de `\\PGX\WIG` ya cumple).

**Configuración inicial (una vez):**
1. En el portal de Azure crear una **Static Web App**, fuente GitHub →
   repo `dchamorro/wigs`, rama `main`, preset *Custom*; subir el plan a
   **Standard** (Hosting plan).
2. Azure agrega el secret `AZURE_STATIC_WEB_APPS_API_TOKEN` al repo. Si Azure
   genera su propio workflow, borrarlo — ya existe
   `.github/workflows/azure-static-web-apps.yml`.
3. Poner la IP pública de la oficina en `web/staticwebapp.config.json`
   (reemplazar `REEMPLAZAR-IP-OFICINA`). El workflow se niega a deployar
   mientras quede el placeholder. Si la oficina tiene varias salidas a
   internet, agregar cada una al array.
