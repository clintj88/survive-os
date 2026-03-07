FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/lib/survive/governance /etc/survive

EXPOSE 8070

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8070"]
