# PRD — Marcador WIG 4DX (GBM Nicaragua)

> **Status:** As-built (documents the system that exists today) + a short roadmap.
> **Owner:** Plans & Controls (Danilo Chamorro).
> **Audience:** software maintainers, GBM leadership, and anyone onboarding to run or
> extend the system. Technical contract and architecture live in
> [`CLAUDE.md`](../CLAUDE.md); this PRD covers the *product* — the problem, the users,
> the experience, and what "done well" means. When the two disagree about a fixed cell
> or sheet position, `CLAUDE.md` and `tests/test_contract.py` win.
> **Language note:** the codebase, the workbook, and the TV scoreboard are in Spanish
> (the users' language). This document is in English by request; product/UI strings
> quoted below stay in their original Spanish.

---

## 1. Background & context

GBM Nicaragua runs its execution against **4DX** (The 4 Disciplines of Execution):
focus on a Wildly Important Goal (WIG), act on **lead measures** (predictive, the team
can influence them), keep a **compelling scoreboard** the team can read at a glance, and
hold a **weekly cadence of accountability**.

The company WIG for this cycle is a multi-year net-profit trajectory:

> **Build Nicaragua's net profit after taxes (NAT): $1M in 2027, $2M (7% margin)
> in 2028, $2.4M (8%) in 2029** (base year 2026).

That trajectory is too lagging to act on weekly, so it is supported by **12 WIGs**,
each owned by a function, each with its own lag measure and up to 8 lead measures (see
§4), and tracked year-by-year on three **year pages** (2027/2028/2029) plus a company
Dashboard. Discipline 3 ("keep a compelling scoreboard") is where software comes in: without a
scoreboard that is *current, public, and effortless to read*, the cadence decays into a
status meeting and the WIG drifts.

This product is that scoreboard, plus the lightweight pipeline that keeps it current.

## 2. Problem statement

A 4DX scoreboard only works if **three things are simultaneously true**, and they fight
each other:

1. **It is trivial for the owners to update.** Twelve functional owners enter their numbers
   every Monday. If updating means logging into a new tool, learning a UI, or asking IT
   for access, it won't happen — the scoreboard goes stale and the cadence dies.
2. **It is compelling on the wall.** The team must read "are we winning?" in 5 seconds,
   from across the room, on a TV — not by squinting at a spreadsheet grid.
3. **It is trustworthy and low-maintenance.** No broken formulas, no blank screens, no
   single point of failure that needs an engineer every Monday.

The tension: the tool owners *trust and already use* (Excel) is not compelling on a TV;
the tools that look good on a TV (dashboards, BI) impose adoption cost on the owners and
ongoing cost on whoever runs them.

## 3. Goals & non-goals

### Product goals

- **G1 — Zero-friction data entry.** Owners update the WIG by typing into a shared Excel
  file they already know. No new tool, no login, no training beyond "type in the blue
  cells."
- **G2 — Glanceable scoreboard.** A TV in the office cycles through slides; anyone can
  tell in seconds, per WIG, whether the team is *En meta / Riesgo / Atrasado* (on
  target / at risk / behind).
- **G3 — Effortless, safe publishing.** Getting fresh numbers onto the screens is one
  command (`make publicar`) that refuses to publish a broken or unrecalculated workbook.
- **G4 — Resilient & low-maintenance.** The scoreboard works offline, survives a flaky
  network, and has no moving parts that demand weekly engineering attention.
- **G5 — Supports the Monday cadence.** The scoreboard is built to be read aloud in the
  weekly accountability meeting, including per-lead drill-down and team commitments
  (*compromisos*).

### Business goal (the WIG this product serves)

- The NAT trajectory ($1M 2027 → $2M 2028 → $2.4M 2029), decomposed into the 12 WIGs in §4
  and tracked on the year pages and Dashboard. The product does not *produce* these numbers
  — it makes the team's progress toward them visible and actionable every week.

### Non-goals

- **Not a system of record / BI platform.** Excel is the source of data on purpose, until
  the cadence matures (see §9 and `CLAUDE.md` "Decisiones tomadas"). Airtable is being
  *explored* as "Option A" (a capture layer with Excel still the calc engine — see
  [`docs/AIRTABLE.md`](./AIRTABLE.md)), but it is not the live source today; no Sheets/Power BI.
- **Not simultaneous multi-user editing.** Owners save-and-close the shared file; there is
  no live co-editing. If this becomes painful, the fallback is a single coordinator who
  types everyone's numbers, or a move to SharePoint.
- **Not public.** The scoreboard contains internal targets and performance. It is
  restricted to the office (LAN via PGX, no login) and to authenticated company accounts
  on Azure (single-tenant Entra ID, `@caobagroup.com` only). It is not a marketing or
  external-stakeholder artifact.
- **Not the meeting itself.** The Monday ritual of uploading the Excel to Claude and
  generating the meeting's talking points lives in claude.ai, not in this repo.
- **No historical data warehouse, alerting, or predictive analytics** in the current
  scope (candidates for the roadmap, §9).

## 4. The 12 supporting WIGs (product content)

These are defined as the single source of truth in
[`excel/build_wig.py`](../excel/build_wig.py) (`WIGS` list) and rendered as one tab each.
"From → to" and any `$X / X→Y` placeholders are filled by the owners in the Meta cell.

| # | WIG (lag measure) | Target | Owning team | Cadence |
|---|---|---|---|---|
| 1 | Grow the Smart User fleet by **500 devices** in 2026 (cumulative; 500 × $40/mo ≈ $6.4K extra MRR) | 500 devices | Pre-Sales, Del-DEX | Weekly, to 2026-12-28 |
| 2 | Reach a **Monthly Value of $X in advisory** by Q1 2027 (local-engineer advisory hours sold; fixed cost already covered) | $X (set in cell) | Sales, CS, Pre-Sales, Del-TSS | Weekly, to 2027-03-29 |
| 3 | Book **10 deals > $30K GP** in 2027 (large deals that move NAT) | 10 deals | Sales, Pre-Sales | Weekly, to 2027-12-27 |
| 4 | Deliver **100% of deliveries & placements on time and in full** | 100% sustained | Finanzas | Weekly, to 2027-12-27 |
| 5 | Grow **Datacenter (San Marcos) services MV by $20,000** | +$20,000 | Pre-Sales, Del-DC | Weekly, to 2027-12-27 |
| 6 | **Zero expired contracts** in at least 16 of the next 18 months | 0 (sustained) | CS, Del-DEX/TSS/DC | Weekly, to 2027-12-27 |
| 7 | Grow **Digital Solutions MV by $30K/mo** by 2027-05-01 (SOC + dev cells) | +$30,000/mo | Sales, Del-DS | Weekly, to 2027-04-26 |
| 8 | Achieve **16% consolidated GP** in 2027 | 16% sustained | Finanzas (all areas) | Monthly |
| 9 | Raise **CSAT from X to Y**, sustained 4 consecutive months | X→Y (set in cell) | CS (all delivery areas) | Monthly |
| 10 | **Keep local costs flat while revenue grows** (operating leverage): local indirect + OREX as % of revenue should *fall* | ≤9% sustained (from ~13%) | Finanzas, CS, all local areas | Monthly |
| 11 | **Recover Digital Solutions margin** and eliminate GP-negative lines | GP ≥ $0 then positive (from ~–$78K/mo) | Sales, Pre-Sales, Del-DS, Finanzas | Monthly |
| 12 | Raise **billable utilization of local engineers from 42% to 48%+** | ≥48% sustained | Del-TSS, Del-DC, CS, Pre-Sales | Monthly |

Beyond the 12 WIG tabs, the workbook carries three **year pages** (`2027`/`2028`/`2029`),
each headed by that year's NAT target with its revenue/GP path and backlog coverage, and a
company **Dashboard** that rolls the trajectory up (see FR4). The TV renders a slide per
year (Company → 2027 → 2028 → 2029 → the 12 WIGs).

Two "direction" conventions matter for the scoreboard math:

- **Cumulative vs. level WIGs.** Cumulative WIGs (1, 2, 3, 5, 7) accumulate toward a total;
  level WIGs (4, 6, 8, 9, 10, 11, 12) must hold at/under/over a threshold each period.
- **"Less is better" WIGs.** WIGs where less = better (6 expired contracts → 0; 10 local
  cost ratio falling) invert the scoring; the parser detects them via the `LOWER_BETTER`
  regex (`/expired|apalanca|costos? local/i`). Their lead measures are still phrased
  *positively* (more = better) so the percentage stays comparable across all WIGs.

Each WIG carries up to **8 lead measures** (defined in `build_wig.py`). **L1–L2 are the
team's "main bet"** (visually emphasized on the TV); **L3–L8 are supporting indicators**.
Empty slots show as `(Disponible)`.

## 5. Users & personas

| Persona | Who | What they need | Frequency |
|---|---|---|---|
| **WIG owner** | A functional lead per WIG (Sales, Pre-Sales, CS, Finance, Delivery) | Type their weekly/monthly numbers into the blue input cells of *their* tab; no other tooling. | Weekly (Mon) / Monthly |
| **Cadence coordinator** | Plans & Controls (1 person) | Run the Monday ritual: collect the saved workbook, validate, and publish to the screens with one command. | Weekly |
| **The team / leadership** | Everyone who walks past the office TV | Read "are we winning?" at a glance; drill into a specific lead and its commitments during the Monday meeting. | Continuous (TV) + weekly (meeting) |
| **Maintainer** | Software (this repo) | Change structure safely (the Excel↔parser contract), build, test, migrate data, deploy. | Ad hoc |

## 6. User journeys

### J1 — Owner updates their numbers (weekly)
1. Owner opens the shared workbook on `\\PGX\WIG` (Samba) — the same `.xlsx` they always use.
2. On their WIG tab, types the week's **Real** value (column D) into the blue input cells;
   optionally updates lead-measure actuals and adds/updates rows in the **Tareas** sheet
   (supporting tasks per lead, with a Pendiente/En curso/Hecho status).
3. Saves and closes (no co-editing). Formulas recalc when the file is next recalculated.

### J2 — Coordinator publishes (weekly, Monday)
1. `make publicar DATOS=/path/to/workbook_with_data.xlsx`.
2. The pipeline **validates the contract** (`tests/test_contract.py`) and **checks recalc**
   (a workbook with no cached calculated values is rejected — it would show blank on the TV).
3. On success it copies to `web/tablero.xlsx`, commits, and pushes. Azure redeploys in ~1 min
   (IP-restricted to the office). On the LAN path, the PGX timer validates and publishes to
   nginx; `web/marcador.html` polls `DATA_URL` every ~10 min.

### J3 — Team reads the scoreboard (continuous)
1. The office TV runs `marcador.html` in kiosk Chrome, cycling slides: company NAT dashboard,
   then one slide per year (2027/2028/2029), then one slide per WIG with its lag gauge, lead
   visualizations, and color status.
2. After inactivity it auto-resumes the rotation; users can swipe/navigate on a touch screen.
3. Tapping/clicking a lead opens its **detail**: the indicator's history + that lead's
   **supporting tasks** (from the Tareas sheet), and legacy commitments if an old workbook
   still carries a Compromisos sheet. Light/dark theme via the ◐ button or `T` (persisted).

### J4 — Maintainer makes a structural change (ad hoc)
1. Edit `excel/build_wig.py` (never hand-edit the `.xlsx` for structure) → `make build`.
2. `make test`; if cell positions changed, update `parseWorkbook()` in `marcador.html` **and**
   `tests/test_contract.py` **in the same commit**.
3. `make migrate OLD=…` to carry owners' typed data into the new structure (rows matched by
   date), review, then replace the file on `\\PGX\WIG`.

