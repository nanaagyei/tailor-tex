.PHONY: install install-python install-web dev dev-api dev-web test test-python test-web lint lint-python lint-web format clean

# ──────────────────────────────────────────────
# Install
# ──────────────────────────────────────────────

install: install-python install-web

install-python:
	cd packages/core && uv sync
	cd packages/bench && uv sync
	cd apps/cli && uv sync
	cd apps/api && uv sync

install-web:
	cd apps/web && pnpm install

# ──────────────────────────────────────────────
# Development
# ──────────────────────────────────────────────

dev:
	@echo "Starting API server and web UI..."
	$(MAKE) dev-api & $(MAKE) dev-web & wait

dev-api:
	cd apps/api && uv run uvicorn tailortex_api.main:app --host 127.0.0.1 --port 7745 --reload

dev-web:
	cd apps/web && pnpm dev

# ──────────────────────────────────────────────
# Test
# ──────────────────────────────────────────────

test: test-python test-web

test-python:
	cd packages/core && uv run pytest -v
	cd packages/bench && uv run pytest -v
	cd apps/cli && uv run pytest -v
	cd apps/api && uv run pytest -v

test-web:
	cd apps/web && pnpm lint
	cd apps/web && pnpm tsc --noEmit
	cd apps/web && pnpm build

# ──────────────────────────────────────────────
# Lint
# ──────────────────────────────────────────────

lint: lint-python lint-web

lint-python:
	cd packages/core && uv run ruff check src/ tests/
	cd packages/core && uv run mypy src/
	cd packages/bench && uv run ruff check src/ tests/
	cd packages/bench && uv run mypy src/
	cd apps/cli && uv run ruff check src/ tests/
	cd apps/api && uv run ruff check src/ tests/

lint-web:
	cd apps/web && pnpm lint
	cd apps/web && pnpm tsc --noEmit

# ──────────────────────────────────────────────
# Format
# ──────────────────────────────────────────────

format:
	cd packages/core && uv run ruff format src/ tests/
	cd apps/cli && uv run ruff format src/ tests/
	cd apps/api && uv run ruff format src/ tests/

# ──────────────────────────────────────────────
# Clean
# ──────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
