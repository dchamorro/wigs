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
make pdf                         # PDF de resumen del proyecto (stack + próximos pasos)
```

## Producción
1. `deploy/setup-wig.sh` en el PGX (Samba + nginx + timer).
2. `make deploy PGX=usuario@ip` para publicar marcador.html.
3. El tablero compartido vive en `\\PGX\WIG`; los dueños digitan cada lunes.

## Publicación en Azure (pantallas de la oficina)

El marcador se publica en Azure Static Web Apps con los datos incluidos.
**Decisión de seguridad:** el sitio exige **login de empresa** (Entra ID de un
solo tenant; solo cuentas `@caobagroup.com`) vía `auth` en
`web/staticwebapp.config.json` — todo el contenido (`marcador.html`,
`tablero.xlsx`) está detrás de `allowedRoles: ["authenticated"]`. La TV de la
oficina NO usa este sitio: lee del PGX por LAN sin login; Azure es la copia
para acceso remoto autenticado. Requiere el tier **Standard** (~$9/mes,
cubierto por el crédito de Azure). Setup del portal: `docs/AZURE_LOGIN.md`.

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
3. Registrar la app en Entra ID y poner el **TENANT_ID** en el `openIdIssuer`
   de `web/staticwebapp.config.json` (reemplazar `REEMPLAZAR-TENANT-ID`), más
   los secrets `AAD_CLIENT_ID` / `AAD_CLIENT_SECRET` en la Static Web App. El
   workflow se niega a deployar mientras quede el placeholder. Pasos del portal
   en `docs/AZURE_LOGIN.md`.
