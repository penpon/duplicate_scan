#!/bin/bash

# Run coverage if tests exist, otherwise skip gracefully
if [ -d "tests" ] && [ "$(find tests -name "*.py" -type f | wc -l)" -gt 0 ]; then
    uv run pytest -n auto --cov=src --cov-report=term tests/
else
    echo "No tests found for coverage"
fi
