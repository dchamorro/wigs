from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as col
from openpyxl.chart import LineChart, Reference
from openpyxl.formatting.rule import Rule
from openpyxl.styles.differential import DifferentialStyle
from datetime import date, timedelta

ARIAL = 'Arial'
F_TITLE = Font(name=ARIAL, size=14, bold=True, color='1F3864')
F_LBL = Font(name=ARIAL, size=10, bold=True)
F_TXT = Font(name=ARIAL, size=10)
F_INPUT = Font(name=ARIAL, size=10, color='0000FF')
F_INPUT_S = Font(name=ARIAL, size=9, color='0000FF')
F_FORM = Font(name=ARIAL, size=10, color='000000')
F_LINK = Font(name=ARIAL, size=10, color='008000')
F_HDR = Font(name=ARIAL, size=10, bold=True, color='FFFFFF')
F_HDR_S = Font(name=ARIAL, size=9, bold=True, color='FFFFFF')
FILL_HDR = PatternFill('solid', start_color='1F3864')
FILL_LEAD = PatternFill('solid', start_color='2E5496')
FILL_YEL = PatternFill('solid', start_color='FFFF00')
FILL_GREY = PatternFill('solid', start_color='F2F2F2')
THIN = Side(style='thin', color='BFBFBF')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal='center', vertical='center')
WRAPC = Alignment(horizontal='center', vertical='center', wrap_text=True)
WRAP = Alignment(vertical='top', wrap_text=True)

GREEN_DXF = DifferentialStyle(fill=PatternFill('solid', start_color='C6EFCE'), font=Font(color='006100', name=ARIAL))
YEL_DXF = DifferentialStyle(fill=PatternFill('solid', start_color='FFEB9C'), font=Font(color='9C6500', name=ARIAL))
RED_DXF = DifferentialStyle(fill=PatternFill('solid', start_color='FFC7CE'), font=Font(color='9C0006', name=ARIAL))

def estado_cf(ws, rng):
    first = rng.split(':')[0]
    for txt, dxf in (('En meta', GREEN_DXF), ('Riesgo', YEL_DXF), ('Atrasado', RED_DXF)):
        ws.conditional_formatting.add(rng, Rule(type='containsText', operator='containsText', text=txt, dxf=dxf, formula=[f'NOT(ISERROR(SEARCH("{txt}",{first})))']))

def mondays(start, end):
    d, out = start, []
    while d <= end:
        out.append(d); d += timedelta(days=7)
    return out

def month_firsts(start, n):
    out, y, m = [], start.year, start.month
    for _ in range(n):
        out.append(date(y, m, 1)); m += 1
        if m > 12: m, y = 1, y + 1
    return out

START = date(2026, 6, 15)
MAX_LEADS = 8
PCT = '0.0%'; CNT = '#,##0'; USD = '"$"#,##0'

