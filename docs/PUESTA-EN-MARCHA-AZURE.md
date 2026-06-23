# Marcador WIG en Azure — puesta en marcha y proceso semanal

Plan operativo para publicar el marcador en Azure Static Web Apps y mantenerlo
actualizado cada semana. Audiencia: quien configura Azure (una vez) y
Plans & Controls (cada lunes).

**La idea en una frase:** los dueños siguen digitando en el Excel compartido
(`\\PGX\WIG`) como siempre; cada lunes una persona publica ese archivo con un
comando, y queda disponible para **acceso remoto autenticado** (login de empresa,
solo cuentas `@caobagroup.com`). La TV de la oficina NO usa este sitio: lee del
PGX por LAN sin login (ver `deploy/setup-wig.sh`); Azure es la copia para verlo
fuera de la oficina con cuenta de empresa.

---

## Parte 1 — Puesta en marcha (una sola vez, ~30 min)

### Paso 1. Tener el workflow en `main`
El repo (`dchamorro/wigs`) ya trae el workflow de publicación
(`.github/workflows/azure-static-web-apps.yml`), el comando semanal y el login
de empresa (Entra ID) en `web/staticwebapp.config.json`.

### Paso 2. Crear el sitio en Azure (~10 min)
1. Entrar a [portal.azure.com](https://portal.azure.com) → **Create a resource**
   → **Static Web App**.
2. Llenar:
   - **Subscription / Resource group:** la suscripción con el crédito; crear
     grupo `rg-marcador-wig` si no existe.
   - **Name:** `marcador-wig` (o similar).
   - **Hosting plan:** **Standard** (≈ $9/mes — necesario para el login de
     empresa con Entra ID; sale del crédito de $200).
   - **Source:** GitHub → repo `dchamorro/wigs`, rama `main`.
   - **Build presets:** *Custom*; app location `/`; output vacío.
3. Crear. Azure conecta el repo y agrega solo el secret
   `AZURE_STATIC_WEB_APPS_API_TOKEN`.
4. **Importante:** Azure habrá commiteado su propio workflow en
   `.github/workflows/` — borrarlo. El bueno es
   `azure-static-web-apps.yml` (ya existe en el repo).
5. Anotar la URL del sitio (algo como `https://<nombre>.azurestaticapps.net`),
   visible en el Overview del recurso.

### Paso 3. Configurar el login de empresa (Entra ID, ~10 min)
1. Registrar la app en Entra ID (un solo tenant, solo `@caobagroup.com`) y
   obtener el **TENANT_ID**, el **CLIENT_ID** y un **CLIENT_SECRET**. Pasos
   detallados del portal en [`AZURE_LOGIN.md`](./AZURE_LOGIN.md).
2. En `web/staticwebapp.config.json`, reemplazar `REEMPLAZAR-TENANT-ID` en el
   `openIdIssuer` por el tenant real. En la Static Web App, agregar los secrets
   de aplicación `AAD_CLIENT_ID` y `AAD_CLIENT_SECRET`.
3. Commit y push a `main`. (El workflow se niega a publicar mientras el
   placeholder `REEMPLAZAR-TENANT-ID` siga ahí — es a propósito, para que el
   sitio nunca salga con el login mal configurado.)

### Paso 4. Preparar la máquina que publica (~10 min, la de P&C)
Requisitos: acceso al repo en GitHub, git configurado, Python 3.
```
git clone https://github.com/dchamorro/wigs && cd wigs
pip install openpyxl
```

### Paso 5. Primera publicación y verificación
1. Copiar el tablero con datos desde `\\PGX\WIG` a la máquina.
2. `make publicar DATOS=/ruta/al/tablero.xlsx`
3. Esperar ~1 minuto y abrir la URL del sitio: debe redirigir al **login de
   empresa**. Iniciar sesión con una cuenta `@caobagroup.com` → se ve el
   marcador con datos, cargado solo (sin arrastrar nada).
4. Probar con una cuenta que NO sea `@caobagroup.com` (o sin sesión): el sitio
   **niega el acceso / redirige al login** y no muestra datos. Si deja entrar a
   cualquiera, revisar que el Hosting plan sea Standard y que `auth` +
   `allowedRoles: ["authenticated"]` estén bien en `staticwebapp.config.json`.

### Paso 6. Las pantallas
La TV de la oficina **no** usa este sitio: corre `marcador.html` servido por el
PGX en la LAN (sin login), configurado con `deploy/setup-wig.sh`. Azure es para
acceso remoto: cada persona abre la URL en su navegador e inicia sesión con su
cuenta de empresa. La página refresca los datos sola cada 10 minutos y rota
entre los WIGs.

---

## Parte 2 — Proceso semanal (cada lunes, ~10 min)

**Quién:** una persona de Plans & Controls.
**Cuándo:** lunes en la mañana, después de que los dueños digitaron y antes
de la reunión WIG.

1. **Los dueños digitan** sus reales de la semana en el tablero compartido
   (`\\PGX\WIG`), como siempre — guardar y cerrar.
2. **P&C revisa** el tablero: abrirlo, verificar que los datos de la semana
   estén completos y razonables, **guardar y cerrar** (ese guardado desde
   Excel deja los valores calculados que el marcador necesita).
3. **Copiar** el archivo a la máquina de P&C.
4. **Publicar:**
   ```
   make publicar DATOS=/ruta/al/tablero.xlsx
   ```
   El comando valida antes de publicar — si el archivo está roto, sin
   recalcular, o alguien cambió la estructura, **se detiene y no publica**
   (las pantallas siguen mostrando la semana anterior, nunca un tablero roto).
5. **Verificar** (~1 min después): abrir la URL del sitio y confirmar que
   aparece la semana nueva.

### Si el paso 4 falla

| Mensaje | Qué significa | Qué hacer |
|---|---|---|
| `Sin valores cacheados: ejecutar recalc` | El archivo no se guardó desde Excel | Abrirlo en Excel, guardar, volver a intentar |
| `contrato roto` / falla de layout | Alguien cambió la estructura del tablero (filas, columnas, pestañas) | No publicar; revisar qué cambió contra CLAUDE.md o avisar al responsable del repo |
| `Publicar solo desde main` | El repo local está en otra rama | `git checkout main` y reintentar |
| `git push` rechazado | El repo local quedó atrás | El comando ya hace `git pull --rebase`; si aun así falla, `git pull` manual y reintentar |

### Si el sitio no se actualiza
1. Revisar la pestaña **Actions** del repo en GitHub — el workflow del deploy
   debe estar en verde. Si está rojo, el mensaje de error dice qué pasó
   (token vencido, placeholder `REEMPLAZAR-TENANT-ID` sin reemplazar, etc.).
2. Refrescar la página con Ctrl+Shift+R (aunque los headers ya evitan caché).

---

## Mantenimiento ocasional

- **Vencimiento del CLIENT_SECRET de Entra:** los secrets de Entra ID expiran
  (1–2 años). Cuando el login deje de funcionar, generar un secret nuevo en el
  registro de la app y actualizar `AAD_CLIENT_SECRET` en la Static Web App.
- **Dar acceso remoto a alguien:** basta con que tenga cuenta `@caobagroup.com`;
  abre la URL e inicia sesión. Para la TV de la oficina no se toca nada (lee del
  PGX por LAN, sin login).
- **Costo:** ~$9/mes (tier Standard), contra el crédito de $200/mes.
- **El PGX no cambia:** sigue siendo donde viven el Excel compartido y la
  digitación de los dueños. La ruta nginx del PGX para la TV local puede
  seguir funcionando en paralelo o retirarse cuando las pantallas estén
  todas sobre Azure.
