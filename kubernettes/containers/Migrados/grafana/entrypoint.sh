#!/bin/bash
set -e

echo "[INFO] Iniciando contenedor de Grafana..."


# Descargamos los ficheros de configuracion
echo "[INFO] Descargando ficheros"
wget -q -O /etc/grafana/dashboards/dashboard.yml <>
wget -q -O /etc/grafana/provisioning/dashboards/dashboard.json <>
wget -q -O /etc/grafana/provisioning/datasources/influxdb_datasource.yaml <>

# Ejecutar Grafana como proceso principal del contenedor
echo "[INFO] Lanzando grafana..."
exec /usr/sbin/grafana-server --config=/etc/grafana/grafana.ini --homepath=/usr/share/grafana web

