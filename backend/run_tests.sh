#!/bin/bash

# Change to the script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest with coverage report
python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Return to the original directory
cd - > /dev/null
