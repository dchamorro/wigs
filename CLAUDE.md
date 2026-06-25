# Marcador WIG 4DX — GBM Nicaragua

Sistema de scoreboards 4DX (4 Disciplinas de Ejecución). WIG de compañía:
$1M de utilidad neta después de impuestos (NAT) en 2027 ($2M en 2028),
soportado por 12 WIGs con lead measures semanales/mensuales.

## Arquitectura

```
excel/build_wig.py  ──genera──>  dist/Tablero_WIG_4DX_GBM.xlsx   (estructura)
                                        │ (los dueños digitan datos en la copia
                                        │  compartida en \\PGX\WIG cada lunes)
deploy: PGX (Lenovo, DGX OS) ── samba comparte el .xlsx ── timer lo valida y
        publica a nginx ── web/marcador.html lo descarga (DATA_URL) cada 10 min
        ── TV en kiosko Chrome muestra los slides rotando
```

- `excel/build_wig.py` — **fuente de verdad de la estructura** del workbook.
- `excel/migrate_data.py` — copia los datos digitados de un tablero viejo a uno nuevo.
- `excel/fill_demo_data.py` — datos dummy para demos.
- `scripts/recalc.py` — recalcula fórmulas con LibreOffice headless. **OBLIGATORIO**
  después de build/migrate/fill: openpyxl no calcula valores y SheetJS solo lee
  valores cacheados; sin recalc el TV se ve vacío.
- `scripts/build_demo.py` — incrusta un xlsx en el HTML (demo standalone).
- `web/marcador.html` — el marcador del TV. Autocontenido (SheetJS embebido,
  funciona offline). CONFIG al inicio del script: `DATA_URL` (vacío = drag-drop)
  y `REFRESH_MIN`. Tema claro/oscuro (botón ◐ o tecla T, persiste en
  localStorage). Tocar/clicar un lead abre su detalle (historia del indicador
  + compromisos, si el tablero trae la pestaña Compromisos opcional); apto para
  pantallas táctiles.
- `deploy/setup-wig.sh` — instala Samba + nginx + timer de publicación en el PGX.
- `.github/workflows/azure-static-web-apps.yml` — publica marcador.html +
  `web/tablero.xlsx` a Azure Static Web Apps en cada push a main que toque
  `web/`. Parcha `DATA_URL: 'tablero.xlsx'` al deployar (misma convención
  que el PGX; el fuente queda con DATA_URL vacío). El sitio exige **login de
  empresa** (Entra ID de un solo tenant; solo cuentas @caobagroup.com) vía
  `web/staticwebapp.config.json` (tier Standard). La TV de la oficina NO usa
  este sitio: lee del PGX por LAN sin login; Azure es la copia para acceso
  remoto autenticado. Setup en el portal (una vez): `docs/AZURE_LOGIN.md`.
  Los datos se suben con `make publicar DATOS=...` (valida contrato + recalc).
- `tests/test_contract.py` — valida el contrato Excel↔parser (ver abajo).

## EL CONTRATO Excel ↔ parser (no romper)

`parseWorkbook()` en `web/marcador.html` lee **posiciones fijas**. Cualquier
cambio estructural en `build_wig.py` debe reflejarse en el parser y en
`tests/test_contract.py`, en el mismo commit.

Pestañas: `Dashboard` (primera), 12 pestañas de WIG (`1. …` … `12. …`), 3
páginas por año (`2027`/`2028`/`2029`), `Tareas` e `Instrucciones` (ignoradas
como slides). Las páginas por año (nombre de 4 dígitos, o el legado `Backlog
<año>`) **no** son slides de WIG, pero el TV **sí** genera un slide propio por
año (meta NAT + cobertura de backlog), leyendo B4/E4/B5/E5/B6/E6/B7/E7 y la
tabla semanal (A/B/C desde fila 12). El orden de slides es: Compañía → 2027 →
2028 → 2029 → los 12 WIGs. `Compromisos` ya **no se genera** pero el parser
conserva soporte **opcional** para tableros viejos que la traigan. `Tareas` sí
se genera y el parser la lee (no es slide; alimenta el detalle de cada lead).

