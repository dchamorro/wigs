# TRMNL — tarjeta de compañía en los e-ink de escritorio (v1)

> v1 = **solo la tarjeta «WIG de Compañía»** (meta NAT + cobertura de backlog +
> trayectoria plurianual), igual para todos, en 1–2 dispositivos. Las tarjetas
> por persona (Mi marcador / Mi equipo / Mi incentivo) son v2 — ver el rollout
> en `docs/ARCHITECTURE.md`.

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
