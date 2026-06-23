#!/usr/bin/env python3
"""Construye la base de Airtable 'Wigs Nicaragua' (esquema + datos semilla).

Opción A del plan: Airtable es el SISTEMA DE REGISTRO donde los dueños digitan
los datos. El cálculo (acumulados, %, estado, cobertura) sigue viviendo en el
Excel: un sync posterior leerá esta base y reconstruirá Tablero_WIG_4DX_GBM.xlsx
→ recalc → TV. Por eso aquí solo guardamos ENTRADAS + ESTRUCTURA, nunca celdas
calculadas.

Esta es la alternativa sin MCP: usa la API REST de Airtable con un token (PAT).
No requiere aprobar el conector; corre como cualquier script del repo.

Uso:
    export AIRTABLE_TOKEN=pat_xxx          # PAT con scopes:
    #   schema.bases:read, schema.bases:write, data.records:read, data.records:write
    export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX   # la base que creaste ("WIGS")
    python3 excel/build_airtable.py            # crea tablas + semilla
    python3 excel/build_airtable.py --dry-run  # imprime el plan, no escribe

Idempotencia: salta tablas/registros que ya existen por nombre, así que se
puede re-correr sin duplicar.

NOTA DE SINCRONÍA: los datos de WIGS / BACKLOG_YEARS / TRAJ son una copia
verbatim de excel/build_wig.py (la fuente de verdad de la estructura). Si se
edita allá, actualizar aquí. (TODO: extraer a excel/wig_data.py compartido.)
"""
import os
import sys
import time
import json
from datetime import date

import requests

# --- formatos de número (mismas claves que build_wig.py) ---
PCT = '0.0%'; CNT = '#,##0'; USD = '"$"#,##0'; DEC = '0.0'

