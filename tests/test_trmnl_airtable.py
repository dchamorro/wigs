"""
test_trmnl_airtable.py — Valida el mapeo Airtable → bundle de la tarjeta de
compañía (scripts/trmnl_airtable.py), sin red: usa el fixture enlatado
tests/fixtures/airtable_company.json (misma forma que api.airtable.com).

Uso:  python3 -m pytest tests/ -q        (o)        python3 tests/test_trmnl_airtable.py
"""
import json
import os
import sys
import xml.dom.minidom
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.trmnl_airtable as ta
import scripts.trmnl_render as t

FIXTURE = os.path.join(os.path.dirname(__file__), 'fixtures', 'airtable_company.json')
# Miércoles de la semana 2 del grid (lunes 22-jun-2026).
NOW = datetime(2026, 6, 24, 9, 30)


def records():
    with open(FIXTURE, encoding='utf-8') as f:
        fx = json.load(f)
    return fx['Years'], fx['Backlog Readings']


def bundle(backlog=None, now=NOW):
    years, readings = records()
    return ta.build_company_bundle(years, readings if backlog is None else backlog, now=now)


def test_bundle_feeds_render_company():
    svg = t.render_company(bundle())
    xml.dom.minidom.parseString(svg)  # lanza si está mal formado
    assert 'width="800" height="480"' in svg, 'tamaño e-ink no es 800×480'
    for needle in ('SEMANA 2', '$1,000,000', '38%', 'TRAYECTORIA PLURIANUAL'):
        assert needle in svg, f'company: falta «{needle}»'


def test_backlog_math():
    b = bundle()['company']['backlog']
    # GP meta = 21,000,000 × 16% = $3.36M; última lectura $1.28M (la fila sin
    # GP comprometido no cuenta, la de 2028 tampoco) → 38%.
    assert b['pct'] == 38, b
    assert b['covered_label'] == '$1.28M de $3.36M de GP meta', b
    assert b['gap_label'] == 'Falta vender (brecha): $2.08M', b


def test_week_from_grid():
    wk = bundle()['week']
    assert wk['num'] == 2 and wk['date_label'] == 'lun 22 jun 2026', wk
    assert wk['updated_label'].endswith('vía Airtable · dato al lun 22 jun 2026'), wk


def test_week_fallback_past_grid():
    # Lunes 4-ene-2027: fuera del grid sembrado (termina dic-2026) → fórmula
    # desde WEEK1_MONDAY (15-jun-2026): 203 días // 7 + 1 = semana 30.
    wk = bundle(now=datetime(2027, 1, 6, 8, 0))['week']
    assert wk['num'] == 30 and wk['date_label'] == 'lun 4 ene 2027', wk


def test_trajectory_only_years_with_page():
    traj = bundle()['company']['trajectory']
    assert [g['year'] for g in traj] == [2027, 2028, 2029], traj  # sin 2026 (base)
    assert [g['label'] for g in traj] == ['$1.0M', '$2.0M', '$2.4M'], traj


def test_empty_readings_renders():
    # Estado del día de lanzamiento: grid sin lecturas todavía.
    b = bundle(backlog=[])
    assert b['company']['backlog']['pct'] == 0
    assert 'sin lecturas aún' in b['week']['updated_label']
    xml.dom.minidom.parseString(t.render_company(b))


def test_fecha_es():
    assert ta.fecha_es(date(2026, 6, 22)) == 'lun 22 jun 2026'
    assert ta.fecha_es(date(2026, 1, 3)) == 'sáb 3 ene 2026'


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for fn in fns:
        fn()
        print(f'OK  {fn.__name__}')
    print(f'\n{len(fns)} pruebas del adaptador Airtable pasaron.')
