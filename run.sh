#!/bin/bash
# StockSage - Launch Script
cd "$(dirname "$0")"

echo "🚀 Starting StockSage Web App..."

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run Streamlit on default port 8501
streamlit run app.py
