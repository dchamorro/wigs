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

```bash
# 1. Crea un Personal Access Token en https://airtable.com/create/tokens
#    Scopes: schema.bases:read, schema.bases:write, data.records:read, data.records:write
#    Acceso: la base "WIGS" que creaste.
export AIRTABLE_TOKEN=pat_xxx
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX   # ID de la base (lo ves en la URL o en la API)

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

## TRMNL (pantallas de escritorio) — preparado, no construido

`Colaboradores` (con `TRMNL ID`) y `Compromisos` (con `Responsable`) existen
para alimentar pantallas e-ink TRMNL por escritorio: arriba el estado de las
lead measures del equipo de la persona, abajo sus compromisos de la semana.
Pendiente: un render por-persona de 800×480 (mono) servido por LAN desde el PGX
(BYOS de TRMNL). Ver discusión en el historial; el dato ya queda modelado.

## Pendiente (sync)

`excel/sync_from_airtable.py` (aún por escribir): lee esta base y reconstruye el
`.xlsx` con la estructura de `build_wig.py`, emparejando filas por fecha. Hoy
`build_airtable.py` solo crea/siembra la base.
