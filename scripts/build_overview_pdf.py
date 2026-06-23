#!/usr/bin/env python3
"""Genera un PDF de una sola pieza que explica el proyecto, su stack y los
próximos pasos. Contenido curado a mano (prosa editorial sintetizada de
CLAUDE.md / docs/), no extraído de los .md, para mantener el control del texto
y que el script no dependa de pandoc/Chrome/LibreOffice — solo reportlab.

Uso:
    python3 scripts/build_overview_pdf.py [salida.pdf]
    make pdf
"""
import sys
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/Marcador_WIG_4DX_Overview.pdf"

# ---- paleta ----
ACCENT = colors.HexColor("#1F3864")   # azul corporativo (mismo que el workbook)
ACCENT2 = colors.HexColor("#2E5AAC")
LIGHT = colors.HexColor("#EAF0FA")
GREY = colors.HexColor("#666666")
RULE = colors.HexColor("#C9D4E8")

# ---- estilos ----
ss = getSampleStyleSheet()
S = {
    "cover_title": ParagraphStyle(
        "cover_title", parent=ss["Title"], fontName="Helvetica-Bold",
        fontSize=30, leading=34, textColor=ACCENT, spaceAfter=10),
    "cover_sub": ParagraphStyle(
        "cover_sub", parent=ss["Normal"], fontSize=14, leading=19,
        textColor=GREY, alignment=TA_CENTER, spaceAfter=4),
    "cover_tag": ParagraphStyle(
        "cover_tag", parent=ss["Normal"], fontSize=10.5, leading=14,
        textColor=ACCENT2, alignment=TA_CENTER),
    "h1": ParagraphStyle(
        "h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=17,
        leading=20, textColor=ACCENT, spaceBefore=16, spaceAfter=4),
    "h2": ParagraphStyle(
        "h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12.5,
        leading=15, textColor=ACCENT2, spaceBefore=10, spaceAfter=3),
    "body": ParagraphStyle(
        "body", parent=ss["Normal"], fontSize=10.5, leading=15, spaceAfter=6),
    "li": ParagraphStyle(
        "li", parent=ss["Normal"], fontSize=10.5, leading=14.5, spaceAfter=2),
    "cap": ParagraphStyle(
        "cap", parent=ss["Normal"], fontSize=8.5, leading=11, textColor=GREY),
    "mono": ParagraphStyle(
        "mono", parent=ss["Normal"], fontName="Courier", fontSize=9.5,
        leading=14, spaceAfter=2),
    "cell": ParagraphStyle(
        "cell", parent=ss["Normal"], fontSize=9, leading=12),
    "cellb": ParagraphStyle(
        "cellb", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=9,
        leading=12, textColor=ACCENT),
    "cellw": ParagraphStyle(
        "cellw", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=9,
        leading=12, textColor=colors.white),
}

story = []


def P(text, style="body"):
    story.append(Paragraph(text, S[style]))


def gap(h=6):
    story.append(Spacer(1, h))


def rule():
    story.append(HRFlowable(width="100%", thickness=0.8, color=RULE,
                            spaceBefore=4, spaceAfter=8))


def bullets(items, style="li"):
    story.append(ListFlowable(
        [ListItem(Paragraph(t, S[style]), leftIndent=10, value="•") for t in items],
        bulletType="bullet", bulletColor=ACCENT2, leftIndent=14, bulletFontSize=8))


