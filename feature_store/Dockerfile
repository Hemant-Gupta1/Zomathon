FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Wait for redis/postgres and initialize Feast repo
CMD ["python", "init_feast.py"]
