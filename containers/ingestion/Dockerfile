FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .

RUN pip3 install -r requirements.txt --no-cache-dir

EXPOSE 8501

RUN adduser -u 5678 --disabled-password --gecos "" appuser

WORKDIR /home/appuser/app
COPY /containters/ingestion/data_set /home/appuser/app
COPY /containters/ingestion/image_ingestion.py /home/appuser/app

RUN ls -la
RUN chown -R appuser /home/appuser/app

USER appuser

ENTRYPOINT ["python3.12", "image_ingestion.py"]