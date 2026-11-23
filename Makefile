.PHONY: help install test evals analyze doctor benchmark docker-headless docker-visual clean

help:
	@echo "Android-MCP — Enterprise Development Commands:"
	@echo "  make install         Install package and dev dependencies in editable mode"
	@echo "  make test            Run the full PyTest test suite with coverage"
	@echo "  make evals           Run the automated agent evaluation benchmark suite"
	@echo "  make analyze         Run the code analyzer (Quality Gate 1 & Gate 2 verification)"
	@echo "  make doctor          Run the environment diagnostic health check"
	@echo "  make docker-headless Start headless ReDroid container (Production grid)"
	@echo "  make docker-visual   Start visual Budtmo container with noVNC browser UI (:6080)"
	@echo "  make clean           Clean up build artifacts and caches"

install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

test:
	python -m pytest -v --tb=short --cov=android_mcp --cov-report=term

evals:
	python evals/evaluators/eval_runner.py

analyze:
	python skills/code-analyzer/scripts/analyze.py

doctor:
	python skills/android-doctor/scripts/doctor.py

docker-headless:
	docker compose --profile headless up -d

docker-visual:
	docker compose --profile visual up -d

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info .coverage coverage.xml