WIGS = [
    dict(tab='1. Smart User 500', title='WIG 1 — Incrementar el Parque de Smart User en 500 equipos en el 2026',
         lag='Equipos Smart User colocados (acumulado). 500 equipos a $40/mes = $6.4K MRR adicional en GP.',
         fromto='De 0 a 500 equipos colocados, antes del 31 de diciembre de 2026.',
         equipo='Pre-Sales, Del - DEX', meta=500, fmt=CNT, tipo='acum', end=date(2026, 12, 28), freq='W',
         leads=[('Compromisos de asignación firmados (equipos)', 20, CNT),
                ('Demos / POCs activos (Promerica, Disnorte, otros)', 2, CNT),
                ('Presentaciones de oferta Smart User realizadas', 3, CNT),
                ('Equipos cotizados en la semana', 30, CNT),
                ('Equipos en bodega listos para colocar', 40, CNT),
                ('Clientes nuevos contactados con la oferta', 2, CNT),
                ('% equipos colocados en ≤2 semanas tras firma', 1.0, PCT)]),
    dict(tab='2. MV Advisory', title='WIG 2 — Lograr un Monthly Value de $X en advisory en el primer trimestre de 2027',
         lag='MV de horas advisory de ingenieros locales vendidas (USD acumulado). Costo fijo ya cubierto = mayor utilidad.',
         fromto='De $0 a la meta de MV advisory, antes del 31 de marzo de 2027. (Definir $X en la celda Meta)',
         equipo='Ventas, Customer Success, Pre-Sales, Del - TSS', meta=10000, fmt=USD, tipo='acum',
         end=date(2027, 3, 29), freq='W', meta_x=True,
         leads=[('Propuestas de advisory presentadas', 3, CNT),
                ('Horas advisory cotizadas', 40, CNT),
                ('Reuniones de venta consultiva con clientes', 4, CNT),
                ('Assessments / health checks ofrecidos', 2, CNT),
                ('% utilización de ingenieros locales en advisory', 0.20, PCT),
                ('Opps de advisory activas en pipeline', 6, CNT),
                ('Contratos advisory firmados en la semana', 1, CNT)]),
    dict(tab='3. Negocios +30K GP', title='WIG 3 — Reconocer 10 negocios mayores a $30K de GP en el 2027',
         lag='Negocios con GP > $30K reconocidos (acumulado). Negocios grandes que mueven el NAT.',
         fromto='De 0 a 10 negocios > $30K GP reconocidos, antes del 31 de diciembre de 2027.',
         equipo='Ventas, Pre-Sales', meta=10, fmt=CNT, tipo='acum', end=date(2027, 12, 27), freq='W',
         leads=[('Opps > $30K GP activas en pipeline', 5, CNT),
                ('Opps nuevas ingresadas en la semana', 4, CNT),
                ('Propuestas > $30K presentadas', 1, CNT),
                ('Reuniones C-level realizadas', 2, CNT),
                ('Leads activas al cierre de la semana', 10, CNT),
                ('Opps > $30K avanzadas de etapa', 2, CNT),
                ('Win rate de opps > $30K (acumulado)', 0.30, PCT)]),
    dict(tab='4. Entregas 100%', title='WIG 4 — Cumplir el 100% de entregas y colocaciones en tiempo y forma',
         lag='% de colocaciones y entregas de la semana realizadas en tiempo y forma.',
         fromto='Sostener 100% de cumplimiento semanal durante todo el periodo.',
         equipo='Finanzas', meta=1.0, fmt=PCT, tipo='nivel_min', end=date(2027, 12, 27), freq='W', riesgo=0.05,
         leads=[('% entregas programadas con checklist completo', 1.0, PCT),
                ('Riesgos de entrega escalados ≥1 semana antes', 1, CNT),
                ('% órdenes de compra liberadas a tiempo', 1.0, PCT),
                ('% inventario confirmado ≥5 días antes', 1.0, PCT),
                ('Coordinaciones logísticas confirmadas', 5, CNT),
                ('% facturas emitidas ≤48h tras la entrega', 1.0, PCT)]),
    dict(tab='5. MV Datacenter', title='WIG 5 — Incrementar el MV de servicios basados en el DC GBM San Marcos en $20,000',
         lag='MV nuevo firmado de servicios basados desde el datacenter (USD acumulado).',
         fromto='De $0 a +$20,000 de MV incremental, antes del 31 de diciembre de 2027.',
         equipo='Pre-Sales, Del - DC', meta=20000, fmt=USD, tipo='acum', end=date(2027, 12, 27), freq='W',
         leads=[('Propuestas de servicios DC presentadas', 2, CNT),
                ('Workloads nuevos aprovisionados / migrados', 1, CNT),
                ('Assessments de migración realizados', 1, CNT),
                ('Opps DC activas en pipeline', 4, CNT),
                ('Clientes contactados con oferta DC', 3, CNT),
                ('% capacidad DC documentada y actualizada', 1.0, PCT)]),
    dict(tab='6. Cero Expired', title='WIG 6 — Tener cero contratos expired en al menos 16 de los próximos 18 meses',
         lag='Contratos en estado Expired / On-Hold al cierre de la semana (meta: 0).',
         fromto='De N a 0 contratos expired, sosteniéndolo en 16 de los próximos 18 meses (jun 2026 – dic 2027).',
         equipo='Customer Success, Del - DEX, Del - TSS, Del - DC', meta=0, fmt=CNT, tipo='nivel_max',
         end=date(2027, 12, 27), freq='W', riesgo=1,
         leads=[('% contratos por vencer en 90 días con plan', 1.0, PCT),
                ('Renovaciones cerradas a tiempo en la semana', 2, CNT),
                ('Cotizaciones de renovación enviadas ≥60 días antes', 3, CNT),
                ('QBRs con clientes en riesgo de no renovar', 1, CNT),
                ('% contratos on-hold con plan de reactivación', 1.0, PCT),
                ('Forecast de renovaciones actualizado (1 = sí)', 1, CNT)]),
    dict(tab='7. MV Digital Sol', title='WIG 7 — Incrementar el MV de Digital Solutions en $30K/mes al 1ro de mayo 2027',
         lag='MV incremental firmado de servicios Digital Solutions (SOC y Célula), USD acumulado.',
         fromto='De $0 a +$30,000 de MV mensual, antes del 1 de mayo de 2027.',
         equipo='Ventas, Del - DS', meta=30000, fmt=USD, tipo='acum', end=date(2027, 4, 26), freq='W',
         leads=[('Opps SOC / Célula activas en pipeline', 4, CNT),
                ('Propuestas DS presentadas', 2, CNT),
                ('Demos / PoV de SOC ejecutados', 1, CNT),
                ('Workshops de células de desarrollo', 1, CNT),
                ('Casos de éxito / referencias compartidas', 1, CNT),
                ('Opps DS avanzadas de etapa', 2, CNT)]),
    dict(tab='8. GP 16%', title='WIG 8 — Lograr un GP consolidado de 16% en el 2027',
         lag='GP consolidado del mes (%).',
         fromto='De GP actual a 16% consolidado sostenido en 2027.',
         equipo='Finanzas (todas las áreas aportan)', meta=0.16, fmt=PCT, tipo='nivel_min',
         end=None, freq='M', riesgo=0.01,
         leads=[('% distribuciones del mes vs plan de baja distribución', 1.0, PCT),
                ('% reservas (inventario + ITA + IR) bajo el tope del plan', 1.0, PCT),
                ('% negocios cotizados con GP ≥ margen mínimo', 1.0, PCT),
                ('Acciones de recuperación de margen ejecutadas', 2, CNT),
                ('Revisiones de pricing realizadas en el mes', 4, CNT),
                ('% proyectos con revisión de rentabilidad mensual', 1.0, PCT)]),
    dict(tab='9. CSAT', title='WIG 9 — Incrementar el CSAT de X a Y, sosteniéndolo 4 meses consecutivos',
         lag='CSAT del mes (puntaje de encuestas de satisfacción).',
         fromto='De X a Y, con 4 meses consecutivos en la meta. (Definir X y Y en la celda Meta)',
         equipo='Customer Success (todas las áreas de entrega aportan)', meta=4.5, fmt='0.0', tipo='nivel_min',
         end=None, freq='M', riesgo=0.3, meta_x=True,
         leads=[('% encuestas CSAT enviadas y respondidas', 0.60, PCT),
                ('QBRs / touchpoints de CS ejecutados', 8, CNT),
                ('% detractores con plan de acción en ≤5 días', 1.0, PCT),
                ('% casos críticos resueltos dentro del SLA', 0.95, PCT),
                ('Llamadas proactivas de CSM en el mes', 12, CNT),
                ('Promotores contactados para referencia', 3, CNT)]),
]

