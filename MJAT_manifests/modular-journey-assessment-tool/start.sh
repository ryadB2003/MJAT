#!/bin/bash
# Start Migration Assessment Tool

cd "$(dirname "$0")"

echo "Starting Migration Assessment Tool..."

# Activate virtual environment
source venv/bin/activate

# Start API server in background
echo "Starting API server on http://localhost:8000..."
python api.py &
API_PID=$!

# Start HTML server in background
echo "Starting HTML server on http://localhost:8080..."
python -m http.server 8080 &
HTML_PID=$!

echo ""
echo "============================================"
echo "  Migration Assessment Tool Running"
echo "============================================"
echo "  UI:  http://localhost:8080/assessment_ui.html"
echo "  API: http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo "============================================"

# Wait and handle Ctrl+C
trap "echo 'Stopping servers...'; kill $API_PID $HTML_PID 2>/dev/null; exit" INT TERM
wait
