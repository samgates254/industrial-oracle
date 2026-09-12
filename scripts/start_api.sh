#!/usr/bin/env bash
set -e

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src:$(pwd)"
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
