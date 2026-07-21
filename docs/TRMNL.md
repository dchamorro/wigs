# TRMNL — tarjeta de compañía en los e-ink de escritorio (v1)

> v1 = **solo la tarjeta «WIG de Compañía»** (meta NAT + cobertura de backlog +
> trayectoria plurianual), igual para todos, en 1–2 dispositivos. Las tarjetas
> por persona (Mi marcador / Mi equipo / Mi incentivo) son v2 — ver el rollout
> en `docs/ARCHITECTURE.md`. Además de la tarjeta v1 hay una pantalla **hero**
> (webhook, sin hosting propio) — ver [la sección al final](#hero-de-compañía-vía-webhook-alternativa-sin-hosting).

## Cómo fluye el dato

```
Airtable (base WIGS: Years + Backlog Readings, digitado en el grid cada lunes)
  → GitHub Actions (cron lunes por hora + un tiro diario) renderiza el PNG
    (scripts/trmnl_render.py --source airtable, 800×480, 1-bit puro)
  → Cloudflare Pages: https://wig-trmnl.pages.dev/<SECRET>/company.png
  → TRMNL cloud (private plugin) → el dispositivo la muestra
```

- **Qué se digita**: el `GP comprometido` acumulado de la semana, en la fila de
  la semana de la tabla **Backlog Readings** (el grid 2027/2028/2029 ya está
  sembrado con `scripts/seed_backlog.py`). Nada más.
- La ruta secreta (`<SECRET>`) es el "token" v1: quien no la conoce no ve el
  PNG. En v2 la reemplaza el Worker `GET /trmnl/card?device=<ID>&token=…`.

## Configuración inicial (una vez)

### 1. Cloudflare

```
npx wrangler login
npx wrangler pages project create wig-trmnl --production-branch=main
```

Crear un **API token** (dash.cloudflare.com → My Profile → API Tokens) con el
permiso *Cloudflare Pages: Edit* sobre la cuenta, y copiar el **Account ID**.

### 2. Secrets del repo (GitHub → Settings → Secrets → Actions)

| Secret | Valor |
|---|---|
| `AIRTABLE_PAT` | PAT de **solo lectura** (`data.records:read`, solo la base WIGS) |
| `CLOUDFLARE_API_TOKEN` | token con *Cloudflare Pages: Edit* |
| `CLOUDFLARE_ACCOUNT_ID` | Account ID de Cloudflare |
| `WIG_TRMNL_SECRET_PATH` | `python3 -c "import secrets; print(secrets.token_urlsafe(24))"` |

Repo público ⇒ los logs de Actions son públicos: **todo va en secrets** (GitHub
los enmascara). Nunca subir el PNG como artifact ni imprimir la URL completa.

### 3. Dispositivo TRMNL

1. **Developer Edition**: en usetrmnl.com → Plugins buscar «Private Plugin».
   Si no aparece, comprar el add-on *Developer Edition* (pago único por cuenta;
   si el dispositivo se compró con esa opción ya está activo).
2. **Crear el private plugin**: Plugins → Private Plugin → New.
   - **Strategy: Static** (no hay datos que mergear; TRMNL descarga la imagen
     al generar cada pantalla).
   - Activar **Remove bleed margin** (imagen borde a borde).
   - Markup (reemplazar `<SECRET>`):

   ```html
   <img class="image image--contain"
        src="https://wig-trmnl.pages.dev/<SECRET>/company.png"
        style="width:100%; height:100%;" alt="WIG de Compañía">
   ```

   Sin `image-dither`: el PNG ya es blanco/negro puro (regla e-ink del
   renderer) a 800×480 = tamaño nativo del TRMNL OG, pasa sin tramado ni
   reescalado.
3. **Preview** en el editor del plugin (valida sin tocar el hardware).
4. **Playlist**: agregar el plugin a la playlist de cada dispositivo (o como
   único item = pantalla fija). Refresh del dispositivo: **60 min** basta (el
   dato cambia 1 vez por semana); *Force Refresh* para probar.

## Operación

- **Lunes**: digitar `GP comprometido` en Airtable → el cron del lunes publica
  el PNG cada hora (o correr el workflow a mano: Actions → *TRMNL — tarjeta de
  compañía* → Run workflow). El dispositivo lo toma en su próximo ciclo.
- **Render local** (para revisar la tarjeta):
  `AIRTABLE_PAT=pat… make trmnl-company` → `dist/trmnl/card_company.png`
  (requiere `pip install cairosvg pillow`; sin cairo solo emite el SVG).
- **Rotar el secreto**: cambiar `WIG_TRMNL_SECRET_PATH`, correr el workflow y
  actualizar el `src` del plugin.

## Notas y límites conocidos

- **El grid termina el 28-dic-2026.** Extenderlo a 2027 es tarea v2 (nuevas
  filas en Backlog Readings; `seed_backlog.py` sirve de plantilla). Mientras
  tanto la fórmula de respaldo sigue contando semanas y la tarjeta no se rompe.
- **Cron de repos públicos**: GitHub suspende los `schedule` tras ~60 días sin
  actividad en el repo. Si el dato semanal solo se digita en Airtable (sin
  commits), reactivarlo con el botón de Actions o hacer un commit al mes.
- **Fuentes**: el runner usa Liberation Sans (métricas tipo Arial/Helvetica),
  instalada por el workflow; revisar visualmente la tarjeta la primera vez.

---

# Hero de compañía vía webhook (alternativa sin hosting)

La pantalla **hero** del WIG de compañía: NAT real vs meta, ritmo al corte,
cobertura de backlog y el semáforo de los 12 WIGs. A diferencia de la tarjeta
v1 (PNG estático hosteado), el hero usa el **webhook** del private plugin: no
requiere Cloudflare ni hosting — TRMNL renderiza el markup Liquid en su
servidor con los merge variables que empuja el script. Su fuente es el
**tablero xlsx** (contrato del Dashboard), no Airtable.

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
