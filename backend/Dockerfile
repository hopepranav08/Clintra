# Use official Python image
FROM python:3.10-slim

WORKDIR /app

# Copy requirements first (for Docker cache efficiency)
COPY ./requirements.txt /app/requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the backend code
COPY . /app

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