wb = Workbook()
dash = wb.active
dash.title = 'Dashboard'
DATA0 = 11

def build_wig_tab(w):
    ws = wb.create_sheet(w['tab'])
    ws.sheet_view.showGridLines = False
    periods = mondays(START, w['end']) if w['freq'] == 'W' else month_firsts(date(2026, 7, 1), 18)
    plabel = 'Semana' if w['freq'] == 'W' else 'Mes'
    last = DATA0 + len(periods) - 1
    last_lead_col = 8 + 2 * MAX_LEADS

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_lead_col)
    ws['A1'] = w['title']; ws['A1'].font = F_TITLE
    def lbl(c, t): ws[c] = t; ws[c].font = F_LBL
    def txt(c, t, f=F_TXT): ws[c] = t; ws[c].font = f
    lbl('A2', 'Indicador lag:'); txt('B2', w['lag'])
    lbl('A3', 'De X a Y:'); txt('B3', w['fromto'])
    lbl('A4', 'Dueño:'); txt('B4', 'Por asignar', F_INPUT); ws['B4'].fill = FILL_YEL
    lbl('D4', 'Equipo:'); txt('E4', w['equipo'])
    lbl('A5', 'Meta:'); ws['B5'] = w['meta']; ws['B5'].font = F_INPUT; ws['B5'].number_format = w['fmt']
    if w.get('meta_x'): ws['B5'].fill = FILL_YEL
    lbl('D5', 'Inicio:'); ws['E5'] = periods[0]; ws['E5'].font = F_INPUT; ws['E5'].number_format = 'dd-mmm-yy'
    lbl('G5', 'Fin:'); ws['H5'] = periods[-1]; ws['H5'].font = F_INPUT; ws['H5'].number_format = 'dd-mmm-yy'
    lbl('A6', 'Leads:')
    per = 'semanal' if w['freq'] == 'W' else 'mensual'
    txt('B6', f'Hasta {MAX_LEADS} indicadores predictivos a la derecha. L1–L2 = apuesta principal del equipo; L3–L8 = indicadores de apoyo. Nombre (fila 8) y meta {per} (fila 9) editables en azul.')
    lbl('A8', 'Periodos:'); ws['B8'] = f'=COUNT(A{DATA0}:A{last})'; ws['B8'].font = F_FORM
    txt('A9', 'Celdas azules = se digitan cada lunes. Celdas negras = fórmulas, no tocar.', Font(name=ARIAL, size=9, italic=True, color='808080'))

    acum = w['tipo'] == 'acum'
    hdrs = ['#', plabel, ('Meta ' + plabel.lower()) if acum else 'Meta', 'Real',
            'Meta acum.' if acum else '', 'Real acum.' if acum else '',
            '% avance' if acum else 'Brecha vs meta', 'Estado']
    for c, h in enumerate(hdrs, 1):
        cell = ws.cell(row=10, column=c, value=h)
        cell.font = F_HDR; cell.fill = FILL_HDR; cell.alignment = CENTER; cell.border = BORDER

    leads = list(w['leads'])[:MAX_LEADS]
    while len(leads) < MAX_LEADS: leads.append(('(Disponible)', None, CNT))
    lbln = ws.cell(row=8, column=8, value='Lead →'); lbln.font = F_LBL; lbln.alignment = Alignment(horizontal='right', vertical='center')
    lblm = ws.cell(row=9, column=8, value='Meta →'); lblm.font = F_LBL; lblm.alignment = Alignment(horizontal='right', vertical='center')
    for k, (name, meta, fmt) in enumerate(leads):
        c1 = 9 + 2 * k; c2 = c1 + 1
        ws.merge_cells(start_row=8, start_column=c1, end_row=8, end_column=c2)
        nc = ws.cell(row=8, column=c1, value=(f'L{k+1}. {name}' if name != '(Disponible)' else name))
        nc.font = F_INPUT_S; nc.alignment = WRAPC; nc.fill = FILL_GREY
        ws.merge_cells(start_row=9, start_column=c1, end_row=9, end_column=c2)
        mc = ws.cell(row=9, column=c1)
        if meta is not None: mc.value = meta
        mc.font = F_INPUT; mc.number_format = fmt; mc.alignment = CENTER
        for rr in (8, 9):
            for cc in (c1, c2): ws.cell(row=rr, column=cc).border = BORDER
        for cc, h in ((c1, 'Real'), (c2, '%')):
            cell = ws.cell(row=10, column=cc, value=h)
            cell.font = F_HDR_S; cell.fill = FILL_LEAD; cell.alignment = CENTER; cell.border = BORDER
    ws.row_dimensions[8].height = 42

    for i, p in enumerate(periods):
        r = DATA0 + i
        ws.cell(row=r, column=1, value=i + 1).font = F_FORM
        dc = ws.cell(row=r, column=2, value=p); dc.font = F_FORM; dc.number_format = 'dd-mmm-yy' if w['freq'] == 'W' else 'mmm-yy'
        if acum:
            ws.cell(row=r, column=3, value='=$B$5/$B$8').number_format = w['fmt']
            ws.cell(row=r, column=5, value=f'=SUM($C${DATA0}:C{r})').number_format = w['fmt']
            ws.cell(row=r, column=6, value=f'=SUM($D${DATA0}:D{r})').number_format = w['fmt']
            ws.cell(row=r, column=7, value=f'=IF(COUNT($D${DATA0}:D{r})=0,"",F{r}/E{r})').number_format = '0.0%'
            ws.cell(row=r, column=8, value=f'=IF(G{r}="","",IF(G{r}>=0.95,"En meta",IF(G{r}>=0.8,"Riesgo","Atrasado")))')
        else:
            ws.cell(row=r, column=3, value='=$B$5').number_format = w['fmt']
            ws.cell(row=r, column=7, value=f'=IF(D{r}="","",D{r}-C{r})').number_format = w['fmt']
            if w['tipo'] == 'nivel_min':
                ws.cell(row=r, column=8, value=f'=IF(D{r}="","",IF(D{r}>=C{r},"En meta",IF(D{r}>=C{r}-{w["riesgo"]},"Riesgo","Atrasado")))')
            else:
                ws.cell(row=r, column=8, value=f'=IF(D{r}="","",IF(D{r}<=C{r},"En meta",IF(D{r}<=C{r}+{w["riesgo"]},"Riesgo","Atrasado")))')
        for k in range(MAX_LEADS):
            c1 = 9 + 2 * k; L1 = col(c1); ML = f'${L1}$9'
            ws.cell(row=r, column=c1).number_format = leads[k][2]
            ws.cell(row=r, column=c1 + 1, value=f'=IF({L1}{r}="","",IF({ML}="","",IF({ML}=0,"",{L1}{r}/{ML})))').number_format = '0%'
        for c in range(1, last_lead_col + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = BORDER
            is_input = (c == 4) or (c >= 9 and (c - 9) % 2 == 0)
            if is_input: cell.font = F_INPUT_S if c >= 9 else F_INPUT
            else: cell.font = Font(name=ARIAL, size=9) if c >= 9 else F_FORM
            if c in (7, 8) or c >= 9: cell.alignment = CENTER
            if i % 2 == 1 and not is_input: cell.fill = FILL_GREY

    estado_cf(ws, f'H{DATA0}:H{last}')
    ws.freeze_panes = f'C{DATA0}'
    for cl, wd in {'A': 5, 'B': 11, 'C': 12, 'D': 11, 'E': 12, 'F': 12, 'G': 13, 'H': 11}.items():
        ws.column_dimensions[cl].width = wd
    for k in range(MAX_LEADS):
        ws.column_dimensions[col(9 + 2 * k)].width = 11
        ws.column_dimensions[col(10 + 2 * k)].width = 7

    ch = LineChart(); ch.title = 'Marcador: Meta vs Real'; ch.style = 12
    ch.height, ch.width = 8, 16
    if acum: data = Reference(ws, min_col=5, max_col=6, min_row=10, max_row=last)
    else: data = Reference(ws, min_col=3, max_col=4, min_row=10, max_row=last)
    cats = Reference(ws, min_col=2, min_row=DATA0, max_row=last)
    ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
    ch.series[0].graphicalProperties.line.solidFill = 'A6A6A6'
    ch.series[0].graphicalProperties.line.dashStyle = 'dash'
    ch.series[1].graphicalProperties.line.solidFill = '2E75B6'
    ch.series[1].graphicalProperties.line.width = 28000
    ws.add_chart(ch, f'{col(last_lead_col + 2)}2')
    return last

lasts = {w['tab']: build_wig_tab(w) for w in WIGS}

# ---------- Dashboard ----------
ws = dash
ws.sheet_view.showGridLines = False
ws.merge_cells('A1:H1'); ws['A1'] = 'Tablero 4DX — GBM Nicaragua'; ws['A1'].font = Font(name=ARIAL, size=16, bold=True, color='1F3864')
ws.merge_cells('A2:H2'); ws['A2'] = 'WIG de la compañía: Generar $1,000,000 de utilidad neta después de impuestos (NAT) en el 2027'
ws['A2'].font = Font(name=ARIAL, size=11, bold=True)
ws['A4'] = 'Meta anual NAT:'; ws['A4'].font = F_LBL
ws['C4'] = 1000000; ws['C4'].font = F_INPUT; ws['C4'].number_format = USD; ws['C4'].fill = FILL_YEL
hdrs = ['Mes', 'Meta mensual', 'NAT real', 'Meta acum.', 'Real acum.', '% avance', 'Estado']
for c, h in enumerate(hdrs, 1):
    cell = ws.cell(row=6, column=c, value=h)
    cell.font = F_HDR; cell.fill = FILL_HDR; cell.alignment = CENTER; cell.border = BORDER
for i, m in enumerate(month_firsts(date(2027, 1, 1), 12)):
    r = 7 + i
    mc = ws.cell(row=r, column=1, value=m); mc.number_format = 'mmm-yy'; mc.font = F_FORM
    ws.cell(row=r, column=2, value='=$C$4/12').number_format = USD
    rc = ws.cell(row=r, column=3); rc.font = F_INPUT; rc.number_format = USD
    ws.cell(row=r, column=4, value=f'=SUM($B$7:B{r})').number_format = USD
    ws.cell(row=r, column=5, value=f'=SUM($C$7:C{r})').number_format = USD
    ws.cell(row=r, column=6, value=f'=IF(COUNT($C$7:C{r})=0,"",E{r}/D{r})').number_format = '0.0%'
    ws.cell(row=r, column=7, value=f'=IF(F{r}="","",IF(F{r}>=0.95,"En meta",IF(F{r}>=0.8,"Riesgo","Atrasado")))')
    for c in range(1, 8):
        cell = ws.cell(row=r, column=c); cell.border = BORDER
        if c != 3 and cell.font.color is None: cell.font = F_FORM
        if c in (6, 7): cell.alignment = CENTER
        if i % 2 == 1 and c != 3: cell.fill = FILL_GREY
estado_cf(ws, 'G7:G18')
ch = LineChart(); ch.title = 'NAT 2027 — Meta vs Real (acumulado)'; ch.style = 12
ch.height, ch.width = 8, 14
data = Reference(ws, min_col=4, max_col=5, min_row=6, max_row=18)
cats = Reference(ws, min_col=1, min_row=7, max_row=18)
ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
ch.series[0].graphicalProperties.line.solidFill = 'A6A6A6'
ch.series[0].graphicalProperties.line.dashStyle = 'dash'
ch.series[1].graphicalProperties.line.solidFill = '2E75B6'
ch.series[1].graphicalProperties.line.width = 28000
ws.add_chart(ch, 'I4')
R0 = 22
ws.cell(row=R0 - 1, column=1, value='WIGs de soporte — estado al último dato ingresado').font = Font(name=ARIAL, size=12, bold=True, color='1F3864')
hdrs = ['#', 'WIG de soporte', 'Dueño', 'Equipo', 'Meta', 'Último real', 'Estado', 'Ir a pestaña']
for c, h in enumerate(hdrs, 1):
    cell = ws.cell(row=R0, column=c, value=h)
    cell.font = F_HDR; cell.fill = FILL_HDR; cell.alignment = CENTER; cell.border = BORDER
for i, w in enumerate(WIGS):
    r = R0 + 1 + i
    t, last = w['tab'], lasts[w['tab']]
    q = f"'{t}'"
    ws.cell(row=r, column=1, value=i + 1).font = F_FORM
    nm = ws.cell(row=r, column=2, value=w['title'].split('— ')[1]); nm.font = F_FORM; nm.alignment = WRAP
    ws.cell(row=r, column=3, value=f'={q}!$B$4').font = F_LINK
    eq = ws.cell(row=r, column=4, value=w['equipo']); eq.font = F_TXT; eq.alignment = WRAP
    mc = ws.cell(row=r, column=5, value=f'={q}!$B$5'); mc.font = F_LINK; mc.number_format = w['fmt']
    lr = ws.cell(row=r, column=6, value=f'=IFERROR(LOOKUP(2,1/({q}!$D${DATA0}:$D${last}<>""),{q}!$D${DATA0}:$D${last}),"Sin datos")')
    lr.font = F_LINK; lr.number_format = w['fmt']
    es = ws.cell(row=r, column=7, value=f'=IFERROR(LOOKUP(2,1/({q}!$D${DATA0}:$D${last}<>""),{q}!$H${DATA0}:$H${last}),"Sin datos")')
    es.font = F_LINK; es.alignment = CENTER
    lk = ws.cell(row=r, column=8, value=t); lk.hyperlink = f"#'{t}'!A1"; lk.font = Font(name=ARIAL, size=10, color='0563C1', underline='single')
    for c in range(1, 9):
        ws.cell(row=r, column=c).border = BORDER
        if i % 2 == 1: ws.cell(row=r, column=c).fill = FILL_GREY
estado_cf(ws, f'G{R0 + 1}:G{R0 + len(WIGS)}')
for cl, wd in {'A': 5, 'B': 52, 'C': 16, 'D': 30, 'E': 11, 'F': 11, 'G': 11, 'H': 16}.items():
    ws.column_dimensions[cl].width = wd
for i in range(len(WIGS)): ws.row_dimensions[R0 + 1 + i].height = 30

# ---------- Instrucciones ----------
ins = wb.create_sheet('Instrucciones')
ins.sheet_view.showGridLines = False
ins.column_dimensions['A'].width = 110
lines = [
    ('Cómo usar este tablero 4DX', F_TITLE), ('', None),
    ('RITUAL DEL LUNES (antes de la reunión de WIG):', F_LBL),
    ('1. Cada dueño de WIG abre su pestaña y digita en las celdas AZULES de la semana: el resultado real del lag (columna "Real") y el real de cada lead measure (columnas "Real" bajo cada lead, a la derecha).', F_TXT),
    ('2. Finanzas digita el NAT del mes en el Dashboard (columna "NAT real") cuando cierre el mes.', F_TXT),
    ('3. El Dashboard se actualiza solo, y el marcador del televisor se refresca arrastrando este archivo a la pantalla.', F_TXT),
    ('4. Suban el archivo actualizado a Claude cada lunes y pidan el marcador semanal para la reunión de cadencia.', F_TXT),
    ('', None),
    ('LEAD MEASURES (hasta 8 por WIG):', F_LBL),
    ('• Cada WIG tiene hasta 8 indicadores predictivos en columnas a la derecha: el nombre (fila 8) y la meta semanal/mensual (fila 9) son editables en azul.', F_TXT),
    ('• Los leads L1 y L2 son la apuesta principal: ahí el equipo rinde cuentas con compromisos semanales. L3–L8 son indicadores de apoyo que explican el resultado.', F_TXT),
    ('• El % de cada lead se calcula automáticamente contra su meta. Dejar la meta vacía desactiva el lead ("(Disponible)").', F_TXT),
    ('• Definan todos los leads en positivo (más = mejor) para que el % se lea igual en todos.', F_TXT),
    ('', None),
    ('CÓDIGO DE COLORES:', F_LBL),
    ('• Texto AZUL = celdas de entrada. Texto NEGRO = fórmulas (no tocar). Texto VERDE = vínculos entre pestañas.', F_TXT),
    ('• Fondo AMARILLO = supuestos pendientes de definir (dueños, metas "X" de los WIGs 2 y 9).', F_TXT),
    ('• Estado: En meta ≥ 95% del plan · Riesgo 80–95% · Atrasado < 80%.', F_TXT),
    ('', None),
    ('PRINCIPIO 4DX:', F_LBL),
    ('Las lead measures son predictivas e influenciables por el equipo; el lag solo se mueve si las leads se cumplen. En la cadencia semanal cada quien rinde cuentas de sus compromisos sobre las leads, no sobre el lag.', F_TXT),
]
for i, (t, f) in enumerate(lines, 1):
    if t:
        ins.cell(row=i, column=1, value=t).font = f
        ins.cell(row=i, column=1).alignment = WRAP

import sys
out = sys.argv[1] if len(sys.argv) > 1 else 'dist/Tablero_WIG_4DX_GBM.xlsx'
wb.save(out)
print('built', out)