# ============================================================================
# DATOS — copia verbatim de excel/build_wig.py (mantener en sync)
# ============================================================================
WIGS = [
    dict(tab='1. Smart User 500', title='WIG 1 — Incrementar el Parque de Smart User en 500 equipos en el 2026',
         lag='Equipos Smart User colocados (acumulado). 500 equipos a $40/mes = $6.4K MRR adicional en GP.',
         fromto='De 0 a 500 equipos colocados, antes del 31 de diciembre de 2026.',
         equipo='Pre-Sales, Del - DEX', meta=500, fmt=CNT, tipo='acum', freq='W',
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
         equipo='Ventas, Customer Success, Pre-Sales, Del - TSS', meta=10000, fmt=USD, tipo='acum', freq='W', meta_x=True,
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
         equipo='Ventas, Pre-Sales', meta=10, fmt=CNT, tipo='acum', freq='W',
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
         equipo='Finanzas', meta=1.0, fmt=PCT, tipo='nivel_min', freq='W', riesgo=0.05,
         leads=[('% entregas programadas con checklist completo', 1.0, PCT),
                ('Riesgos de entrega escalados ≥1 semana antes', 1, CNT),
                ('% órdenes de compra liberadas a tiempo', 1.0, PCT),
                ('% inventario confirmado ≥5 días antes', 1.0, PCT),
                ('Coordinaciones logísticas confirmadas', 5, CNT),
                ('% facturas emitidas ≤48h tras la entrega', 1.0, PCT)]),
    dict(tab='5. MV Datacenter', title='WIG 5 — Incrementar el MV de servicios basados en el DC GBM San Marcos en $20,000',
         lag='MV nuevo firmado de servicios basados desde el datacenter (USD acumulado).',
         fromto='De $0 a +$20,000 de MV incremental, antes del 31 de diciembre de 2027.',
         equipo='Pre-Sales, Del - DC', meta=20000, fmt=USD, tipo='acum', freq='W',
         leads=[('Propuestas de servicios DC presentadas', 2, CNT),
                ('Workloads nuevos aprovisionados / migrados', 1, CNT),
                ('Assessments de migración realizados', 1, CNT),
                ('Opps DC activas en pipeline', 4, CNT),
                ('Clientes contactados con oferta DC', 3, CNT),
                ('% capacidad DC documentada y actualizada', 1.0, PCT)]),
    dict(tab='6. Cero Expired', title='WIG 6 — Tener cero contratos expired en al menos 16 de los próximos 18 meses',
         lag='Contratos en estado Expired / On-Hold al cierre de la semana (meta: 0).',
         fromto='De N a 0 contratos expired, sosteniéndolo en 16 de los próximos 18 meses (jun 2026 – dic 2027).',
         equipo='Customer Success, Del - DEX, Del - TSS, Del - DC', meta=0, fmt=CNT, tipo='nivel_max', freq='W', riesgo=1,
         leads=[('% contratos por vencer en 90 días con plan', 1.0, PCT),
                ('Renovaciones cerradas a tiempo en la semana', 2, CNT),
                ('Cotizaciones de renovación enviadas ≥60 días antes', 3, CNT),
                ('QBRs con clientes en riesgo de no renovar', 1, CNT),
                ('% contratos on-hold con plan de reactivación', 1.0, PCT),
                ('Forecast de renovaciones actualizado (1 = sí)', 1, CNT)]),
    dict(tab='7. MV Digital Sol', title='WIG 7 — Incrementar el MV de Digital Solutions en $30K/mes al 1ro de mayo 2027',
         lag='MV incremental firmado de servicios Digital Solutions (SOC y Célula), USD acumulado.',
         fromto='De $0 a +$30,000 de MV mensual, antes del 1 de mayo de 2027.',
         equipo='Ventas, Del - DS', meta=30000, fmt=USD, tipo='acum', freq='W',
         leads=[('Opps SOC / Célula activas en pipeline', 4, CNT),
                ('Propuestas DS presentadas', 2, CNT),
                ('Demos / PoV de SOC ejecutados', 1, CNT),
                ('Workshops de células de desarrollo', 1, CNT),
                ('Casos de éxito / referencias compartidas', 1, CNT),
                ('Opps DS avanzadas de etapa', 2, CNT)]),
    dict(tab='8. GP 16%', title='WIG 8 — Lograr un GP consolidado de 16% en el 2027',
         lag='GP consolidado del mes (%).',
         fromto='De GP actual a 16% consolidado sostenido en 2027.',
         equipo='Finanzas (todas las áreas aportan)', meta=0.16, fmt=PCT, tipo='nivel_min', freq='M', riesgo=0.01,
         leads=[('% distribuciones del mes vs plan de baja distribución', 1.0, PCT),
                ('% reservas (inventario + ITA + IR) bajo el tope del plan', 1.0, PCT),
                ('% negocios cotizados con GP ≥ margen mínimo', 1.0, PCT),
                ('Acciones de recuperación de margen ejecutadas', 2, CNT),
                ('Revisiones de pricing realizadas en el mes', 4, CNT),
                ('% proyectos con revisión de rentabilidad mensual', 1.0, PCT)]),
    dict(tab='9. CSAT', title='WIG 9 — Incrementar el CSAT de X a Y, sosteniéndolo 4 meses consecutivos',
         lag='CSAT del mes (puntaje de encuestas de satisfacción).',
         fromto='De X a Y, con 4 meses consecutivos en la meta. (Definir X y Y en la celda Meta)',
         equipo='Customer Success (todas las áreas de entrega aportan)', meta=4.5, fmt=DEC, tipo='nivel_min', freq='M', riesgo=0.3, meta_x=True,
         leads=[('% encuestas CSAT enviadas y respondidas', 0.60, PCT),
                ('QBRs / touchpoints de CS ejecutados', 8, CNT),
                ('% detractores con plan de acción en ≤5 días', 1.0, PCT),
                ('% casos críticos resueltos dentro del SLA', 0.95, PCT),
                ('Llamadas proactivas de CSM en el mes', 12, CNT),
                ('Promotores contactados para referencia', 3, CNT)]),
    dict(tab='10. Apalancamiento', title='WIG 10 — Sostener costos locales planos mientras crece el ingreso (apalancamiento operativo)',
         lag='Costo indirecto local + OREX del mes como % del ingreso del mes (objetivo: que BAJE al crecer ventas).',
         fromto='De ~13% (local+OREX / ingreso) hacia ≤9% sostenido, manteniendo el costo local en valor absoluto plano mientras el ingreso crece.',
         equipo='Finanzas, Customer Success, todas las áreas locales', meta=0.09, fmt=PCT, tipo='nivel_max', freq='M', riesgo=0.01,
         leads=[('Costo local absoluto del mes vs. mes base (≤100%)', 1.0, PCT),
                ('Headcount local de apoyo vs. plan plano (≤100%)', 1.0, PCT),
                ('Vacantes de apoyo cubiertas con productividad, no contratación', 1, CNT),
                ('% de crecimiento de ingreso absorbido sin nuevo costo local', 1.0, PCT),
                ('Iniciativas de automatización/eficiencia en marcha', 1, CNT),
                ('Revisión mensual de costo local por área ejecutada (1 = sí)', 1, CNT)]),
    dict(tab='11. Recuperar DS', title='WIG 11 — Recuperar el margen de Digital Solutions y eliminar líneas con GP negativo',
         lag='GP del mes de las líneas hoy negativas (Digital Solutions + service-attach): de negativo a positivo (USD).',
         fromto='De ~-$78K/mes de arrastre (DS + líneas negativas) a GP ≥ $0 y luego positivo, antes de dic 2027.',
         equipo='Ventas, Pre-Sales, Del - DS, Finanzas', meta=0, fmt=USD, tipo='nivel_min', freq='M', riesgo=10000,
         leads=[('% negocios DS cotizados con GP ≥ piso de margen', 1.0, PCT),
                ('Líneas con GP negativo re-precificadas o cerradas (acum.)', 1, CNT),
                ('Contratos DS renegociados al alza en el mes', 1, CNT),
                ('% utilización de la célula / SOC', 0.70, PCT),
                ('Revisión de rentabilidad por línea DS ejecutada (1 = sí)', 1, CNT),
                ('Casos de service-attach negativo investigados', 2, CNT)]),
    dict(tab='12. Utilizacion', title='WIG 12 — Subir la utilización facturable de ingenieros locales de 42% a 48%+',
         lag='% de horas facturables sobre horas disponibles de los ingenieros locales (mes). Costo ya fijo = margen directo.',
         fromto='De 42% a ≥48% de utilización facturable, sostenido, antes de dic 2027.',
         equipo='Del - TSS, Del - DC, Customer Success, Pre-Sales', meta=0.48, fmt=PCT, tipo='nivel_min', freq='M', riesgo=0.03,
         leads=[('Horas facturables registradas en el mes vs. meta', 1.0, PCT),
                ('% de timesheets completos y a tiempo', 1.0, PCT),
                ('Horas advisory/billable vendidas en el mes', 40, CNT),
                ('Ingenieros con utilización < 40% con plan de acción', 1, CNT),
                ('Proyectos con staffing confirmado 2 semanas antes', 3, CNT),
                ('% de horas no facturables justificadas/categorizadas', 1.0, PCT)]),
]

