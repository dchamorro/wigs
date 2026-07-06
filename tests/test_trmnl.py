"""
test_trmnl.py — Valida el render de las tarjetas TRMNL (scripts/trmnl_render.py).

Renderiza el fixture de ejemplo (scripts/trmnl_sample.json) y verifica que las
4 tarjetas salgan bien formadas (XML válido), con los valores y glifos del
bundle, y que la aritmética de barras coincida con los mocks de web/trmnl_card_*.svg.

Uso:  python3 -m pytest tests/ -q        (o)        python3 tests/test_trmnl.py
No requiere cairosvg (solo SVG/string).
"""
import os
import sys
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.trmnl_render as t

SAMPLE = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'trmnl_sample.json')


def bundle():
    return t.from_json(SAMPLE)


def test_render_all_kinds():
    cards = t.render_all(bundle())
    assert set(cards) == {'marcador', 'company', 'team', 'incentive'}, 'faltan tarjetas'


def test_well_formed_xml():
    for kind, svg in t.render_all(bundle()).items():
        xml.dom.minidom.parseString(svg)  # lanza si está mal formado
        assert svg.startswith('<svg') and svg.rstrip().endswith('</svg>'), f'{kind}: no es un SVG'
        assert 'width="800" height="480"' in svg, f'{kind}: tamaño e-ink no es 800×480'


def test_marcador_values_and_glyphs():
    svg = t.render_marcador(bundle())
    for needle in ('María José Selva', 'WIG 1 · Smart User 500', 'L1 · Cartas de asignación firmadas',
                   '14 / 20', '2 / 2', 'MIS COMPROMISOS · ESTA SEMANA', 'WIG 1 · L4 · HECHO'):
        assert needle in svg, f'marcador: falta «{needle}»'
    assert '<polyline' in svg, 'marcador: el compromiso «HECHO» debe llevar checkmark'


def test_bar_arithmetic_matches_mock():
    # lead 14/20 sobre barra de 300px → relleno 210px (= 0.7×300), como en el mock.
    assert 'width="210" height="7" fill="#000"' in t.render_marcador(bundle())
    # backlog 38% sobre 420px → 160px, como en trmnl_card_company.svg.
    assert 'width="160" height="16" fill="#000"' in t.render_company(bundle())
    # incentivo hero 64% sobre 420px → 269px.
    assert 'width="269" height="18" fill="#000"' in t.render_incentive(bundle())


def test_trajectory_scaled_to_max():
    # 2029 = valor máx → 184px; 2027 ($1.0M) → 75px (escala 184/2.445).
    svg = t.render_company(bundle())
    assert 'width="184" height="16" fill="#000"' in svg, 'company: la barra máx debe medir 184px'
    assert 'width="75" height="16" fill="#000"' in svg, 'company: $1.0M debe escalar a 75px'


def test_glyph_semaphore_is_glyph_not_color():
    # e-ink: el estado se codifica como glifo (relleno/medio/vacío), nunca con color.
    meta = t.glyph('meta', 10, 10, 7)
    riesgo = t.glyph('riesgo', 10, 10, 7)
    atrasado = t.glyph('atrasado', 10, 10, 7)
    assert 'fill="#000"' in meta and '<path' not in meta, 'meta = círculo lleno'
    assert '<path' in riesgo, 'riesgo = medio círculo (path)'
    assert 'fill="#fff"' in atrasado and '<path' not in atrasado, 'atrasado = círculo vacío'
    for svg in t.render_all(bundle()).values():
        assert 'fill="#ccc"' not in svg and 'fill="gray"' not in svg, 'e-ink: sin grises'


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for fn in fns:
        fn()
        print(f'OK  {fn.__name__}')
    print(f'\n{len(fns)} pruebas de render TRMNL pasaron.')
