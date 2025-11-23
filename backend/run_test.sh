#!/bin/bash
# Helper script to run Python tests with venv activated

set -e

cd "$(dirname "$0")"

# Activate venv if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the test script
python test_data_integrity_e2e.py "$@"

