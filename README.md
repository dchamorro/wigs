# WIG Scoreboard

A static website that renders a Wildly Important Goals (WIG) scoreboard from an
Excel workbook. No backend, no build step — the browser fetches the workbook
and renders it with [SheetJS](https://sheetjs.com/).

## Where the data lives

**`data/scoreboard.xlsx`** in this repo is the source of truth. It is deployed
with the site as a static asset.

To update the scoreboard:

1. Edit `data/scoreboard.xlsx` in Excel.
2. Commit and push to `main`.
3. GitHub Actions redeploys the site automatically (~1 minute).

### Workbook format

**Sheet `Scoreboard`** — one row per WIG:

| WIG | Owner | Metric | Start | Target | Current | Due Date | (extra columns…) |
|-----|-------|--------|-------|--------|---------|----------|------------------|
| Increase monthly revenue | Danilo | Monthly revenue (USD) | 40000 | 60000 | 51000 | 2026-12-31 | |

- Progress % is computed as `(Current − Start) / (Target − Start)`, so it works
  for both "increase" goals (Start < Target) and "decrease" goals (Start > Target).
- Any extra columns (e.g. `Notes`) are shown in the card details.

**Sheet `Settings`** (optional) — key/value pairs in columns A/B:

| A | B |
|---|---|
| Title | Caoba Group — WIG Scoreboard |
| Subtitle | Wildly Important Goals — updated weekly |

### Hosting the Excel elsewhere (optional, later)

If non-technical editors need to update the scoreboard without git, host the
workbook in Azure Blob Storage (or a SharePoint direct-download link) and point
`DATA_URL` at the top of `assets/app.js` to that URL. The host must allow CORS
from the site's origin. Nothing else changes.

## One-time Azure setup

Uses [Azure Static Web Apps](https://learn.microsoft.com/azure/static-web-apps/)
(the **Free** tier covers this easily; the $200/month credit is more than enough
if you ever need the Standard tier).

1. In the [Azure Portal](https://portal.azure.com), create a **Static Web App**:
   - Plan: **Free**
   - Source: **GitHub** → select `dchamorro/wigs`, branch `main`
   - Build presets: **Custom**; app location `/`, output location *(empty)*
2. Azure connects to GitHub and adds the `AZURE_STATIC_WEB_APPS_API_TOKEN`
   secret to the repo automatically. (If it also commits its own workflow file,
   delete it and keep `.github/workflows/azure-static-web-apps.yml` from this
   repo, or just let Azure's generated one stand — they are equivalent.)
3. Push to `main` — the site deploys to the URL shown in the Static Web App
   overview (e.g. `https://<name>.azurestaticapps.net`).

Alternatively, with the Azure CLI:

```sh
az group create -n rg-wig-scoreboard -l eastus2
az staticwebapp create -n wig-scoreboard -g rg-wig-scoreboard \
  --source https://github.com/dchamorro/wigs --branch main \
  --app-location "/" --login-with-github
```

## Run locally

Browsers block `fetch` of local files over `file://`, so serve the folder:

```sh
npx serve .        # or: python3 -m http.server 8000
```

Then open http://localhost:3000 (or :8000).
