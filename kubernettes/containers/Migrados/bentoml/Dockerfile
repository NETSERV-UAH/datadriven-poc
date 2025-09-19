FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y python3-pip python3.10 python3.10-dev git curl wget && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
COPY train.py .
COPY service.py .
COPY bentofile.yaml .

RUN pip install -r requirements.txt
RUN mkdir -p dataset && wget -O dataset/manufacturing_6G_dataset.csv https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/bentoml/dataset/manufacturing_6G_dataset.csv
RUN python3 train.py

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]