## 7. Functional requirements

- **FR1 — Structure generated from code.** The workbook is produced by `build_wig.py`; the
  structure is never hand-edited. Data (lead names, targets, owners, weekly actuals) are
  owner-editable input cells and need no code change.
- **FR2 — Fixed Excel↔parser contract.** `parseWorkbook()` reads fixed cell/column positions
  (see `CLAUDE.md` "EL CONTRATO"). `DATA0 = row 11`, `MAX_LEADS = 8`. Any structural change
  touches `build_wig.py` + `parseWorkbook` + `test_contract.py` together.
- **FR3 — Status semaphore.** Per WIG/lead: **En meta ≥95% · Riesgo 80–95% · Atrasado <80%**
  (exact Spanish strings — conditional formatting and the dashboard `SEARCH` on them). The TV
  uses one consistent color semaphore everywhere.
- **FR4 — Company dashboard.** The first sheet is the home page: NAT targets 2027→2029
  (rows 6–9, with a link to each year page), backlog coverage by year (rows 14–16),
  current-year monthly NAT tracking (annual goal C19 + months in rows 22–33), and a roll-up
  of all 12 WIGs' latest status (rows 37–48). The TV's parser reads the NAT-by-year,
  backlog-coverage, and monthly-NAT blocks.
- **FR5 — Lead visualizations, deterministic by position.** L1 = gauge, L2 = sparkline; the
  rest cycle bar / bullet / big-number. Same color semaphore as the lag.
