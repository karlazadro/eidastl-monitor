COUNTRIES ?= HR,SI,DE

.PHONY: run test lint clean

run:
	. .venv/bin/activate && COUNTRIES=$(COUNTRIES) python -m src.run_all

test:
	. .venv/bin/activate && pytest -q

clean:
	rm -f eidastl.sqlite
	rm -rf reports/*
	rm -rf data_raw/*