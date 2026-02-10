COUNTRIES ?= HR,SI,DE

run:
	. .venv/bin/activate && COUNTRIES=$(COUNTRIES) python -m src.run_all