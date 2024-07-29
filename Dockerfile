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
COPY data_set /home/appuser/app
COPY image_ingestion.py /home/appuser/app
COPY inference_ui.py /home/appuser/app

RUN ls -la
RUN chown -R appuser /home/appuser/app

USER appuser

RUN python3.12 image_ingestion.py

ENTRYPOINT ["streamlit", "run", "inference_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]