# Hero WIG en TRMNL (e-ink 800×480)

La pantalla hero del WIG de compañía en un TRMNL físico: NAT real vs meta,
ritmo al corte, cobertura de backlog y el semáforo de los 12 WIGs.

## Cómo funciona

```
tablero.xlsx (recalculado)
   └─ scripts/trmnl_hero.py ── extrae Dashboard ──> merge variables (JSON ≤2KB)
         │                                              │  --push (webhook)
         │                                              ▼
         │                        https://usetrmnl.com/api/custom_plugins/<uuid>
         │                                              │
         └──> dist/trmnl/hero.svg (revisión local)      ▼
              dist/trmnl/hero_markup.liquid   TRMNL renderiza el markup Liquid
              (se pega UNA vez en el plugin)  con esas variables → e-ink
```

El markup Liquid y el render local salen del **mismo template**
(`render_hero()` en `scripts/trmnl_render.py`): el markup es el template con
placeholders `{{ … }}`; el semáforo va por `<use href="#g-{{ s1 }}">` y las
barras llegan con el ancho ya calculado en px. No hay dos layouts que mantener.

## Setup (una sola vez)

1. En [usetrmnl.com](https://usetrmnl.com) → **Plugins → Private Plugin →
   New**. Nombre: `Marcador WIG — Hero`. **Strategy: Webhook**. Guardar.
2. Copiar la **URL del webhook** que muestra el plugin
   (`https://usetrmnl.com/api/custom_plugins/<uuid>`).
3. Generar el markup y pegarlo:
   ```bash
   make trmnl-hero            # usa dist/demo_data.xlsx (correr `make demo` antes)
   ```
   Abrir `dist/trmnl/hero_markup.liquid`, copiar TODO el contenido y pegarlo en
   el plugin → **Edit Markup** → guardar.
4. Agregar el plugin a la **playlist** del dispositivo (Devices → playlist).

## Publicar datos

```bash
export TRMNL_WEBHOOK_URL='https://usetrmnl.com/api/custom_plugins/<uuid>'
make trmnl-hero DATOS=web/tablero.xlsx PUSH=1
```

El e-ink muestra los números nuevos en su siguiente refresh (según el
refresh rate configurado en TRMNL). Sin `PUSH=1` solo genera los archivos
locales (`dist/trmnl/hero.svg` para revisar, `hero_payload.json` con lo que se
enviaría). También sirve `TRMNL_PLUGIN_UUID=<uuid>` en vez de la URL completa.

**El tablero debe estar recalculado** (`scripts/recalc.py`): openpyxl solo lee
valores cacheados. `web/tablero.xlsx` ya cumple (lo publica `make publicar`);
para otro archivo, recalcular primero.

## Publicación automática (cada lunes)

`.github/workflows/trmnl.yml` empuja el hero a TRMNL en cada push a `main` que
toque `web/tablero.xlsx` — es decir, en cada `make publicar`. Solo requiere el
secret **`TRMNL_WEBHOOK_URL`** en GitHub (Settings → Secrets and variables →
Actions). Sin el secret, el workflow lo reporta y termina sin fallar.

## Reglas de diseño (no romper)

- E-ink 1-bit: solo negro sobre blanco, sin grises.
- El semáforo es GLIFO, no color: ● en meta · ◐ riesgo · ○ atrasado.
- El payload del webhook tiene límite de **2KB** (`PAYLOAD_MAX`); el script
  falla si se excede. Los nombres de WIG van truncados (`shorten`) por eso.
- Si cambia la estructura del Dashboard (contrato en CLAUDE.md), actualizar
  `extract_hero()` en el mismo commit.
- Si cambia el layout del hero: regenerar el markup (`make trmnl-hero`) y
  volver a pegarlo en el plugin — el markup pegado en TRMNL no se actualiza
  solo.
