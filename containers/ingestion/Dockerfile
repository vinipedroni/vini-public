FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
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
RUN ls -la
RUN pwd
COPY data_set/model_1 /home/appuser/app/model_1
COPY data_set/model_2 /home/appuser/app/model_2
COPY data_set/model_3 /home/appuser/app/model_3
COPY image_ingestion.py /home/appuser/app
RUN cat image_ingestion.py

RUN ls -la
RUN ls -la model_1
RUN ls -la model_2
RUN ls -la model_3
RUN chown -R appuser /home/appuser/app

USER appuser

ENTRYPOINT ["python3.12", "image_ingestion.py"]