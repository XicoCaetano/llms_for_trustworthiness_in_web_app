# Use an official Python runtime as a parent image
FROM python:3.9

WORKDIR /tool

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["python3", "tool/main.py"]