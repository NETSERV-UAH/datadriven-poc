#!/bin/bash

sudo -u vagrant -i bash <<'EOF'
## Datadriven
# ns
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/datadriven-ns.yaml
# influxdb
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/influxdb/influxdb-secrets.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/influxdb/influxdb-pvc.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/influxdb/influxdb-deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/influxdb/influxdb-service.yaml
# Grafana
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/grafana/grafana-secrets.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/grafana/grafana-pvc.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/grafana/grafana-deploy.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/grafana/grafana-service.yaml
# RYU
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/ryu/ryu-secrets.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/ryu/ryu-deploy.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/ryu/ryu-service.yaml
# Bento
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/bentoml/bentoml-deploy.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/bentoml/bentoml-service.yaml
## factory-floor


EOF