- **FR6 — Supporting-task drill-down.** A build-generated **Tareas** sheet (`WIG | Lead |
  Tarea | Responsable | Estado`, `Estado ∈ {Pendiente, En curso, Hecho}`) feeds each lead's
  detail view as "Tareas de soporte". The parser (`parseTareas`) reads it by position and
  groups by (WIG, Lead). A legacy **Compromisos** sheet (`Semana | WIG | Lead | Compromiso |
  Responsable | Estado`) is still read if present, but the build no longer generates it. Both
  are robust to absence (must not break the parser — contract-tested).
- **FR7 — Self-contained, offline-first scoreboard.** `marcador.html` embeds SheetJS and works
  with no network; data fetched same-origin from `tablero.xlsx`. Drag-and-drop when `DATA_URL`
  is empty (the source keeps `DATA_URL` empty; deploy patches it).
- **FR8 — Safe publish.** Publishing validates the contract and recalc state and refuses a
  broken/uncalculated workbook. `recalc.py` (LibreOffice headless) is mandatory after any
  build/migrate/fill, because openpyxl doesn't compute values and SheetJS reads only cached ones.
- **FR9 — Data migration.** `migrate_data.py` copies owners' typed data from an old workbook
  into a freshly built one, matching rows by date so period-range changes don't misalign.

