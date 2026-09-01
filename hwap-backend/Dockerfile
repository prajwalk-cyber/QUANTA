FROM python:3.11-slim
RUN apt-get update && apt-get install -y build-essential cmake pkg-config libssl-dev git
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/open-quantum-safe/liboqs-python.git@0.10.0
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