Por pestaña de WIG:
| Celda/Col | Contenido |
|---|---|
| A1 | Título (el parser quita el prefijo `WIG n — `) |
| B2 / B3 | Definición lag / "de X a Y" |
| B4 / E4 | Dueño / Equipo |
| B5 | Meta (el FORMATO de número de B5 decide cómo se muestran los valores: $, %, o número) |
| B6 / B7 | **Captura del lag**: responsable que digita (B6) / fuente o método (B7) (input). El **equipo** del lag es E4. El parser y el Dashboard los leen. |
| E10 | Si tiene texto ⇒ WIG acumulativo; vacío ⇒ WIG de nivel |
| Fila 5 / 6 / 7, cols I,K,…,W | **Captura por lead** (mismas columnas que el lead): fila 5 **equipo**, fila 6 **responsable** (quién digita), fila 7 **fuente/método** (input). Rótulos en col H (`Equipo →`/`Responsable →`/`Fuente →`). El `Fin` del periodo se movió a F5/G5 para liberar H5. |
| Fila 8, cols I,K,M,…,W | Nombres de leads (pares combinados; `(Disponible)` = slot inactivo) |
| Fila 9, misma col | Meta del lead |
| Filas 11+ | B fecha · C meta · D real (input) · E/F acumulados · G % · H estado · I+2k real lead · J+2k % lead |
| Hitos (bloque bajo los datos) | **Metas binarias con fecha objetivo**. Rótulo `Hitos…` en col A en `último_dato + 2`; encabezados en la fila siguiente; `HITO_ROWS` (6) filas de entrada. Cols: **A–D Hito** (combinadas) · **E Lead** (1–8, opcional) · **F Responsable** · **G Fecha objetivo** · **H Estado** (`Pendiente`/`En curso`/`Logrado`). El parser lo localiza por el rótulo (no por fila fija, porque `último_dato` varía por WIG). |

Dashboard (cuatro bloques + tabla de soporte). Es la **página principal**: arriba
las metas de utilidad neta (NAT) de los 3 años con enlace a cada pestaña de año.
- Metas de Utilidad Neta (NAT) 2027→2029 (base 2026): encabezados fila 5, datos
  filas 6–9 (A año · B ingreso · C GP% · D **Meta NAT** · E NAT% · F NAT real
  input · G estado · H enlace a la pestaña del año). **El parser del TV lee estas
  4 filas** (año + Meta NAT col D + NAT real col F).
- Cobertura de backlog: encabezados fila 13, datos filas 14–16 (un año por fila)
  (A año · B GP meta · C GP comprometido · D brecha · E % cobertura) — fórmulas
  que referencian las páginas por año. **El parser del TV lee 14–16.**
- Seguimiento mensual NAT del año en curso: **C19 meta anual NAT** · encabezados
  fila 21 · filas 22–33: A mes, B meta, C real (input), D/E acumulados, F %,
  G estado. **El parser del TV lee este bloque (C19 + filas 22–33).**
- WIGs de soporte: encabezados fila 36, una fila por WIG (37–48). Cols A–I:
  # · WIG · Dueño · Equipo · Meta · Último real · Estado · **Captura del lag** (H,
  `=WIG!E4 · WIG!B6 — WIG!B7`) · Ir a pestaña.
- Hitos por WIG: encabezados en `48+3+1`, una fila por WIG. Por WIG: # · WIG ·
  Logrado · En curso · Pendiente (`COUNTIF` sobre el rango de Estado del bloque
  Hitos de la pestaña) · Próxima fecha (`MIN` de las fechas objetivo). Las
  fórmulas referencian el rango de Hitos de cada WIG, que `build_wig.py` conoce
  en tiempo de construcción (`hitos_ranges`).

Páginas por año `2027`/`2028`/`2029` (encabezan con la meta de utilidad neta):
| Celda/Col | Contenido |
|---|---|
| A1 | Título `<año> — Meta de Utilidad Neta (NAT)` |
| B4 / E4 | Ingreso meta / GP meta % (E4 editable si es supuesto, p. ej. 2029) |
| B5 | **GP meta = Ingreso × GP%** (`=B4*E4`) — lo que la cobertura referencia |
| E5 / E7 | **Meta NAT** (utilidad neta del año) / Margen NAT (NAT/Ingreso) |
| B6 / E6 / B7 | GP comprometido (último) / % cobertura / brecha |
| Filas 12+ | A semana · B GP comprometido acum. (input) · C GP meta · D brecha · E % |
El Dashboard las lee por posición fija (B5/B6/B7/E6); migrate copia la col B por fecha.

Compromisos (legado/opcional; el build ya no la genera). Si existe: encabezados
fijos en fila 1, datos desde fila 2: `Semana | WIG | Lead | Compromiso |
Responsable | Estado` — WIG = número de pestaña, Lead = 1–8, Estado =
`Pendiente`/`Hecho`. El parser la lee por posición A–F y es opcional. En el
detalle del TV se muestra **solo si trae filas** (debajo de «Tareas de soporte»).

