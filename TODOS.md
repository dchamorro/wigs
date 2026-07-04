# TODOS

Pendientes conocidos del proyecto, agrupados por componente y priorizados
P0 (urgente) → P4 (algún día). Los ítems completados se mueven al final.

## Marcador TV (web/marcador.html)

### Empotrar las fuentes para identidad offline real
**Priority:** P2
Saira Condensed e Inter se cargan de Google Fonts; el fallback (Arial Narrow)
ya es digno, pero el kiosko offline pierde la identidad visual. Empotrar los
woff2 en base64 (~120KB) o servirlos junto al HTML.
_Deferred from /design-review 2026-07-02 (DEFER-001)._

### Breakpoints por ancho para vistas remotas (teléfono)
**Priority:** P2
El layout es TV-first con `overflow:hidden`; quien abre el sitio de Azure en
un teléfono ve contenido recortado. Agregar un fallback apilado con scroll
bajo cierto ancho.
_Deferred from /design-review 2026-07-02 (DEFER-003)._

### Estados hover/focus-visible en chips y botones del pie
**Priority:** P3
Solo `.lead` tiene estados completos; `.wschip`, `.yrchip` y los botones del
pie carecen de `:focus-visible`/`:active` pese al soporte de teclado.
_Deferred from /design-review 2026-07-02 (DEFER-004)._

### Sistema de tokens de espaciado/radio/tipografía
**Priority:** P3
Los paddings son números mágicos vh/vw con deriva (1.2vw vs 1.4vw). Definir
`--space-*`, `--radius-*`, `--type-*` y mapear componentes.
_Deferred from /design-review 2026-07-02 (DEFER-002)._

### El encabezado #companywig está fijo en el HTML
**Priority:** P3
Dice «$1,000,000 NAT en 2027» aunque el parser ya lee la meta de Dashboard
C19; poblarlo desde los datos al cargar para que no derive.
_Deferred from /design-review 2026-07-02 (DEFER-005)._

### Valores del eje Y en el gráfico SVG del detalle
**Priority:** P4
El gráfico principal (canvas) rotula el eje Y; el SVG del detalle no.
_Deferred from /design-review 2026-07-02 (DEFER-006)._

### Matemática de padding del canvas mezcla px con y sin dpr
**Priority:** P4
`P.l=80*dpr/2` vs `P.r=20,t:18,b:46`; inocuo a dpr 1 (la TV), incorrecto en
pantallas de alta densidad.
_Deferred from /design-review 2026-07-02 (DEFER-007)._

## Completed
