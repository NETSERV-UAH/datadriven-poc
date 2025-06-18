#!/bin/bash
set -e

echo "[INFO] Iniciando contenedor de Grafana..."

# Descargamos los ficheros de configuracion
echo "[INFO] Descargando ficheros"

wget -q -O /var/lib/grafana/dashboards/dashboard.json https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/grafana/dashboards/dashboard.json

wget -q -O /etc/grafana/provisioning/dashboards/dashboard.yaml https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/grafana/provisioning/dashboards/dashboards.yaml

wget -q -O /etc/grafana/provisioning/datasources/influxdb_datasource.yaml https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/grafana/provisioning/datasources/influxdb_datasource.yaml

echo "[INFO] Lanzando grafana..."
exec /usr/sbin/grafana-server --config=/etc/grafana/grafana.ini --homepath=/usr/share/grafana web
