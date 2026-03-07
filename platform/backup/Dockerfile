FROM python:3.11-slim-bookworm

WORKDIR /opt/survive-os

COPY platform/backup/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared/ shared/
COPY platform/backup/ platform/backup/

EXPOSE 8095

CMD ["python3", "-m", "uvicorn", "platform.backup.app.main:app", "--host", "0.0.0.0", "--port", "8095"]
