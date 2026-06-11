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

Además del PGX, el marcador se publica en Azure Static Web Apps (cubierto por
el crédito de Azure; el tier Free alcanza). Cada push a `main` que toque
`web/` redeploya el sitio: el workflow copia `marcador.html` (con
`DATA_URL: 'tablero.xlsx'` ya configurado, igual que en el PGX) y
`web/tablero.xlsx` si existe.

**Configuración inicial (una vez):**
1. En el portal de Azure crear una **Static Web App** (plan Free), fuente
   GitHub → repo `dchamorro/wigs`, rama `main`, preset *Custom*.
2. Azure agrega el secret `AZURE_STATIC_WEB_APPS_API_TOKEN` al repo. Si Azure
   genera su propio workflow, borrarlo — ya existe
   `.github/workflows/azure-static-web-apps.yml`.

**Actualización semanal de datos:**
```
make publicar DATOS=/ruta/al/tablero_con_datos.xlsx
```
Copia el Excel (con los datos que digitaron los dueños en `\\PGX\WIG`) a
`web/tablero.xlsx`, hace commit y push — Azure redeploya solo. Importante:
el archivo debe venir guardado desde Excel/LibreOffice (valores calculados);
ver la nota de recalc en CLAUDE.md.