# (etiqueta, ingreso, GP%, NAT meta, pestaña del año o None para la base)
TRAJ = [('2026 (estimado)', 18656000, 0.144, 375000, None),
        ('2027 (meta)', 21000000, 0.16, 1000000, '2027'),
        ('2028 (meta)', 28571000, 0.164, 2000000, '2028'),
        ('2029 (meta)', 30571000, 0.165, 2445680, '2029')]

# año → GP% es supuesto editable (solo 2029 hoy)
GP_ASSUMED = {'2029'}

# ----------------------------------------------------------------------------
# Mapeos de formato → opciones de Airtable
# ----------------------------------------------------------------------------
FMT_LABEL = {USD: 'Dinero $', PCT: 'Porcentaje %', CNT: 'Número', DEC: 'Decimal'}
FREQ_LABEL = {'W': 'Semanal', 'M': 'Mensual'}


def sl(name, **kw):      return dict(name=name, type='singleLineText', **kw)
def ml(name):            return dict(name=name, type='multilineText')
def num(name, p=0):      return dict(name=name, type='number', options=dict(precision=p))
def pct(name, p=1):      return dict(name=name, type='percent', options=dict(precision=p))
def cur(name, p=0):      return dict(name=name, type='currency', options=dict(precision=p, symbol='$'))
def dt(name):            return dict(name=name, type='date', options=dict(dateFormat=dict(name='iso')))
def chk(name):           return dict(name=name, type='checkbox', options=dict(icon='check', color='greenBright'))
def sel(name, *opts):    return dict(name=name, type='singleSelect', options=dict(choices=[dict(name=o) for o in opts]))
def link(name, table):   return dict(name=name, type='multipleRecordLinks', _link=table)  # _link resuelto en fase 2


