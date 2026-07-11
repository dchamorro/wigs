#!/usr/bin/env python3
"""Adaptador Airtable → bundle TRMNL (v1: solo la tarjeta de compañía).

Lee la base `WIGS` (tablas Years y Backlog Readings, digitadas en el grid de
Airtable cada lunes) y arma el bundle {week, company} con la misma forma que
`scripts/trmnl_sample.json`, para que `trmnl_render.render_company` no cambie.

Solo stdlib (urllib) — sin dependencias. Auth: PAT de solo lectura en el env
`AIRTABLE_PAT` (scope data.records:read sobre la base WIGS).

La v2 (tarjetas por persona) agrega más tablas detrás de este mismo seam.
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

BASE_ID = "appZ8gj9HvUsOBuvP"
T_YEARS = "tbl9umbEdqqLpfqFe"    # Years: Año · Etiqueta · Ingreso · GP % · Meta NAT · Tiene página
T_BACKLOG = "tblHb9ImXr3hVBxUR"  # Backlog Readings: Etiqueta · Fecha · GP comprometido · Año (link)
NAT_YEAR = 2027

# Espejo de BACKLOG_START (excel/build_wig.py) — solo fallback si el grid de
# Backlog Readings no está sembrado o el lunes actual cae fuera de él.
WEEK1_MONDAY = date(2026, 6, 15)

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Managua")
except Exception:  # sin tzdata: Nicaragua es UTC-6 fijo (sin DST)
    TZ = timezone(timedelta(hours=-6))

# Fechas en español a mano (sin locale: los runners de CI no traen es_NI).
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_es(d):
    return f"{DIAS[d.weekday()]} {d.day} {MESES[d.month - 1]} {d.year}"


def fetch_table(table_id, token, base_id=BASE_ID):
    """GET paginado de api.airtable.com; devuelve la lista de records."""
    records, offset = [], None
    while True:
        params = {"pageSize": "100"}
        if offset:
            params["offset"] = offset
        url = (f"https://api.airtable.com/v0/{base_id}/{table_id}"
               f"?{urllib.parse.urlencode(params)}")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
        records.extend(payload.get("records", []))
        offset = payload.get("offset")
        if not offset:
            return records


def _monday(d):
    return d - timedelta(days=d.weekday())


def _week_num(monday, grid_dates):
    """Posición 1-based del lunes en el grid sembrado; fórmula como fallback."""
    if monday in grid_dates:
        return grid_dates.index(monday) + 1
    return max(1, (monday - WEEK1_MONDAY).days // 7 + 1)


def build_company_bundle(years_records, backlog_records, *, nat_year=NAT_YEAR, now=None):
    """Puro (sin red): records de Airtable → bundle {week, company}."""
    by_year = {r["fields"].get("Año"): r for r in years_records if r.get("fields")}
    yr = by_year.get(str(nat_year))
    if yr is None:
        raise SystemExit(f"Airtable: no hay fila {nat_year} en Years")
    f = yr["fields"]
    ingreso, gp_pct, meta_nat = f.get("Ingreso"), f.get("GP %"), f.get("Meta NAT")
    if not all((ingreso, gp_pct, meta_nat)):
        raise SystemExit(f"Airtable: Years {nat_year} sin Ingreso/GP %/Meta NAT")
    gp_meta = ingreso * gp_pct

    # Lecturas de backlog del año meta (el link Año trae record ids).
    rows = [r["fields"] for r in backlog_records
            if yr["id"] in (r.get("fields", {}).get("Año") or []) and r["fields"].get("Fecha")]
    grid_dates = sorted({date.fromisoformat(r["Fecha"]) for r in rows})
    readings = sorted((date.fromisoformat(r["Fecha"]), r["GP comprometido"])
                      for r in rows if r.get("GP comprometido") is not None)
    covered, last_read = (readings[-1][1], readings[-1][0]) if readings else (0, None)

    trajectory = sorted((r["fields"] for r in years_records
                         if r.get("fields", {}).get("Tiene página")),
                        key=lambda g: g["Año"])

    now = now or datetime.now(TZ)
    monday = _monday(now.date())
    dato = f"dato al {fecha_es(last_read)}" if last_read else "sin lecturas aún"
    return {
        "week": {
            "num": _week_num(monday, grid_dates),
            "date_label": fecha_es(monday),
            "updated_label": f"Actualizado {fecha_es(now.date())} {now:%H:%M} · vía Airtable · {dato}",
        },
        "company": {
            "subtitle": f"Generar ${meta_nat:,.0f} de utilidad neta (NAT) en {nat_year}",
            "nat_year": nat_year,
            "nat_meta_label": f"${meta_nat:,.0f}",
            "backlog": {
                "pct": round(covered / gp_meta * 100),
                "covered_label": f"${covered / 1e6:.2f}M de ${gp_meta / 1e6:.2f}M de GP meta",
                "gap_label": f"Falta vender (brecha): ${(gp_meta - covered) / 1e6:.2f}M",
            },
            "trajectory": [{"year": int(g["Año"]), "value_m": g["Meta NAT"] / 1e6,
                            "label": f"${g['Meta NAT'] / 1e6:.1f}M"} for g in trajectory],
            "notes": [
                f"Ingreso {nat_year}: ${ingreso / 1e6:.1f}M · GP meta {gp_pct * 100:.0f}%",
                "El piso de impuesto (3% s/ventas) se gana",
                "en GP% y costo local plano, no solo ventas.",
            ],
        },
    }


def from_airtable(*, token=None, base_id=BASE_ID, nat_year=NAT_YEAR, now=None):
    """Fuente en vivo: 2 GETs a Airtable → bundle de la tarjeta de compañía."""
    token = token or os.environ.get("AIRTABLE_PAT")
    if not token:
        raise SystemExit("Falta AIRTABLE_PAT (PAT de solo lectura sobre la base WIGS)")
    return build_company_bundle(fetch_table(T_YEARS, token, base_id),
                                fetch_table(T_BACKLOG, token, base_id),
                                nat_year=nat_year, now=now)
