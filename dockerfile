FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY valenbisi_collector.py .

CMD ["python", "valenbisi_collector.py"]