# ============================================================================
# Esquema — 9 tablas. Los campos `link(...)` se crean en una 2da fase (necesitan
# el ID de la tabla destino).
# ============================================================================
TABLES = {
    'WIGs': [
        sl('Nombre'),                       # primario, ej. "1. Smart User 500"
        num('Número'),
        sl('Título'),
        ml('Lag'),
        ml('De X a Y'),
        sl('Dueño'),                        # entrada
        sl('Equipo'),
        num('Meta', 4),                     # valor crudo; el formato lo dicta MetaFormato
        sel('MetaFormato', 'Dinero $', 'Porcentaje %', 'Número', 'Decimal'),
        sel('Tipo', 'acum', 'nivel_min', 'nivel_max'),
        sel('Frecuencia', 'Semanal', 'Mensual'),
        num('RiesgoUmbral', 4),
        link('Líderes', 'Colaboradores'),   # quién está en el equipo (TRMNL)
    ],
    'Leads': [
        sl('Nombre'),
        link('WIG', 'WIGs'),
        num('Slot'),
        num('Meta', 4),
        sel('Formato', 'Número', 'Porcentaje %', 'Dinero $', 'Decimal'),
        chk('Apuesta principal'),           # L1/L2
        link('Responsable', 'Colaboradores'),
    ],
    'WIG Readings': [
        sl('Etiqueta'),
        link('WIG', 'WIGs'),
        dt('Fecha'),
        num('Real', 4),                     # entrada (lag real del periodo)
    ],
    'Lead Readings': [
        sl('Etiqueta'),
        link('Lead', 'Leads'),
        dt('Fecha'),
        num('Real', 4),                     # entrada
    ],
    'Years': [
        sl('Año'),                          # "2026" … "2029"
        sl('Etiqueta'),                     # "2027 (meta)"
        cur('Ingreso'),
        pct('GP %'),
        cur('Meta NAT'),
        cur('NAT real'),                    # entrada anual
        chk('Año base'),
        chk('Tiene página'),
        chk('GP% supuesto'),
    ],
    'Backlog Readings': [
        sl('Etiqueta'),
        link('Año', 'Years'),
        dt('Fecha'),
        cur('GP comprometido'),             # entrada (acum.)
    ],
    'NAT Monthly': [
        sl('Mes'),                          # "ene-27"
        dt('Fecha'),
        cur('NAT real'),                    # entrada
    ],
    'Colaboradores': [                      # People — para las pantallas TRMNL
        sl('Nombre'),
        dict(name='Email', type='email'),
        sl('Área'),
        sl('TRMNL ID'),                     # id del dispositivo en el escritorio
        chk('Activo'),
    ],
    'Compromisos': [                        # commitments semanales (qué trabajar)
        sl('Compromiso'),
        dt('Semana'),
        link('WIG', 'WIGs'),
        link('Lead', 'Leads'),
        link('Responsable', 'Colaboradores'),
        sel('Estado', 'Pendiente', 'Hecho'),
    ],
}

