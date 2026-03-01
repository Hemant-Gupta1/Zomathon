FROM python:3.10-slim

WORKDIR /app

# 1. Install ONLY the core light dependencies. PyTorch removed for speed constraints.
COPY requirements.txt .
RUN pip install --default-timeout=2000 --retries=10 --no-cache-dir -r requirements.txt

# 2. Copy project files
COPY . .

EXPOSE 8080
CMD ["python", "main.py"]