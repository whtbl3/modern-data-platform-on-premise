.PHONY: dev up down test lint quality dagster

# Local development
dev: up dagster

up:
	docker compose up -d

down:
	docker compose down

# Run Dagster webserver locally
dagster:
	uv run dagster dev

# Testing
test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/ dagster_project/

lint-fix:
	uv run ruff check --fix src/ dagster_project/

# Data quality
quality:
	uv run soda scan -d lakehouse -c src/quality/soda_checks.yml

# dbt
dbt-run:
	cd src/transforms && uv run dbt run --target dev

dbt-test:
	cd src/transforms && uv run dbt test --target dev

dbt-docs:
	cd src/transforms && uv run dbt docs generate && uv run dbt docs serve

# VietMart data generation
datagen-batch:
	uv run python -m src.datagen --mode batch --pos-txns 10000 --ecom-orders 1000 --clickstream-events 5000

datagen-batch-full:
	uv run python -m src.datagen --mode batch

datagen-stream:
	uv run python -m src.datagen --mode stream --interval 0.5

datagen-flash-sale:
	uv run python -m src.datagen --mode flash-sale

datagen-pos-only:
	uv run python -m src.datagen --mode batch --source pos --pos-txns 50000

datagen-payments-only:
	uv run python -m src.datagen --mode batch --source payments

# Build images
build-spark:
	docker build -t lakehouse-spark:latest -f src/batch/Dockerfile .

build-flink:
	docker build -t lakehouse/flink-vietmart:latest -f src/streaming/Dockerfile .

build-dagster:
	docker build -t lakehouse-dagster:latest -f Dockerfile.dagster .

build: build-spark build-flink build-dagster
