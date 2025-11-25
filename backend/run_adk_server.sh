#!/bin/bash
# Script to run ADK unified server with venv activated

cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Run the unified ADK server
python adk_unified_main.py

