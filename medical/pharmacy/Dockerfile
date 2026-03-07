FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/lib/survive/pharmacy /etc/survive

# Seed the database at build time
RUN python -m seed.seed_data

EXPOSE 8040

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8040"]
