FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn requests pydantic

COPY service/ ./service/
COPY middleware/ ./middleware/

RUN pip install --no-cache-dir ./middleware/

EXPOSE 8001

CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8001"]