Tareas (tareas de soporte por lead; el build **sí** la genera). Encabezados
fijos en fila 1, datos desde fila 2: `WIG | Lead | Tarea | Responsable | Estado`
(cols A–E) — WIG = número de pestaña (1–12), Lead = 1–8, Estado =
`Pendiente`/`En curso`/`Hecho` (con desplegables de validación). El parser
(`parseTareas`) la lee por posición A–E y la agrupa por (WIG, Lead); el TV la
muestra como «Tareas de soporte» en el detalle de cada lead (toque/clic). El
build incluye filas semilla de ejemplo (WIG 1); `migrate` copia las filas reales
(A2:E) y descarta la semilla. Es robusta a su ausencia (tableros viejos).
Las **metas binarias con fecha** (p. ej. "Certificarse como Apple Authorized
Service Provider") **no** van en Tareas: viven en el bloque **Hitos** de cada
pestaña de WIG (ver arriba).

Reglas duras:
- DATA0 = fila 11. MAX_LEADS = 8. HITO_ROWS = 6. No cambiar sin tocar parser +
  tests + migrate.
- Captura del dato (3 campos): **equipo** (lag = E4; por lead = fila 5),
  **responsable** (lag = B6; por lead = fila 6), **fuente/método** (lag = B7; por
  lead = fila 7). Hitos: estados `Pendiente`/`En curso`/`Logrado` (texto exacto,
  el conditional formatting y el rollup del Dashboard hacen SEARCH/COUNTIF).
- La columna "Captura del lag" del Dashboard usa `&` (no `TEXTJOIN`: LibreOffice
  headless no lo recalcula → `#NAME?`): `=E4 & " · " & B6 & " — " & B7`.
- WIGs "menos es mejor": el parser los detecta por nombre/título con el regex
  `LOWER_BETTER` (`/expired|apalanca|costos? local/i`). Al agregar un WIG de
  nivel donde menos = mejor (status Excel `D<=C`), ampliar ese regex.
- Los leads se definen en positivo (más = mejor) para que el % sea comparable.
- L1–L2 son la "apuesta principal" (resaltados en el TV); L3–L8 son de apoyo.
- Estados: En meta ≥95% · Riesgo 80–95% · Atrasado <80% (texto exacto, el
  conditional formatting y el dashboard hacen SEARCH sobre esas palabras).

## Flujo de trabajo para cambios al Excel (sin romper nada)

Cambios de **datos o ajustes menores** (nombres de leads, metas, dueños):
los hacen los dueños directamente en la copia compartida — son celdas de
entrada, no requieren código.

Cambios **estructurales** (agregar/quitar WIGs, leads, columnas, fórmulas):
1. Editar `excel/build_wig.py` (nunca editar el .xlsx a mano para estructura).
2. `make build` → genera dist/ y recalcula.
3. `make test` → contrato verde. Si el cambio era de posiciones, actualizar
   `parseWorkbook` en marcador.html y el test en el mismo commit.
4. `make migrate OLD=/ruta/al/tablero_con_datos.xlsx` → produce
   `dist/Tablero_migrado.xlsx` con los datos de los dueños ya copiados
   (empareja filas por fecha, así cambiar el rango de periodos no desalinea).
5. Revisar la migración, publicar el archivo migrado en `\\PGX\WIG`
   reemplazando el anterior (avisar a los dueños que cierren el archivo).

## Comandos

```
make build      # construye dist/Tablero_WIG_4DX_GBM.xlsx + recalc
make demo       # tablero con datos dummy + dist/demo.html para ver el marcador
make test       # pruebas de contrato
make migrate OLD=ruta.xlsx   # migra datos al tablero recién construido
make deploy PGX=usuario@ip   # copia marcador.html al PGX vía scp
```

## Decisiones tomadas (no rediscutir sin razón)

- Excel como fuente de datos (no Airtable/Sheets) hasta que la cadencia madure.
- Edición compartida vía Samba en el PGX; sin co-edición simultánea (guardar y
  cerrar). Si estorba: un coordinador digita todo, o migrar a SharePoint.
- marcador.html autocontenido y offline-first; fetch same-origin (`tablero.xlsx`).
- Visualizaciones de leads deterministas por posición: L1 gauge, L2 sparkline,
  resto cicla barras/bullet/número grande. Mismo semáforo de color en todas.
- El ritual del lunes (subir Excel a Claude y pedir el marcador de la reunión)
  vive en claude.ai, no en este repo.
