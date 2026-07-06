# Arquitectura — Marcador WIG 4DX (sin Excel como fuente, sin SSO, todo web)

> Estado: **propuesta acordada** (jun 2026). Reemplaza Excel-como-fuente y el PGX
> como servidor. Sin Entra/SSO. Mantiene el Excel como **artefacto generado**.

## Decisiones tomadas (no rediscutir sin razón)

1. **Airtable es la fuente de verdad.** Excel deja de editarse a mano; se **genera**
   desde Airtable solo para visualizar/auditar.
2. **Sin PGX, todo web.** Ningún servidor en oficina; solo corren navegadores
   (la TV en kiosko) y los dispositivos TRMNL, que jalan del cloud.
3. **Sin Entra / sin SSO.** El acceso se ata al **dispositivo/red**, no a personas.
   Si algún día se quiere acceso remoto, será con login tradicional (usuario/clave),
   no SSO.
4. **TV de sala = lista blanca por IP** (la oficina tiene IP pública estable) + ruta
   secreta. Solo la red de la oficina puede mostrar el marcador.
5. **TRMNL = endpoint tokenizado por dispositivo.** Cada equipo está mapeado a un
   empleado en la base; el dispositivo jala su tarjeta sin que el empleado firme nada.
6. **Formularios = formulario propio en Cloudflare** (Worker + página), enlaces
   tokenizados por persona, sin login, sin vendor externo.
7. **Sin visualización remota** por ahora (se elimina toda la capa de auth remota).

## Diagrama de flujo

```
   Lunes 08:00 · formularios            ┌──────────────────────────────┐
   (enlace tokenizado por persona) ───▶ │  AIRTABLE  (fuente de verdad) │
        ▲  Cloudflare Worker + página   │  Empleados · WIGs · Leads ·   │
        │  escribe vía API              │  Captura semanal · Compromisos│
        │                               │  Years · NAT · Incentivos     │
   Automatización Airtable 08:00 ───────┤                               │
   (envía enlaces)                      └───────────────┬───────────────┘
                                                        │  API (pull)
                                   GitHub Actions (cron, LibreOffice headless)
                          build_wig.from_airtable → tablero.xlsx (recalc)
                          trmnl_render.from_airtable → 4 tarjetas por persona
                                                        │  deploy
                          ┌─────────────────────────────┼──────────────────────┐
                          ▼                              ▼                      ▼
                 Cloudflare Pages              Cloudflare Worker /trmnl   Excel (descarga
                 marcador.html + tablero.xlsx  (render por dispositivo)   para revisar)
                          │                              │
                   TV de sala (kiosko)            TRMNL cloud → pantallas de escritorio
                   IP allowlist + ruta secreta    (private plugin, polling, por dispositivo)
```

## Capa de datos — Airtable (base `WIGS`, `appZ8gj9HvUsOBuvP`)

Guarda **solo entradas + estructura**; lo calculado se deriva al generar el Excel.

| Tabla | Rol | Entradas (lo que se digita) |
|---|---|---|
| **Empleados** *(lista maestra)* | toda persona potencialmente responsable; mapeo de dispositivo | nombre, email, área, **TRMNL ID**, manager, activo |
| **WIGs** | los 12 WIG (estructura/metas) | dueño, meta |
| **Leads** | lead measures → enlazadas a WIG y a **Responsable (Empleado)** | nombre, meta, responsable |
| **Captura semanal** *(ancha)* | 1 fila por WIG por semana | **Lag real, L1…L8 real** |
| **Compromisos** | compromisos semanales por persona | texto, estado, responsable |
| **Years / NAT mensual** | metas anuales / seguimiento NAT | NAT real, GP comprometido |
| **Incentivos** | pesos por persona (solo relativo) | pesos por componente |

La lista **Empleados** es el punto de unión: define **quién recibe qué formulario**
y **qué muestra cada pantalla**.

## Entrada de datos — formulario propio en Cloudflare + cadencia del lunes

- **Automatización de Airtable, lunes 08:00:** por cada empleado **responsable activo**
  envía un enlace tokenizado a *su* formulario (email/WhatsApp). El token identifica a
  la persona; no hay login.
- **Formulario (Cloudflare Worker + página):** al abrir el enlace, el Worker consulta
  Airtable y arma el formulario con **exactamente los indicadores que esa persona
  posee** (sus leads como Responsable + el lag si es Dueño del WIG), incluso si
  cruzan varios WIG. Al enviar, el Worker escribe la fila de **Captura semanal** de la
  semana vía API de Airtable.
- **Pre-siembra:** la automatización crea la fila de la semana antes de enviar, para que
  el envío caiga en la semana correcta y el sync con Excel quede alineado por fecha.
