#!/bin/bash

# Run tests if they exist, otherwise skip gracefully
if [ -d "tests" ] && [ "$(find tests -name "*.py" -type f | wc -l)" -gt 0 ]; then
    uv run pytest -n auto tests/ -v
else
    echo "No tests found"
fi
