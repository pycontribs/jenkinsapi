.PHONY: test lint tox coverage dist

test:
	uv run pytest -sv jenkinsapi_tests

lint:
	uv run pycodestyle
	uv run pylint jenkinsapi/*.py
	uv run flake8 jenkinsapi/ --count --select=E9,F63,F7,F82 --ignore F821,W503,W504 --show-source --statistics
	uv run flake8 jenkinsapi/ --count --exit-zero --max-complexity=10 --max-line-length=79 --statistics

tox:
	tox

dist:
	uv build

coverage:
	uv run pytest -sv --cov=jenkinsapi --cov-report=term-missing --cov-report=xml jenkinsapi_tests