## 8. Non-functional requirements

- **NFR1 — Adoption cost ≈ 0 for owners.** No new tool or login; editing is in the Excel they
  already use. This is the load-bearing constraint behind "Excel as source of data."
- **NFR2 — Resilience.** Offline-first; same-origin fetch; a network blip does not blank the TV.
  No component requires weekly engineering intervention.
- **NFR3 — Security / confidentiality.** Internal targets and performance. LAN-only via PGX
  (no login — the building is the trust boundary); on Azure, **company login** gates access
  (single-tenant Entra ID, `@caobagroup.com` only) via `web/staticwebapp.config.json`
  (Standard tier). First-time portal setup: [`docs/AZURE_LOGIN.md`](./AZURE_LOGIN.md).
- **NFR4 — Readability.** Legible across a room on a TV; light/dark theme; touch-friendly.
- **NFR5 — Maintainability.** Single source of structural truth (`build_wig.py`); the contract
  is enforced by tests so structural drift fails CI rather than the TV.
- **NFR6 — Cost.** Minimal: one Azure Standard plan, or a repurposed Lenovo (PGX) on the LAN.

## 9. Roadmap / future considerations

Explicitly **out of current scope**, kept here so the trade-offs aren't re-litigated:

- **SharePoint / co-editing.** If save-and-close on Samba becomes a bottleneck, move the shared
  workbook to SharePoint for real co-editing, or designate a single coordinator who types all
  numbers. Decision deferred "until the cadence matures."