def table(rows, header, col_widths, header_style="cellw"):
    data = [[Paragraph(c, S[header_style]) for c in header]]
    for r in rows:
        data.append([Paragraph(c, S["cell"]) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ]
    t.setStyle(TableStyle(style))
    story.append(t)


# ====================================================================
# COVER
# ====================================================================
gap(150)
P("Marcador WIG 4DX", "cover_title")
P("A 4DX execution scoreboard for GBM Nicaragua", "cover_sub")
gap(6)
story.append(HRFlowable(width="40%", thickness=1.2, color=ACCENT2,
                        spaceBefore=6, spaceAfter=14, hAlign="CENTER"))
P("Company WIG: $1M net profit after taxes (NAT) in 2027 → $2M in 2028 → "
  "$2.4M in 2029, supported by 12 WIGs with weekly &amp; monthly lead measures.",
  "cover_tag")
gap(60)
P(f"Project overview · {date.today():%B %Y}", "cap")
P("Maintainer: Plans &amp; Controls (Danilo Chamorro) · "
  "Owners: 12 functional leads", "cap")
story.append(PageBreak())

# ====================================================================
# 1. WHAT THIS PROJECT IS
# ====================================================================
P("What this project is", "h1")
rule()
P("This is the scoreboard system behind GBM Nicaragua's <b>4DX</b> "
  "(4 Disciplines of Execution) program. The whole organization is steering "
  "toward one Wildly Important Goal — the <b>company WIG</b>: reach <b>$1M of "
  "net profit after taxes (NAT) in 2027</b>, then $2M in 2028 and ~$2.4M in "
  "2029 (base year 2026).")
P("That single number is too far away to manage week to week, so it is broken "
  "down into <b>12 supporting WIGs</b>. Each WIG has one <i>lag</i> measure "
  "(the result you want) and several <i>lead</i> measures (the weekly or "
  "monthly behaviors the team can actually influence). Owners report on their "
  "lead measures in the Monday cadence; the lag only moves if the leads do.")
gap(2)
P("The product tension it solves", "h2")
P("There is a real conflict between two things the program needs at once: "
  "owners must be able to update their numbers with <b>zero friction</b> (so "
  "the data is current), and leadership needs a <b>glanceable scoreboard</b> "
  "readable from across a room in five seconds (so the cadence has teeth). A "
  "spreadsheet is great for the first and poor for the second; a BI tool is "
  "the reverse and adds adoption cost. This project keeps <b>Excel as the "
  "input surface</b> and renders a <b>self-contained TV scoreboard</b> on top "
  "of it — owners keep typing in cells they already understand, and the room "
  "sees a clean, rotating board.")

# ====================================================================
# 2. HOW IT WORKS
# ====================================================================
P("How it works", "h1")
rule()
P("Structure lives in code; data lives in cells. A Python script generates "
  "the workbook's fixed structure, owners fill the blue input cells, and a "
  "single HTML file parses the workbook by fixed cell positions and turns it "
  "into rotating slides.")
gap(2)
flow = [
    ["1 · Excel", "Owners type weekly/monthly results into blue input cells "
        "(shared copy on the PGX server)."],
    ["2 · build_wig.py", "Generates the workbook <i>structure</i> — the 12 WIG "
        "tabs, Dashboard, year pages, Tareas. Single source of truth."],
    ["3 · recalc", "LibreOffice headless computes the formulas and caches the "
        "values (mandatory — the reader only sees cached values)."],
    ["4 · marcador.html", "Parses the .xlsx by fixed positions (SheetJS, "
        "embedded) and builds the slides; offline-first, no backend."],
    ["5 · Display", "Office TV reads it over the LAN in kiosk Chrome; a "
        "login-gated Azure copy serves remote viewers."],
]
table([[a, b] for a, b in flow], ["Stage", "What happens"],
      [1.5 * inch, 5.0 * inch])
gap(4)
P("Slide order on the TV: Company dashboard → 2027 → 2028 → 2029 → the 12 "
  "WIGs. Touching a lead opens its detail (history + supporting tasks).", "cap")

# ====================================================================
# 3. THE 12 SUPPORTING WIGs
# ====================================================================
story.append(PageBreak())
P("The 12 supporting WIGs", "h1")
rule()
P("Each rolls up to the company NAT goal. Targets in parentheses; “X/Y” means "
  "the threshold is still being defined by the owner.")
gap(2)
wigs = [
    ("1", "Grow the Smart User fleet", "+500 devices placed by Dec 2026"),
    ("2", "Advisory Monthly Value", "$X of advisory MV by Q1 2027"),
    ("3", "Large deals (>$30K GP)", "10 deals recognized in 2027"),
    ("4", "On-time delivery", "100% on-time placements/deliveries"),
    ("5", "Datacenter (San Marcos) MV", "+$20,000 incremental MV in 2027"),
    ("6", "Zero expired contracts", "0 expired, 16 of next 18 months"),
    ("7", "Digital Solutions MV", "+$30K/month by May 2027"),
    ("8", "Consolidated gross profit", "16% GP sustained in 2027"),
    ("9", "Customer satisfaction (CSAT)", "X→Y, sustained 4 months"),
    ("10", "Operating leverage", "Local cost flat as revenue grows (≤9%)"),
    ("11", "Recover Digital Solutions margin", "Negative lines → GP ≥ $0"),
    ("12", "Billable engineer utilization", "42% → 48%+ sustained"),
]
table(wigs, ["#", "WIG (lag measure)", "Target"],
      [0.35 * inch, 3.5 * inch, 2.65 * inch])

# ====================================================================
# 4. THE STACK
# ====================================================================
P("The stack", "h1")
rule()
stack = [
    ("Data / structure", "Python 3 + <font name=Courier>openpyxl</font> "
        "(<font name=Courier>build_wig.py</font> generates the workbook; "
        "<font name=Courier>migrate_data.py</font> moves owner data forward), "
        "LibreOffice headless for formula recalculation."),
    ("Display", "<font name=Courier>web/marcador.html</font> — one "
        "self-contained file with SheetJS embedded. Vanilla JS, no framework, "
        "offline-first. Light/dark theme, rotating slides, touch drill-down to "
        "each lead's history and supporting tasks."),
    ("Distribution — LAN", "PGX server (Lenovo, DGX OS): Samba shares the "
        "workbook, a systemd timer validates &amp; publishes it, nginx serves "
        "the board. Office TV runs kiosk Chrome — no login on the LAN."),
    ("Distribution — remote", "Azure Static Web Apps (Standard tier) with "
        "Entra ID single-tenant login — only <font name=Courier>@caobagroup.com"
        "</font> accounts. The authenticated copy for remote viewers."),
    ("CI / publish", "GitHub Actions (<font name=Courier>azure-static-web-"
        "apps.yml</font>) deploys <font name=Courier>web/</font> on push to "
        "main; <font name=Courier>make publicar</font> validates the contract "
        "+ recalc before publishing."),
    ("Tests", "Contract tests (<font name=Courier>tests/test_contract.py</font>) "
        "enforce that the Excel layout and the HTML parser stay in sync."),
    ("Explorations (not live)", "Airtable “Option A” as a future input layer; "
        "TRMNL e-ink desktop cards rendered per person "
        "(<font name=Courier>trmnl_render.py</font>)."),
]
table(stack, ["Layer", "Technology"], [1.5 * inch, 5.0 * inch])

# ====================================================================
# 5. NEXT STEPS
# ====================================================================
story.append(PageBreak())
P("Next steps", "h1")
rule()
P("Operational rollout (near-term)", "h2")
P("Getting the board live and the cadence running:")
bullets([
    "<b>Provision the PGX server</b> — run <font name=Courier>deploy/setup-"
    "wig.sh</font> (Samba + nginx + publish timer), copy "
    "<font name=Courier>marcador.html</font> and the workbook, map the share "
    "on owner machines, and set the office TV to kiosk Chrome.",
    "<b>Configure remote login</b> — finish the Azure Entra ID setup per "
    "<font name=Courier>docs/AZURE_LOGIN.md</font> (register the app, set the "
    "tenant ID and secret) so the remote copy is gated to company accounts.",
    "<b>Establish the Monday ritual</b> — owners enter their numbers in the "
    "shared workbook; the coordinator runs <font name=Courier>make publicar "
    "DATOS=…</font> to validate and publish. Lock in this weekly cadence.",
])
gap(4)
P("Roadmap (deferred — revisit as the cadence matures)", "h2")
bullets([
    "<b>SharePoint co-editing</b> — replace save-and-close Samba sharing if "
    "simultaneous edits become a pain point.",
    "<b>Move the data source off Excel</b> — Airtable “Option A” is prototyped "
    "(<font name=Courier>build_airtable.py</font>); the "
    "<font name=Courier>sync_from_airtable.py</font> adapter is not yet written.",
    "<b>History &amp; trends</b> — keep period-over-period data to show "
    "trajectories, not just the current week.",
    "<b>Alerting</b> — notify owners when a WIG slips into Riesgo/Atrasado.",
    "<b>TRMNL e-ink cards</b> — always-on personal desktop scoreboards "
    "(mockups and renderer exist; not connected to live data).",
    "<b>Multi-country rollout</b> — generalize beyond Nicaragua.",
])

# ====================================================================
# APPENDIX
# ====================================================================
story.append(PageBreak())
P("Technical appendix", "h1")
rule()
P("For maintainers. Full detail lives in <font name=Courier>CLAUDE.md</font>, "
  "<font name=Courier>docs/PRD.md</font> and <font name=Courier>docs/DESIGN.md"
  "</font>.")

P("The Excel ↔ parser contract", "h2")
P("<font name=Courier>parseWorkbook()</font> in "
  "<font name=Courier>marcador.html</font> reads <b>fixed cell positions</b> — "
  "there are no headers or named ranges to rely on. The hard rules:")
bullets([
    "Data starts at <b>row 11</b> (DATA0); each WIG has at most <b>8 leads</b> "
    "(MAX_LEADS).",
    "Status semaphore (exact Spanish text): <b>En meta</b> ≥95% · <b>Riesgo</b> "
    "80–95% · <b>Atrasado</b> &lt;80%.",
    "<b>Three-files-in-one-commit rule:</b> any structural change must touch "
    "<font name=Courier>build_wig.py</font>, the parser in "
    "<font name=Courier>marcador.html</font>, and "
    "<font name=Courier>tests/test_contract.py</font> together — never hand-"
    "edit the .xlsx for structure.",
])

P("Key commands", "h2")
cmds = [
    ("make build", "Generate the workbook structure + recalc."),
    ("make demo", "Workbook with dummy data + a standalone demo board."),
    ("make test", "Run the contract tests."),
    ("make migrate OLD=…", "Carry owner data forward into a rebuilt workbook."),
    ("make publicar DATOS=…", "Validate (contract + recalc) and publish to Azure."),
    ("make pdf", "Regenerate this overview PDF."),
]
table([[Paragraph(c, S["mono"]).text, d] for c, d in cmds],
      ["Command", "What it does"], [2.2 * inch, 4.3 * inch])

P("Repository layout", "h2")
layout = [
    ("excel/", "Workbook generator, data migrator, demo filler, Airtable seeder."),
    ("scripts/", "recalc (mandatory), demo embedder, TRMNL card renderer."),
    ("web/", "marcador.html (the TV board), published workbook, Azure config."),
    ("deploy/", "PGX provisioning script (Samba + nginx + timer)."),
    ("docs/", "PRD, DESIGN, Airtable notes, Azure login &amp; rollout runbooks."),
    ("tests/", "Contract tests (Excel↔parser) + TRMNL render checks."),
    ("dist/", "Build artifacts (gitignored) — including this PDF."),
]
table(layout, ["Path", "Contents"], [1.2 * inch, 5.3 * inch])

# ====================================================================
# build
# ====================================================================
doc = SimpleDocTemplate(
    OUT, pagesize=LETTER,
    leftMargin=0.85 * inch, rightMargin=0.85 * inch,
    topMargin=0.8 * inch, bottomMargin=0.7 * inch,
    title="Marcador WIG 4DX — Project Overview",
    author="GBM Nicaragua · Plans & Controls",
)
doc.build(story)
print(f"PDF escrito en {OUT}")
