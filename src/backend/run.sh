#!/bin/bash

# Получаем директорию, где находится скрипт
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
(
    export PYTHONPATH="$BACKEND_DIR"

    echo "PYTHONPATH set to: $PYTHONPATH"

    # Активируем виртуальное окружение, если оно существует
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo "Virtual environment activated"
    fi

    echo "Starting FastAPI application..."
    echo "Server will be available at: http://localhost:8000"
    echo "Use http://localhost:8000/docs to see all endpoints"
    echo "Press Ctrl+C to stop"
    echo ""

    # Запускаем сервер
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
)

echo ""
echo "Application stopped"
