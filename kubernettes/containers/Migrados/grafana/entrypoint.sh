#!/bin/bash
set -e

echo "[INFO] Iniciando contenedor de Grafana..."
: "${GF_SECURITY_ADMIN_USER:?Falta GF_SECURITY_ADMIN_USER}"
: "${GF_SECURITY_ADMIN_PASSWORD:?Falta GF_SECURITY_ADMIN_PASSWORD}"
: "${INFLUX_URL:?Falta INFLUX_URL}"
: "${INFLUX_USER:?Falta INFLUX_USER}"
: "${INFLUX_PASSWORD:?Falta INFLUX_PASSWORD}"
: "${INFLUX_TOKEN:?Falta INFLUX_TOKEN}"
echo "[INFO] Descargando ficheros"

mkdir -p /var/lib/grafana/dashboards
mkdir -p /etc/grafana/provisioning/dashboards
mkdir -p /tmp

wget -q -O /var/lib/grafana/dashboards/dashboard.json https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/grafana/dashboards/dashboard.json
wget -q -O /etc/grafana/provisioning/dashboards/dashboard.yaml https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/grafana/provisioning/dashboards/dashboards.yaml
wget -q -O /tmp/influxdb_datasource.yaml.tpl https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/grafana/provisioning/datasources/influxdb_datasource.yaml.tpl
wget -q -O /tmp/grafana.ini.tpl https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/containers/Migrados/grafana/grafana.ini.tpl

echo "[INFO] Procesando plantillas..."
envsubst < /tmp/influxdb_datasource.yaml.tpl > /etc/grafana/provisioning/datasources/influxdb_datasource.yaml
envsubst < /tmp/grafana.ini.tpl > /etc/grafana/grafana.ini
echo "[INFO] Lanzando Grafana..."
exec /usr/sbin/grafana-server --config=/etc/grafana/grafana.ini --homepath=/usr/share/grafana --packaging=deb web

