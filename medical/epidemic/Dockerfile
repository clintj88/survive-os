FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlcipher-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/lib/survive/epidemic /etc/survive

EXPOSE 8040

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8040"]
