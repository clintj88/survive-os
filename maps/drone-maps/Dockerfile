FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/lib/survive/drone-maps /etc/survive

EXPOSE 8062

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8062"]