- **Por qué propio:** vive en el mismo stack (Cloudflare) que el render TRMNL, sin costo
  extra ni vendor, con control exacto del enlace por persona. Editar entradas pasadas:
  el mismo Worker en modo edición o un grid en Airtable.

## Procesamiento — GitHub Actions (cron) + derivación

- **Workflow programado** (cada ~10–15 min en horario laboral, + disparo manual):
  1. `pip install` + LibreOffice headless.
  2. `build_wig.from_airtable` → estructura + datos → `recalc.py` → `tablero.xlsx`.
  3. `trmnl_render.from_airtable` → *bundle* por persona → 4 tarjetas (SVG/PNG).
  4. Deploy de `marcador.html` + `tablero.xlsx` a Cloudflare Pages; tarjetas servidas
     por el Worker `/trmnl`.
- **Excel = artefacto derivado.** Se sigue generando para visualizar/auditar, pero ya
  **no es fuente**. El contrato Excel↔`marcador.html` (posiciones fijas) se mantiene
  intacto: el TV no cambia.
- **Seam ya existente:** `scripts/trmnl_render.py` hoy solo tiene `from_json`; se agrega
  `from_airtable` detrás del mismo *bundle*. Igual para `build_wig` (`from_airtable`).
- **Secretos:** PAT de Airtable en GitHub Actions Secrets (y en el Worker para escritura).

## Hosting — Cloudflare

| Pieza | Servicio |
|---|---|
| `marcador.html` + `tablero.xlsx` | **Cloudflare Pages** (estático) |
| Endpoint render TRMNL por dispositivo | **Cloudflare Worker** `GET /trmnl/card?device=<ID>&token=…` |
| Formulario semanal por persona | **Cloudflare Worker** + página, escribe a Airtable |
| Build/sync (LibreOffice) | **GitHub Actions** (cron) — independiente del host |

Un solo vendor para el front (Cloudflare), gratis/barato, sin Azure, sin Entra.

## Control de acceso — sin login

- **TV de sala:** servida **solo a la IP pública de la oficina** (regla en Cloudflare) +
  **ruta secreta**. Fuera de la red de la oficina no carga, aunque se filtre el enlace.
  El navegador kiosko carga directo, sin prompt.
- **TRMNL:** cada dispositivo manda su token; el endpoint resuelve persona por **TRMNL
  ID** y devuelve su tarjeta. El empleado nunca firma.
- **Formularios:** enlace tokenizado por persona (vive solo en su correo).
- **Remoto:** **ninguno** por ahora. Si se revive → usuario/clave tradicional, no SSO.

## Display en sala (touch screen)

- **Chrome en kiosko** apuntando a la URL de Cloudflare; el touch-para-detalle ya existe
  en `marcador.html`.
- **Service worker** para cache offline: si Internet parpadea, la TV sigue mostrando el
  último marcador bueno (refuerza el `lastGoodLoad` ya presente).
- Refresco automático cada ~10 min; el cron regenera `tablero.xlsx` desde Airtable.

## TRMNL — pantallas de escritorio

- Cada equipo = **private plugin (polling)** apuntando al Worker `/trmnl`, identificado
  por **TRMNL ID** (en Empleados). TRMNL cloud hace la conversión e-ink y la rotación.
- Las 4 tarjetas (`web/trmnl_card_*.svg` vía `scripts/trmnl_render.py`): Mi marcador ·
  WIG de Compañía · Mi equipo (con tendencia) · Mi incentivo (solo relativo, sin montos).
- **Tendencia:** el render toma el historial de **Captura semanal** para la mini-serie.

## Rollout por fases

1. **Empleados + propiedad:** llenar la lista maestra; asignar `Leads.Responsable` /
   `WIGs.Dueño` del equipo real.
2. **Captura semanal (ancha) + formulario Cloudflare + automatización 08:00** — probar el
   ciclo con un WIG.
3. **`build_wig.from_airtable`** — Excel pasa a derivado; el TV se alimenta de Airtable.
4. **`trmnl_render.from_airtable`** — *bundles* en vivo; piloto de 2–3 escritorios.
5. **Cloudflare Pages + IP allowlist** — publicar el TV detrás de la regla de IP.

## Descartado (para el registro)

- **Entra ID / Azure AD / Azure Static Web Apps / `staticwebapp.config.json`** — el
  acceso ya no depende de un IdP corporativo. (`docs/AZURE_LOGIN.md` queda como histórico.)
- **PGX como servidor** (Samba/nginx/timer) — sin servidor en oficina.
- **Capa de auth para acceso remoto** — eliminada; futura, con login tradicional.

## Pendientes (TBD)

- Detalle del esquema `Captura semanal` (anchos L1–L8 por WIG) y migración desde las
  tablas normalizadas de *Readings*.
- Tabla `Incentivos` (pesos por persona; **sin montos**).
- Implementar `from_airtable` en `build_wig.py` y `scripts/trmnl_render.py`.