# Orden de creación: las tablas sin dependencia de enlace primero no es
# obligatorio (los enlaces se agregan en fase 2), pero conviene un orden estable.
TABLE_ORDER = ['Colaboradores', 'WIGs', 'Leads', 'WIG Readings', 'Lead Readings',
               'Years', 'Backlog Readings', 'NAT Monthly', 'Compromisos']


# ============================================================================
# Cliente REST mínimo
# ============================================================================
class Airtable:
    def __init__(self, token, base_id, dry=False):
        self.base = base_id
        self.dry = dry
        self.s = requests.Session()
        self.s.headers.update({'Authorization': f'Bearer {token}',
                               'Content-Type': 'application/json'})

    def _req(self, method, url, **kw):
        for attempt in range(5):
            r = self.s.request(method, url, **kw)
            if r.status_code == 429:               # rate limit
                time.sleep(2 ** attempt); continue
            if r.status_code >= 400:
                raise RuntimeError(f'{method} {url} → {r.status_code}: {r.text}')
            time.sleep(0.22)                       # ~5 req/s cap
            return r.json() if r.text else {}
        raise RuntimeError('rate-limited tras 5 intentos')

    # --- meta (esquema) ---
    def list_tables(self):
        if self.dry: return []
        url = f'https://api.airtable.com/v0/meta/bases/{self.base}/tables'
        return self._req('GET', url).get('tables', [])

    def create_table(self, name, fields):
        url = f'https://api.airtable.com/v0/meta/bases/{self.base}/tables'
        if self.dry:
            print(f'  [dry] tabla {name!r} ({len(fields)} campos)'); return {'id': f'tbl_dry_{name}'}
        return self._req('POST', url, data=json.dumps({'name': name, 'fields': fields}))

    def create_field(self, table_id, field):
        url = f'https://api.airtable.com/v0/meta/bases/{self.base}/tables/{table_id}/fields'
        if self.dry:
            print(f'  [dry] campo {field["name"]!r} en {table_id}'); return {}
        return self._req('POST', url, data=json.dumps(field))

    # --- datos (registros) ---
    def list_records(self, table_id, fields=None):
        if self.dry: return []
        url = f'https://api.airtable.com/v0/{self.base}/{table_id}'
        out, offset = [], None
        while True:
            params = {'pageSize': 100}
            if fields: params['fields[]'] = fields
            if offset: params['offset'] = offset
            j = self._req('GET', url, params=params)
            out += j.get('records', [])
            offset = j.get('offset')
            if not offset: break
        return out

    def create_records(self, table_id, records):
        url = f'https://api.airtable.com/v0/{self.base}/{table_id}'
        ids = []
        for i in range(0, len(records), 10):       # data API: 10/registros por request
            batch = [{'fields': r} for r in records[i:i + 10]]
            if self.dry:
                print(f'  [dry] +{len(batch)} registros en {table_id}')
                ids += [f'rec_dry_{i+j}' for j in range(len(batch))]; continue
            j = self._req('POST', url, data=json.dumps({'records': batch, 'typecast': True}))
            ids += [rec['id'] for rec in j['records']]
        return ids


# ============================================================================
# Construcción
# ============================================================================
def wig_number(tab):  return int(tab.split('.')[0])


