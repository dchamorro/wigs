# Airtable como sistema de registro (Opción A)

Mueve la **captura de datos** de Excel a Airtable, sin tocar el contrato
Excel↔TV. Airtable guarda **solo entradas + estructura**; el cálculo
(acumulados, %, estado, cobertura de backlog) sigue en el Excel: un sync
posterior lee la base y reconstruye `Tablero_WIG_4DX_GBM.xlsx` → `recalc` → TV.

```
Airtable (dueños digitan)  ──sync──>  build_wig.py-shaped .xlsx  ──recalc──>  marcador.html (TV)
```

Por qué así: el TV lee posiciones fijas de celda y Excel es el **motor de
cálculo** (ver CLAUDE.md). Reimplementar ese cálculo en Airtable es frágil
(acumulados entre filas, referencias entre tablas). Mantener Excel como motor
deja el contrato y el offline-first intactos.

## Crear / actualizar la base

`excel/build_airtable.py` crea el esquema y siembra los datos vía API REST de
Airtable (no usa el conector MCP, así que no hay prompt de aprobación). Es
idempotente: re-correrlo no duplica (salta tablas/registros por nombre).

La base ya existe y está sembrada: **WIGS** = `appZ8gj9HvUsOBuvP` (creada vía MCP
el 2026-06-23). El script de abajo es la versión reproducible/idempotente por
REST: re-correrlo no duplica, así que sirve para re-sembrar o migrar a otra base.

```bash
# 1. Crea un Personal Access Token en https://airtable.com/create/tokens
#    Scopes: schema.bases:read, schema.bases:write, data.records:read, data.records:write
#    Acceso: la base "WIGS" que creaste.
export AIRTABLE_TOKEN=pat_xxx
export AIRTABLE_BASE_ID=appZ8gj9HvUsOBuvP   # base "WIGS"

make airtable-dry      # imprime el plan, no escribe (offline)
make airtable          # crea las 9 tablas + siembra
```

Egress: la red debe permitir `api.airtable.com` (el contenedor remoto de Claude
no lo tiene en allowlist; correr desde una máquina con salida a internet).

## Esquema (9 tablas)

Solo se siembran **estructura + metas**; las tablas de *Readings* y *Compromisos*
nacen vacías (las llenan los dueños cada lunes).

| Tabla | Qué guarda | Origen |
|---|---|---|
| **WIGs** | los 12 WIG: número, título, lag, de-X-a-Y, dueño, equipo, meta, formato, tipo (`acum`/`nivel_min`/`nivel_max`), frecuencia, umbral de riesgo | semilla desde `build_wig.py` |
| **Leads** | hasta 8 por WIG: nombre, slot, meta, formato, *apuesta principal* (L1/L2), responsable | semilla |
| **WIG Readings** | lag real por periodo (WIG, fecha, **real**) | dueños |
| **Lead Readings** | real de cada lead por periodo (lead, fecha, **real**) | dueños |
| **Years** | trayectoria NAT 2026→2029: ingreso, GP%, meta NAT, **NAT real**, banderas (año base / tiene página / GP% supuesto) | semilla |
| **Backlog Readings** | GP comprometido acum. por semana (año, fecha, **GP comprometido**) | dueños |
| **NAT Monthly** | seguimiento mensual NAT del año en curso (mes, fecha, **NAT real**) | rejilla 2027 sembrada |
| **Colaboradores** | personas: nombre, email, área, **TRMNL ID**, activo | manual |
| **Compromisos** | compromisos semanales: texto, semana, WIG, lead, responsable, estado | dueños |

**En negrita** = celdas de entrada (lo que se digita). Todo lo demás es
estructura o se calcula en el Excel tras el sync.

## TRMNL (pantallas de escritorio)

`Colaboradores` (con `TRMNL ID`) y `Compromisos` (con `Responsable`) alimentan
pantallas e-ink TRMNL por escritorio: arriba el estado de las lead measures de
los WIG donde la persona es **Líder**, abajo sus **compromisos** de la semana.

El dispositivo **rota** entre varias pantallas (mocks 800×480, 1-bit):
1. `web/trmnl_card_demo.svg` — **Mi marcador**: mis lead measures + mis compromisos.
2. `web/trmnl_card_company.svg` — **WIG de Compañía**: meta NAT $1M + cobertura de backlog + trayectoria 2027-2029 (igual para todos; alineación 4DX).
3. `web/trmnl_card_team.svg` — **Mi equipo**: lag acumulado del WIG, tendencia 8 semanas y tablero de compromisos del equipo (rendición de cuentas).
4. `web/trmnl_card_incentive.svg` — **Mi incentivo**: progreso del variable hacia
   el objetivo, **solo en relativo (sin montos)**, descompuesto por driver
   (lead measures / compromisos / WIG de compañía). Decisión de privacidad: nunca
   montos en la pantalla siempre-encendida; el detalle de pago va en una app
   privada con login. En producción, una tabla `Incentivos` (por persona:
   período, pesos, % por componente) alimentaría esta pantalla — sin cifras de pago.

Reglas de diseño e-ink: solo negro sobre blanco, sin grises; el semáforo es
glifo (● en meta · ◐ riesgo · ○ atrasado), no color; tipografía grande y legible.

### Render dirigido por datos

`scripts/trmnl_render.py` convierte esos mocks estáticos en un render por-persona:
dado un *bundle* normalizado (la persona, sus WIG como líder con sus lead measures,
compromisos, el WIG de compañía y su incentivo) emite las **4 tarjetas** SVG
800×480 (y PNG con `--png` si hay `cairosvg`). La aritmética de barras y los glifos
se generan desde los datos; el layout reproduce los mocks.

```bash
make trmnl                              # usa el fixture de ejemplo (María José)
make trmnl INPUT=mi_bundle.json PNG=1   # otra persona, con PNG (necesita cairosvg)
```

El fixture `scripts/trmnl_sample.json` reproduce el mock (colaboradora **María
José Selva**, Pre-Sales, Líder de WIG 1 y WIG 5, 3 compromisos de la semana 22) y
sirve de contrato visual; `tests/test_trmnl.py` lo valida (parte de `make test`).

**Fuente de datos (adaptadores en `trmnl_render.py`):**
- `from_json(path)` — fuente de trabajo y de pruebas (el fixture de arriba).
- `from_airtable(base_id, token, trmnl_id)` — **pendiente** (stub documentado):
  ubicar la persona por `TRMNL ID` en `Colaboradores`, leer sus WIG donde es
  `Líder` + últimas *Readings* + sus `Compromisos` de la semana + `Years`/backlog
  para la tarjeta de compañía, con el mismo cálculo de estado que `build_wig.py`.

Pendiente para producción: implementar `from_airtable` y el servidor por LAN desde
el PGX (BYOS de TRMNL) que sirva un PNG/HTML por `TRMNL ID`; cada dispositivo se
configura como *private plugin* (polling) apuntando al PGX.

## Pendiente (sync)

`excel/sync_from_airtable.py` (aún por escribir): lee esta base y reconstruye el
`.xlsx` con la estructura de `build_wig.py`, emparejando filas por fecha. Hoy
`build_airtable.py` solo crea/siembra la base.
