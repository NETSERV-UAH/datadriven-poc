FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y python3-pip python3.10 python3.10-dev git curl

WORKDIR /app

COPY requirements.txt .
COPY train.py .
COPY service.py .
COPY bentofile.yaml .

RUN pip install -r requirements.txt
RUN mkdir -p dataset && wget -O dataset/IIOT-temp-warn-max.csv https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/bentoml/dataset/IIOT-temp-warn-max.csv
RUN python3 train.py

CMD ["bentoml", "serve", "-p3001", "."]