def build(at):
    existing = {t['name']: t for t in at.list_tables()}
    ids = {name: t['id'] for name, t in existing.items()}

    # ---- Fase 1: crear tablas con sus campos NO-enlace ----
    print('Fase 1 · tablas + campos base')
    for name in TABLE_ORDER:
        if name in ids:
            print(f'  = {name} (ya existe)'); continue
        plain = [f for f in TABLES[name] if f.get('type') != 'multipleRecordLinks']
        res = at.create_table(name, plain)
        ids[name] = res['id']
        print(f'  + {name}')

    # ---- Fase 2: agregar campos de enlace (ya tenemos todos los IDs) ----
    print('Fase 2 · campos de enlace')
    for name in TABLE_ORDER:
        tid = ids[name]
        have = {f['name'] for f in (existing.get(name, {}).get('fields', []))}
        for f in TABLES[name]:
            if f.get('type') != 'multipleRecordLinks' or f['name'] in have:
                continue
            field = {'name': f['name'], 'type': 'multipleRecordLinks',
                     'options': {'linkedTableId': ids[f['_link']]}}
            at.create_field(tid, field)
            print(f'  + {name}.{f["name"]} → {f["_link"]}')

    # ---- Fase 3: semilla (idempotente por nombre) ----
    print('Fase 3 · datos semilla')

    # WIGs
    wig_have = {r['fields'].get('Nombre'): r['id'] for r in at.list_records(ids['WIGs'])}
    new = []
    for w in WIGS:
        if w['tab'] in wig_have: continue
        new.append(dict(Nombre=w['tab'], Número=wig_number(w['tab']), Título=w['title'],
                        Lag=w['lag'], **{'De X a Y': w['fromto']},
                        Dueño='Por asignar', Equipo=w['equipo'], Meta=w['meta'],
                        MetaFormato=FMT_LABEL[w['fmt']], Tipo=w['tipo'],
                        Frecuencia=FREQ_LABEL[w['freq']], RiesgoUmbral=w.get('riesgo', 0)))
    for rid, w in zip(at.create_records(ids['WIGs'], new), [w for w in WIGS if w['tab'] not in wig_have]):
        wig_have[w['tab']] = rid
    print(f'  WIGs: {len(new)} nuevos / {len(WIGS)} total')

    # Leads (enlazados al WIG por record id)
    lead_have = {r['fields'].get('Nombre') for r in at.list_records(ids['Leads'], fields=['Nombre'])}
    leads = []
    for w in WIGS:
        for i, (nm, meta, fmt) in enumerate(w['leads'][:8], start=1):
            label = f"L{i}. {nm}"
            if label in lead_have: continue
            leads.append(dict(Nombre=label, WIG=[wig_have[w['tab']]], Slot=i,
                              Meta=meta, Formato=FMT_LABEL[fmt],
                              **{'Apuesta principal': i <= 2}))
    at.create_records(ids['Leads'], leads)
    print(f'  Leads: {len(leads)} nuevos')

    # Years
    yr_have = {r['fields'].get('Año') for r in at.list_records(ids['Years'], fields=['Año'])}
    years = []
    for etiqueta, ing, gp, nat, tab in TRAJ:
        y4 = etiqueta[:4]
        if y4 in yr_have: continue
        years.append({'Año': y4, 'Etiqueta': etiqueta, 'Ingreso': ing, 'GP %': gp,
                      'Meta NAT': nat, 'Año base': tab is None,
                      'Tiene página': tab is not None, 'GP% supuesto': y4 in GP_ASSUMED})
    at.create_records(ids['Years'], years)
    print(f'  Years: {len(years)} nuevos')

    # NAT Monthly — 12 meses de 2027 (rejilla lista; NAT real lo digita Finanzas)
    MES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
    nm_have = {r['fields'].get('Mes') for r in at.list_records(ids['NAT Monthly'], fields=['Mes'])}
    months = []
    for i in range(12):
        label = f'{MES[i]}-27'
        if label in nm_have: continue
        months.append({'Mes': label, 'Fecha': date(2027, i + 1, 1).isoformat()})
    at.create_records(ids['NAT Monthly'], months)
    print(f'  NAT Monthly: {len(months)} nuevos')

    print('\n✓ Listo. Las tablas de *Readings* y Compromisos quedan vacías '
          '(las llenan los dueños / un seed de periodos posterior).')


def main():
    dry = '--dry-run' in sys.argv
    token = os.environ.get('AIRTABLE_TOKEN')
    base = os.environ.get('AIRTABLE_BASE_ID')
    if not dry and (not token or not base):
        sys.exit('Falta AIRTABLE_TOKEN o AIRTABLE_BASE_ID en el entorno. '
                 '(usa --dry-run para ver el plan sin escribir)')
    at = Airtable(token or 'dry', base or 'appDRYRUN000000000', dry=dry)
    if dry:
        print('— DRY RUN — no se escribe nada\n')
    build(at)


if __name__ == '__main__':
    main()
