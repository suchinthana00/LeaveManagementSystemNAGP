FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "services.employee_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
