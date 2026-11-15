#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export UV_CACHE_DIR="${UV_CACHE_DIR:-/workspace/.cache/uv}"
uv run --frozen ease-rtc pilot --config configs/experiments/pilot.yaml \
  --output "${1:-data/local/pilot}"
