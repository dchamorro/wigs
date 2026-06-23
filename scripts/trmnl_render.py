#!/usr/bin/env python3
"""Renderiza las tarjetas TRMNL (e-ink 800×480, 1-bit) por persona.

Convierte los mocks estáticos `web/trmnl_card_*.svg` en un render dirigido por
datos: dado un "bundle" normalizado de una persona (sus WIG como líder, sus
lead measures, compromisos, el WIG de compañía y su incentivo), emite las 4
tarjetas que el dispositivo rota:

  marcador  — Mi marcador   (lead measures + compromisos)
  company   — WIG de Compañía (NAT + cobertura + trayectoria)   [igual para todos]
  team      — Mi equipo      (lag acum. + tendencia + compromisos del equipo)
  incentive — Mi incentivo   (avance del variable, solo relativo, sin montos)

Fuente de datos (adaptadores, ver más abajo):
  - from_json(path)      — fuente de trabajo y de pruebas (fixture local).
  - from_airtable(...)   — pendiente: lee la base "WIGS" por `TRMNL ID`. Stub
                           documentado; ver docs/AIRTABLE.md.

Reglas de diseño e-ink (no romper): solo negro sobre blanco, sin grises; el
semáforo es GLIFO, no color (● en meta · ◐ riesgo/ritmo · ○ atrasado);
tipografía grande y legible.

Uso:
  python3 scripts/trmnl_render.py --input scripts/trmnl_sample.json --out dist/trmnl
  python3 scripts/trmnl_render.py --input scripts/trmnl_sample.json --kind company
  python3 scripts/trmnl_render.py --input scripts/trmnl_sample.json --out dist/trmnl --png

`--png` rasteriza con cairosvg si está instalado (lo que consume el e-ink);
sin cairosvg se emite solo SVG (y se avisa).
"""
import argparse
import json
import os
import sys
from xml.sax.saxutils import escape

W, H = 800, 480
FONT = "Helvetica, Arial, sans-serif"

# ── primitivas SVG ────────────────────────────────────────────────────────────
def _esc(s):
    return escape(str(s))

def text(x, y, s, size, *, bold=False, anchor="start", ls=None):
    attrs = [f'x="{x}"', f'y="{y}"', f'font-size="{size}"']
    if bold:
        attrs.append('font-weight="bold"')
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if ls is not None:
        attrs.append(f'letter-spacing="{ls}"')
    return f'<text {" ".join(attrs)}>{_esc(s)}</text>'

def line(x1, y1, x2, y2, sw=1):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000" stroke-width="{sw}"/>'

def bar(x, y, w, h, frac, sw=1.4):
    """Barra de progreso: contorno + relleno (frac en 0..1)."""
    frac = max(0.0, min(1.0, frac))
    fill_w = round(w * frac)
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#000" stroke-width="{sw}"/>'
    if fill_w > 0:
        out += f'<rect x="{x}" y="{y}" width="{fill_w}" height="{h}" fill="#000"/>'
    return out

def glyph(status, cx, cy, r, sw=1.6):
    """Semáforo de glifo: ● meta · ◐ riesgo/ritmo · ○ atrasado."""
    s = (status or "").lower()
    if s in ("meta", "en meta"):
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#000"/>'
    if s in ("riesgo", "ritmo", "en ritmo"):
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" stroke="#000" stroke-width="{sw}"/>'
                f'<path d="M{cx},{cy - r} A{r},{r} 0 0,0 {cx},{cy + r} Z" fill="#000"/>')
    # atrasado / desconocido
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" stroke="#000" stroke-width="{sw}"/>'

def _frame():
    return (f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>'
            f'<rect x="6" y="6" width="788" height="468" rx="6" fill="none" stroke="#000" stroke-width="3"/>')

def _header(title, subtitle, period, date, *, title_size=28):
    return "".join([
        text(24, 44, title, title_size, bold=True),
        text(24, 65, subtitle, 14),
        text(776, 36, period, 17, bold=True, anchor="end"),
        text(776, 58, date, 14, anchor="end"),
        line(16, 78, 784, 78, 2),
    ])

def _col_divider():
    return line(474, 88, 474, 446, 1)

