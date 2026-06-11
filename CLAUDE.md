# Marcador WIG 4DX — GBM Nicaragua

Sistema de scoreboards 4DX (4 Disciplinas de Ejecución). WIG de compañía:
$1M de utilidad neta después de impuestos (NAT) en 2027, soportado por 9 WIGs
con lead measures semanales/mensuales.

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
  y `REFRESH_MIN`.
- `deploy/setup-wig.sh` — instala Samba + nginx + timer de publicación en el PGX.
- `.github/workflows/azure-static-web-apps.yml` — publica marcador.html a
  Azure Static Web Apps en cada push a main, en modo arrastrar-y-soltar
  (DATA_URL vacío): `tablero.xlsx` NO se publica hasta que el sitio tenga
  login (ver "Pendiente" en README). No commitear tablero.xlsx (gitignored).
- `tests/test_contract.py` — valida el contrato Excel↔parser (ver abajo).

## EL CONTRATO Excel ↔ parser (no romper)

`parseWorkbook()` en `web/marcador.html` lee **posiciones fijas**. Cualquier
cambio estructural en `build_wig.py` debe reflejarse en el parser y en
`tests/test_contract.py`, en el mismo commit.

Pestañas: `Dashboard` (primera), pestañas de WIG, `Instrucciones` (ignorada).

Por pestaña de WIG:
| Celda/Col | Contenido |
|---|---|
| A1 | Título (el parser quita el prefijo `WIG n — `) |
| B2 / B3 | Definición lag / "de X a Y" |
| B4 / E4 | Dueño / Equipo |
| B5 | Meta (el FORMATO de número de B5 decide cómo se muestran los valores: $, %, o número) |
| E10 | Si tiene texto ⇒ WIG acumulativo; vacío ⇒ WIG de nivel |
| Fila 8, cols I,K,M,…,W | Nombres de leads (pares combinados; `(Disponible)` = slot inactivo) |
| Fila 9, misma col | Meta del lead |
| Filas 11+ | B fecha · C meta · D real (input) · E/F acumulados · G % · H estado · I+2k real lead · J+2k % lead |

Dashboard: C4 meta anual NAT · filas 7–18: A mes, B meta, C real (input),
D/E acumulados, F %, G estado.

Reglas duras:
- DATA0 = fila 11. MAX_LEADS = 8. No cambiar sin tocar parser + tests + migrate.
- WIGs "menos es mejor": el parser los detecta por `/expired/i` en nombre/título.
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
