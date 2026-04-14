FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY utils.py n8n_hybrid_server.py ./

EXPOSE 8000

CMD ["python", "n8n_hybrid_server.py"]
