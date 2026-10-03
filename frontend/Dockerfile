FROM python:3.12-alpine

WORKDIR /app

ENV FRONTEND_HOST=0.0.0.0 \
    FRONTEND_PORT=8000 \
    TASK_API_HOST=backend \
    TASK_API_PORT=5000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY index.html styles.css app.js dev_server.py ./

EXPOSE 8000

CMD ["python", "dev_server.py"]
