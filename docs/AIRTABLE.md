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

Se rasteriza
con `cairosvg web/trmnl_card_demo.svg trmnl_card.png` (o `python3 -c "import
cairosvg; cairosvg.svg2png(url='web/trmnl_card_demo.svg', write_to='card.png')"`).
Reglas de diseño e-ink: solo negro sobre blanco, sin grises; el semáforo es
glifo (● en meta · ◐ riesgo · ○ atrasado), no color; tipografía grande y legible.

Datos de ejemplo sembrados en la base para el mock: colaboradora **María José
Selva** (Pre-Sales), Líder de WIG 1 y WIG 5, con 3 compromisos de la semana 22.

Pendiente para producción: el render por-persona (servido por LAN desde el PGX,
BYOS de TRMNL) que toma estos datos y emite un PNG/HTML 800×480 por `TRMNL ID`.
Cada dispositivo se configura como *private plugin* (polling) apuntando al PGX.

## Pendiente (sync)

`excel/sync_from_airtable.py` (aún por escribir): lee esta base y reconstruye el
`.xlsx` con la estructura de `build_wig.py`, emparejando filas por fecha. Hoy
`build_airtable.py` solo crea/siembra la base.