- **Move off Excel as source of data.** Airtable/Sheets/a small DB become attractive once the
  weekly cadence is reliable and the team wants history/automation. Excel is a deliberate
  *starting* point, not the end state. **Airtable is already prototyped as "Option A"**
  ([`excel/build_airtable.py`](../excel/build_airtable.py), [`docs/AIRTABLE.md`](./AIRTABLE.md)):
  Airtable as the capture layer while Excel stays the calculation engine and the Excel↔TV
  contract is untouched. It also enables per-person **TRMNL** e-ink desktop cards (Mi
  marcador / Compañía / Mi equipo / Mi incentivo — `web/trmnl_card_*.svg`). This is
  exploratory, not the live data source today; `sync_from_airtable.py` is not yet written.
- **History & trends.** Persisting weekly snapshots for trend lines beyond the current period.
- **Alerting.** Push a Slack/email nudge when a WIG flips to *Atrasado* or when an owner hasn't
  updated by Monday.
- **More WIGs / org rollout.** The structure supports adding WIG tabs via `build_wig.py`; other
  GBM countries/functions could reuse the same scoreboard.

## 10. Success metrics (for this product)

The business metric is the $1M NAT. Success of *the scoreboard itself* is measured by whether
it sustains Discipline 3 (compelling scoreboard) and the Monday cadence:

- **M1 — Data freshness.** % of the 12 WIGs with current-week/month data entered by each Monday
  meeting. *Target: 12/12 (100%) by meeting time, sustained.*
- **M2 — Owner self-service.** Share of weeks where owners update without a manual reminder
  from the coordinator. *Target: trending to 100%; reminders → exception, not routine.*
- **M3 — Publish reliability.** % of Mondays the scoreboard publishes without a broken/blank
  TV (no failed `make publicar`, no stale screen). *Target: 100%.*
- **M4 — Visibility.** The office TV is on and rotating during business hours. *Target: always.*
- **M5 — Cadence usage.** The scoreboard (incl. lead drill-down + commitments) is actually used
  to run the weekly accountability meeting. *Target: every weekly meeting.*
- **M6 — Maintenance load.** Engineering touches required to keep it running, week over week.
  *Target: ≈ 0 outside intentional structural changes.*

> M1–M3 are directly observable from the repo/pipeline (entered cells, push history, CI status);
> M4–M5 are observed in the office. No analytics are collected on the TV (it's offline-first).

## 11. Risks & mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Owners stop entering data | Scoreboard goes stale, cadence dies | Zero-friction Excel entry (NFR1); M1/M2 watched; fallback = single coordinator types all |
| Save-and-close friction (no co-edit) | Edit conflicts, lost updates | Documented protocol (close before publish); SharePoint as escape hatch (§9) |
| Forgotten recalc → blank TV | Loss of trust in the screen | `make publicar` rejects un-recalculated workbooks (FR8); recalc is mandatory & automated |
| Structural change breaks the contract | TV misreads cells | Contract tests fail CI before deploy (FR2/NFR5); parser+test+build changed in one commit |
| Public exposure of internal targets | Confidentiality breach | LAN-only on PGX (no login); company login on Azure (single-tenant Entra ID) (NFR3) |
| Single shared file corrupts/locks | Whole scoreboard down | Generated from code (rebuild any time) + `migrate_data.py` to recover owners' data |

## 12. References

- [`CLAUDE.md`](../CLAUDE.md) — architecture, the Excel↔parser contract, and change workflow (authoritative on structure).
- [`README.md`](../README.md) — quick start, production, and the Monday Azure ritual.
- [`docs/PUESTA-EN-MARCHA-AZURE.md`](./PUESTA-EN-MARCHA-AZURE.md) — Azure first-time setup runbook.
- [`excel/build_wig.py`](../excel/build_wig.py) — single source of truth for workbook structure and the 12 WIGs.
- [`docs/DESIGN.md`](./DESIGN.md) — system design: architecture, components, data flow, decisions.
- [`docs/AIRTABLE.md`](./AIRTABLE.md) — Airtable "Option A" exploration + TRMNL desktop cards.
- [`tests/test_contract.py`](../tests/test_contract.py) — enforces the contract.
