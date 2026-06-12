"""
test_contract.py — Valida el CONTRATO entre el Excel y el parser del marcador.

El marcador (web/marcador.html) lee posiciones FIJAS del workbook. Si este
test falla después de un cambio en excel/build_wig.py, el televisor se
rompería: hay que ajustar también el parser en marcador.html (función
parseWorkbook) y mantener ambos lados sincronizados.

Uso:  python3 -m pytest tests/ -q        (o)        python3 tests/test_contract.py
Requiere un tablero construido y recalculado en dist/Tablero_WIG_4DX_GBM.xlsx
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openpyxl import load_workbook

WB_PATH = os.environ.get('WIG_XLSX', 'dist/Tablero_WIG_4DX_GBM.xlsx')
HTML_PATH = os.environ.get('WIG_HTML', 'web/marcador.html')
DATA0 = 11
MAX_LEADS = 8


def wb():
    assert os.path.exists(WB_PATH), f'Construir primero: make build (falta {WB_PATH})'
    return load_workbook(WB_PATH, data_only=False)


def test_tabs_exist():
    names = wb().sheetnames
    assert names[0] == 'Dashboard'
    assert 'Instrucciones' in names
    wig_tabs = [n for n in names if n not in ('Dashboard', 'Instrucciones')]
    assert len(wig_tabs) >= 1, 'Debe existir al menos una pestaña de WIG'


def test_wig_tab_layout():
    book = wb()
    for name in book.sheetnames:
        if name in ('Dashboard', 'Instrucciones'):
            continue
        ws = book[name]
        # encabezado que el parser lee
        assert ws['A1'].value, f'{name}: falta título en A1'
        assert ws['B2'].value, f'{name}: falta lag en B2'
        assert ws['B4'].value is not None, f'{name}: falta dueño en B4'
        assert ws['B5'].value is not None, f'{name}: falta meta en B5'
        # detección acum/nivel: E10 con o sin texto
        e10 = ws['E10'].value
        acum = e10 is not None and str(e10).strip() != ''
        # primera fila de datos: fecha en B11 y fórmulas correctas
        assert ws.cell(row=DATA0, column=2).value is not None, f'{name}: falta fecha en B{DATA0}'
        estado = ws.cell(row=DATA0, column=8).value
        assert isinstance(estado, str) and estado.startswith('='), f'{name}: H{DATA0} debe ser fórmula de Estado'
        if acum:
            for c, frag in ((5, 'SUM'), (6, 'SUM'), (7, '/')):
                v = ws.cell(row=DATA0, column=c).value
                assert isinstance(v, str) and v.startswith('=') and frag in v, \
                    f'{name}: col {c} fila {DATA0} no tiene la fórmula esperada'
        # bloque de leads: nombre fila 8, meta fila 9, % en columna par
        found = 0
        for k in range(MAX_LEADS):
            c1 = 9 + 2 * k
            nm = ws.cell(row=8, column=c1).value
            if nm and '(Disponible)' not in str(nm):
                found += 1
                pct = ws.cell(row=DATA0, column=c1 + 1).value
                assert isinstance(pct, str) and pct.startswith('='), \
                    f'{name}: L{k+1} sin fórmula de % en fila {DATA0}'
        assert found >= 1, f'{name}: ningún lead activo en fila 8'


def test_dashboard_layout():
    ws = wb()['Dashboard']
    assert ws['C4'].value is not None, 'Dashboard: falta meta anual en C4'
    assert ws.cell(row=7, column=1).value is not None, 'Dashboard: falta primer mes en A7'
    f = ws.cell(row=7, column=4).value
    assert isinstance(f, str) and f.startswith('='), 'Dashboard: D7 debe ser fórmula'


def test_html_parser_matches():
    """El parser del HTML debe leer las mismas celdas ancla del contrato."""
    assert os.path.exists(HTML_PATH), f'falta {HTML_PATH}'
    html = open(HTML_PATH, encoding='utf-8').read()
    for anchor in ("g('B2')", "g('B4')", "g('B5')", "g('E10')", "g('B'+r)",
                   "g('C4')", "encode_col(8+2*k)"):
        assert anchor in html, f'parser: ancla {anchor} no encontrada — contrato roto'
    assert "const CONFIG = { DATA_URL: ''" in html, (
        'falta la línea CONFIG exacta — el workflow de Azure parchea esa cadena literal')


def test_recalculated():
    """SheetJS lee valores cacheados: el workbook publicado debe estar recalculado."""
    book = load_workbook(WB_PATH, data_only=True)
    name = [n for n in book.sheetnames if n not in ('Dashboard', 'Instrucciones')][0]
    ws = book[name]
    v = ws.cell(row=DATA0, column=3).value  # Meta: fórmula en tabs acum, constante en nivel
    assert v is not None, ('Sin valores cacheados: ejecutar python3 scripts/recalc.py ' + WB_PATH)


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for fn in fns:
        fn()
        print(f'OK  {fn.__name__}')
    print(f'\n{len(fns)} pruebas de contrato pasaron.')
