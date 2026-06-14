.PHONY: install test cov lint fmt typecheck run e2e check

install:
	pip install -e ".[dev]"

test:
	pytest -q

cov:
	pytest --cov=capital_mcp --cov-report=term-missing

lint:
	ruff check capital_mcp tests

fmt:
	ruff format capital_mcp tests

typecheck:
	mypy capital_mcp

run:
	capitalcom-mcp run

e2e:
	CAP_MCP_E2E=1 pytest -m e2e -v

check: lint typecheck test
