#!/bin/bash
# FinScan India - Launch Script
cd "$(dirname "$0")"

echo "🚀 Starting FinScan India Web App..."

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run Streamlit on default port 8501
streamlit run app.py
