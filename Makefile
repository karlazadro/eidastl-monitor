.PHONY: venv install run clean lint test

venv:
	python3 -m venv .venv

install:
	. .venv/bin/activate && pip install -r requirements.txt

run:
	. .venv/bin/activate && python -m src.run_all

clean:
	rm -f eidastl.sqlite
	rm -rf reports/*
	touch reports/.gitkeep

lint:
	. .venv/bin/activate && ruff check .

test:
	. .venv/bin/activate && pytest -q
