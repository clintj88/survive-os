FROM python:3.11-slim

WORKDIR /opt/survive/agriculture/sensors

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/lib/survive/sensors /etc/survive
COPY sensors.yml /etc/survive/sensors.yml

EXPOSE 8030

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8030"]
