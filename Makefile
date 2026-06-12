XLSX = dist/Tablero_WIG_4DX_GBM.xlsx
PY = python3

build:
	$(PY) excel/build_wig.py $(XLSX)
	$(PY) scripts/recalc.py $(XLSX)

demo: build
	$(PY) excel/fill_demo_data.py $(XLSX) dist/demo_data.xlsx
	$(PY) scripts/recalc.py dist/demo_data.xlsx
	$(PY) scripts/build_demo.py web/marcador.html dist/demo_data.xlsx dist/demo.html

test:
	$(PY) tests/test_contract.py

migrate: build
	@test -n "$(OLD)" || (echo "Uso: make migrate OLD=/ruta/tablero_con_datos.xlsx" && exit 1)
	$(PY) excel/migrate_data.py "$(OLD)" $(XLSX) dist/Tablero_migrado.xlsx
	$(PY) scripts/recalc.py dist/Tablero_migrado.xlsx

deploy:
	@test -n "$(PGX)" || (echo "Uso: make deploy PGX=usuario@ip" && exit 1)
	scp web/marcador.html $(PGX):/var/www/html/wig/marcador.html

publicar:
	@test -n "$(DATOS)" || (echo "Uso: make publicar DATOS=/ruta/tablero_con_datos.xlsx" && exit 1)
	@test "$$(git branch --show-current)" = "main" || (echo "Publicar solo desde main (el workflow de Azure no corre en otras ramas)" && exit 1)
	git pull --rebase
	WIG_XLSX="$(DATOS)" $(PY) tests/test_contract.py
	cp "$(DATOS)" web/tablero.xlsx
	git add web/tablero.xlsx
	@git diff --cached --quiet -- web/tablero.xlsx \
		&& echo "Tablero sin cambios — nada que publicar" \
		|| git commit -m "data: tablero semanal $$(date +%Y-%m-%d)" -- web/tablero.xlsx
	git push

.PHONY: build demo test migrate deploy publicar