def _footer(left, right=None, *, right_bold=False):
    out = line(16, 452, 784, 452, 1) + text(24, 468, left, 11)
    if right:
        out += text(776, 468, right, 11, bold=right_bold, anchor="end")
    return out

def _legend(items, y=464):
    """items: [(status, label, cx)] — clave del semáforo en el pie."""
    out = ['<g font-size="11">']
    for status, label, cx in items:
        out.append(glyph(status, cx, y, 6, sw=1.4))
        out.append(text(cx + 10, y + 4, label, 11))
    out.append("</g>")
    return "".join(out)

def _svg(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="{FONT}">\n'
            '  <!-- e-ink 1-bit: solo negro sobre blanco -->\n  '
            + body + "\n</svg>\n")

# ── tarjetas ──────────────────────────────────────────────────────────────────
def render_marcador(d):
    p, wk, m = d["person"], d["week"], d["marcador"]
    b = [_frame(),
         _header(p["name"], f'{p["area"]} · {p.get("org", "GBM Nicaragua")}', f'SEMANA {wk["num"]}', wk["date_label"]),
         _col_divider(),
         text(24, 104, "MIS LEAD MEASURES", 15, bold=True, ls=1.5)]
    y = 130
    for wig in m["wigs"]:
        b.append(text(24, y, f'WIG {wig["num"]} · {wig["name"]}', 16, bold=True))
        b.append(glyph(wig["status"], 452, y - 5, 8))
        ly = y + 24
        for lead in wig["leads"]:
            b.append(glyph(lead["status"], 36, ly - 4, 7))
            b.append(text(52, ly, f'{lead["slot"]} · {lead["name"]}', 13))
            b.append(text(452, ly, f'{lead["real"]} / {lead["meta"]}', 13, bold=True, anchor="end"))
            frac = (lead["real"] / lead["meta"]) if lead["meta"] else 0
            b.append(bar(52, ly + 6, 300, 7, frac, sw=1))
            ly += 36
        y = ly + 8  # siguiente WIG
    # compromisos (columna derecha)
    b.append(text(486, 104, "MIS COMPROMISOS · ESTA SEMANA", 14, bold=True, ls=0.6))
    by = 118
    for c in m["compromisos"]:
        b.append(f'<rect x="490" y="{by}" width="18" height="18" rx="2" fill="#fff" stroke="#000" stroke-width="1.6"/>')
        if c.get("done"):
            cy = by + 9
            b.append(f'<polyline points="493,{cy} 499,{cy + 6} 506,{cy - 7}" fill="none" stroke="#000" stroke-width="2.2"/>')
        lines = c["text"] if isinstance(c["text"], list) else [c["text"]]
        ty = by + 8
        for ln in lines[:2]:
            b.append(text(520, ty, ln, 13.5))
            ty += 18
        b.append(text(520, by + 43, c["tag"], 11, ls=0.5))
        by += 64
    b.append(_footer(wk["updated_label"]))
    b.append(_legend([("meta", "en meta", 556), ("riesgo", "riesgo", 636), ("atrasado", "atrasado", 710)]))
    return _svg("".join(b))

def render_company(d):
    wk, c = d["week"], d["company"]
    bk, traj = c["backlog"], c["trajectory"]
    b = [_frame(),
         _header("WIG de Compañía", c["subtitle"], f'SEMANA {wk["num"]}', wk["date_label"]),
         _col_divider(),
         text(24, 106, f'META DE UTILIDAD NETA {c["nat_year"]}', 13, bold=True, ls=1.2),
         text(24, 156, c["nat_meta_label"], 46, bold=True),
         text(24, 178, "Utilidad neta después de impuestos (NAT)", 14),
         text(24, 222, f'BACKLOG GP {c["nat_year"]} · COMPROMETIDO', 13, bold=True, ls=1.2),
         text(24, 262, f'{bk["pct"]}%', 34, bold=True),
         text(120, 262, "cubierto", 16),
         bar(24, 276, 420, 16, bk["pct"] / 100),
         text(24, 314, bk["covered_label"], 14),
         text(24, 334, bk["gap_label"], 14),
         text(486, 106, "TRAYECTORIA PLURIANUAL (NAT)", 13, bold=True, ls=1.2)]
    maxv = max(t["value_m"] for t in traj)
    scale = 184 / maxv
    ry = 138
    for t in traj:
        w = round(t["value_m"] * scale)
        b.append(text(486, ry + 12, t["year"], 15, bold=True))
        b.append(f'<rect x="556" y="{ry}" width="{w}" height="16" fill="#000"/>')
        b.append(text(556 + w + 8, ry + 13, t["label"], 14, bold=True))
        ry += 46
    ny = 300
    for note in c["notes"]:
        b.append(text(486, ny, note, 13))
        ny += 21
    b.append(_footer(wk["updated_label"], c.get("rally", "4DX · Todos remamos hacia la misma meta"), right_bold=True))
    return _svg("".join(b))

