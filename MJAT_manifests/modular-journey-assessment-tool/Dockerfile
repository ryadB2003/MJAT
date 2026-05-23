FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api.py .
COPY assessment_ui.html .
COPY models/ ./models/
COPY logic/ ./logic/

# Expose ports
EXPOSE 8000 8080

# Start script
COPY <<EOF /app/start.sh
#!/bin/bash
echo ""
echo "============================================"
echo "  Migration Assessment Tool Running"
echo "============================================"
echo "  UI:  http://localhost:8080/assessment_ui.html"
echo "  API: http://localhost:8000/docs"
echo "============================================"
echo ""
python -m http.server 8080 &
exec uvicorn api:app --host 0.0.0.0 --port 8000
EOF
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
