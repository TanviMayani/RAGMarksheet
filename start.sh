#!/bin/bash

# Start FastAPI backend in the background
echo "Starting FastAPI backend on port 8000..."
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &

# Wait for FastAPI backend to become healthy
echo "Waiting for backend to become available..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/health > /dev/null; then
        echo "Backend is up and running!"
        break
    fi
    sleep 1
done

# Start Streamlit frontend on the assigned PORT (default to 7860 for HuggingFace / Render)
PORT=${PORT:-7860}
echo "Starting Streamlit frontend on port $PORT..."
exec streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false