def render_team(d):
    wk, t = d["week"], d["team"]
    lag, comp = t["lag"], t["compromisos"]
    b = [_frame(),
         _header(f'Mi equipo · WIG {t["wig_num"]}', f'{t["wig_name"]} · {t["wig_teams"]}',
                 f'SEMANA {wk["num"]}', wk["date_label"]),
         _col_divider(),
         text(24, 106, lag["caption"], 13, bold=True, ls=1.2),
         text(24, 152, f'{lag["real"]} / {lag["meta"]}', 42, bold=True),
         glyph(lag["status"], 430, 140, 9, sw=1.8),
         text(24, 176, lag["note"], 14),
         bar(24, 186, 420, 14, lag["real"] / lag["meta"] if lag["meta"] else 0),
         text(24, 232, "ÚLTIMAS 8 SEMANAS (ACUM.)", 13, bold=True, ls=1.2)]
    # tendencia: 8 barras, base y=412
    trend = t["trend"]
    maxv = max(trend) or 1
    b.append('<g fill="#000">')
    x = 28
    for v in trend:
        h = round(v / maxv * 110)
        b.append(f'<rect x="{x}" y="{412 - h}" width="40" height="{h}"/>')
        x += 52
    b.append("</g>")
    b.append(line(24, 412, 444, 412, 1.4))
    b.append(text(28, 428, t["trend_start"], 11))
    b.append(text(392, 428, t["trend_end"], 11))
    # compromisos del equipo (derecha)
    b.append(text(486, 106, f'COMPROMISOS · SEMANA {wk["num"]}', 13, bold=True, ls=1.2))
    b.append(text(486, 148, f'{comp["done"]} / {comp["total"]}', 32, bold=True))
    pct = round(comp["done"] / comp["total"] * 100) if comp["total"] else 0
    b.append(text(566, 148, f'hechos ({pct}%)', 16))
    b.append(bar(486, 160, 298, 14, comp["done"] / comp["total"] if comp["total"] else 0))
    b.append(text(486, 206, "POR PERSONA", 13, bold=True, ls=1.2))
    py = 232
    for person in comp["by_person"]:
        b.append(text(486, py, person["name"], 14))
        dots = min(person["total"], 3)
        for i in range(dots):
            cx = 700 + i * 20
            b.append(glyph("meta" if i < person["done"] else "atrasado", cx, py - 5, 6, sw=1.4))
        b.append(text(770, py, f'{person["done"]}/{person["total"]}', 13, anchor="end"))
        py += 26
    b.append(text(486, 298, "APUESTA PRINCIPAL", 13, bold=True, ls=1.2))
    ay = 320
    for lead in t["apuesta"]:
        b.append(glyph(lead["status"], 492, ay, 6, sw=1.4))
        b.append(text(508, ay + 4, f'{lead["slot"]} · {lead["name"]}', 13.5))
        b.append(text(770, ay + 4, f'{lead["real"]} / {lead["meta"]}', 13.5, bold=True, anchor="end"))
        ay += 24
    b.append(_footer(wk["updated_label"], t["owner_note"]))
    return _svg("".join(b))

