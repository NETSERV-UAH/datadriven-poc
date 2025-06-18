#!/bin/bash
set -e

echo "[INFO] Lanzando InfluxDB y configurando entorno inicial..."

influxd &

until curl -s http://localhost:8086/health | grep -q '"status":"pass"'; do
    echo "[INFO] Esperando a que InfluxDB esté disponible..."
    sleep 2
done

echo "[INFO] InfluxDB está listo. Realizando configuración inicial..."

curl -s -X POST http://localhost:8086/api/v2/setup \
-H "Content-Type: application/json" \
--data "{
    \"username\": \"${INFLUXDB_USERNAME}\",
    \"password\": \"${INFLUXDB_PASSWORD}\",
    \"token\": \"${INFLUXDB_TOKEN}\",
    \"org\": \"UAH\",
    \"bucket\": \"iiot_data\"
}"

echo "[INFO] Configuración inicial realizada con éxito."

wait

