FROM python:3.12

WORKDIR /app

COPY ./bot /app/
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
