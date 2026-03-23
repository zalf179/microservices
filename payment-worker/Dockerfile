# Pake slim biar enteng, tapi butuh gcc buat install psycopg2
FROM python:3.9-slim
WORKDIR /app
# Install gcc dan postgresql-dev buat build psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "worker.py"]
