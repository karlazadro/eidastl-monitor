COUNTRIES ?= HR,SI,DE
PY := . .venv/bin/activate &&

setup:
	python3 -m venv .venv
	$(PY) pip install -r requirements.txt

run:
	$(PY) COUNTRIES=$(COUNTRIES) python -m src.run_all

check:
	$(PY) python -m compileall src

clean:
	rm -f eidastl.sqlite
	rm -rf reports/*
	touch reports/.gitkeep