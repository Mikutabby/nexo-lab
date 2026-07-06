#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Shell syntax check (bash -n) ==="
errors=0
while IFS= read -r -d '' f; do
    if bash -n "$f" 2>/dev/null; then
        echo "  OK  $f"
    else
        echo "  FAIL $f"
        errors=$((errors + 1))
    fi
done < <(find . -name '*.sh' -type f -print0; find . -path ./tests -prune -o -type f ! -name '*.py' ! -name '*.md' ! -name '*.json' ! -name '*.service' ! -name '*.example' -exec grep -l '^#!/bin/bash' {} \; -print0 2>/dev/null)

echo ""
echo "=== Python syntax check ==="
while IFS= read -r -d '' f; do
    if python3 -m py_compile "$f" 2>/dev/null; then
        echo "  OK  $f"
    else
        echo "  FAIL $f"
        errors=$((errors + 1))
    fi
done < <(find memory/ tools/ -type f -exec grep -l '^#!/usr/bin/env python3' {} \; -print0 2>/dev/null)

if command -v pytest &>/dev/null; then
    echo ""
    echo "=== pytest ==="
    python3 -m pytest tests/test_nexo_graph.py -v --tb=short || errors=$((errors + 1))
fi

if command -v bats &>/dev/null; then
    echo ""
    echo "=== bats ==="
    bats tests/test_shell.bats || errors=$((errors + 1))
fi

echo ""
if [ "$errors" -eq 0 ]; then
    echo "✅ All checks passed"
else
    echo "❌ $errors check(s) failed"
fi
exit "$errors"