def render_incentive(d):
    inc = d["incentive"]
    b = [_frame(),
         _header("Mi incentivo", "Variable ligado al avance de mis WIG · sin montos",
                 inc["period"], inc["cut_label"]),
         _col_divider(),
         text(24, 106, "PROGRESO HACIA MI OBJETIVO", 13, bold=True, ls=1.2),
         text(24, 168, f'{inc["pct"]}%', 52, bold=True),
         text(170, 168, "del objetivo", 20),
         glyph(inc["status"], 32, 200, 8),
         text(50, 205, inc["status_note"], 15),
         bar(24, 222, 420, 18, inc["pct"] / 100),
         f'<text x="24" y="282" font-size="14">Proyección al ritmo actual: '
         f'<tspan font-weight="bold">{_esc(inc["projection"])}</tspan></text>',
         line(24, 306, 444, 306, 1),
         text(24, 332, "Esta pantalla no muestra montos.", 13),
         text(24, 352, "El detalle de pago vive en la app privada (con login).", 13),
         text(486, 106, "CÓMO SE COMPONE (PONDERADO)", 13, bold=True, ls=1.2)]
    cy = 140
    for comp in inc["components"]:
        b.append(text(486, cy, comp["label"], 13.5))
        b.append(text(770, cy, f'{comp["pct"]}%', 13.5, bold=True, anchor="end"))
        b.append(bar(486, cy + 8, 220, 12, comp["pct"] / 100, sw=1.2))
        b.append(text(486, cy + 36, comp["note"], 11))
        cy += 68
    b.append(line(486, 332, 784, 332, 1))
    b.append(text(486, 356, inc["weighted_note"], 14, bold=True))
    b.append(_footer("Solo progreso relativo · montos en app privada (login)"))
    b.append(_legend([("meta", "en meta", 600), ("ritmo", "en ritmo", 680), ("atrasado", "atrás", 758)]))
    return _svg("".join(b))

RENDERERS = {
    "marcador": render_marcador,
    "company": render_company,
    "team": render_team,
    "incentive": render_incentive,
}
KINDS = list(RENDERERS)

def render_all(bundle):
    return {kind: fn(bundle) for kind, fn in RENDERERS.items()}

# ── adaptadores de fuente de datos ────────────────────────────────────────────
def from_json(path):
    """Fuente de trabajo/pruebas: bundle normalizado desde un fixture local."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def from_airtable(base_id, token, trmnl_id):
    """PENDIENTE — leer la base "WIGS" y armar el bundle de una persona.

    Diseño (ver docs/AIRTABLE.md): por `TRMNL ID` ubicar al colaborador en
    `Colaboradores`; sus WIG donde es `Líder` → `WIGs`/`Leads` + últimas
    `Lead Readings`/`WIG Readings` para real vs meta y estado; sus `Compromisos`
    de la semana; `Years`/`Backlog Readings`/`NAT Monthly` para la tarjeta de
    compañía. El cálculo de acumulados/estado debe coincidir con build_wig.py.
    El contenedor remoto de Claude no alcanza api.airtable.com; correr desde una
    máquina con salida a internet.
    """
    raise NotImplementedError(
        "from_airtable() aún no implementado — ver docs/AIRTABLE.md «Pendiente». "
        "Hoy use --input con un fixture JSON (scripts/trmnl_sample.json)."
    )

# ── rasterización (opcional) ──────────────────────────────────────────────────
def to_png(svg, out_path):
    try:
        import cairosvg
    except ImportError:
        return False
    cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=out_path,
                     output_width=W, output_height=H)
    return True

# ── CLI ───────────────────────────────────────────────────────────────────────
def main(argv=None):
    ap = argparse.ArgumentParser(description="Renderiza las tarjetas TRMNL por persona.")
    ap.add_argument("--input", required=True, help="fixture JSON con el bundle de la persona")
    ap.add_argument("--kind", choices=KINDS + ["all"], default="all")
    ap.add_argument("--out", default="dist/trmnl", help="carpeta de salida")
    ap.add_argument("--png", action="store_true", help="rasterizar a PNG con cairosvg si está")
    args = ap.parse_args(argv)

    bundle = from_json(args.input)
    tid = bundle.get("person", {}).get("trmnl_id", "card")
    kinds = KINDS if args.kind == "all" else [args.kind]
    os.makedirs(args.out, exist_ok=True)

    png_warned = False
    for kind in kinds:
        svg = RENDERERS[kind](bundle)
        base = os.path.join(args.out, f"{tid}_{kind}")
        with open(base + ".svg", "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"✓ {base}.svg")
        if args.png:
            if to_png(svg, base + ".png"):
                print(f"✓ {base}.png")
            elif not png_warned:
                print("⚠ cairosvg no instalado — solo SVG. `pip install cairosvg` para PNG.", file=sys.stderr)
                png_warned = True
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
