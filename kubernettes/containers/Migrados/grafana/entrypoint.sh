#!/bin/bash
set -e

echo "[INFO] Iniciando contenedor de Grafana..."

# Descargamos los ficheros de configuracion
echo "[INFO] Descargando ficheros"

mkdir /etc/grafana/dashboards
wget -q -O /etc/grafana/dashboards/dashboard.yml https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/grafana/provisioning/dashboards/dashboards.yaml

# mkdir /etc/grafana/provisioning/

# mkdir /etc/grafana/provisioning/dashboards/
wget -q -O /etc/grafana/provisioning/dashboards/dashboard.json https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/grafana/dashboards/dashboard.json

# mkdir /etc/grafana/provisioning/datasources/
wget -q -O /etc/grafana/provisioning/datasources/influxdb_datasource.yaml https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/grafana/provisioning/datasources/influxdb_datasource.yaml

# Ejecutar Grafana como proceso principal del contenedor
echo "[INFO] Lanzando grafana..."
exec /usr/sbin/grafana-server --config=/etc/grafana/grafana.ini --homepath=/usr/share/grafana web
