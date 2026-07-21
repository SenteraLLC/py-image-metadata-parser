#!/usr/bin/env bash
set -euo pipefail

resolve() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "$1"
    elif command -v "$1.exe" >/dev/null 2>&1; then
        echo "$1.exe"
    else
        echo "error: '$1' not found on PATH" >&2
        exit 127
    fi
}

if [[ -f uv.lock ]]; then
    exec "$(resolve uv)" run mypy .
else
    exec "$(resolve poetry)" run mypy .
fi
