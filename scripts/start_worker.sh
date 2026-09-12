#!/usr/bin/env bash
set -e

export PYTHONPATH="${PYTHONPATH}:$(pwd)/src:$(pwd)"
python3 -m apps.worker.main
