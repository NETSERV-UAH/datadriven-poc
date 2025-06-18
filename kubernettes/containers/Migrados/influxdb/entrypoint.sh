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
--data '{
    "username": "jorge",
    "password": "ELPORRAS",
    "token": "3hv3m8nphSlHRbVbKQ7o5Hrm0S4FhLDhu8WWGt9abXHQ26Ked4hGDSRqtZsYC-hc2gS9snCLjN5p9OnoYBeRYA==",
    "org": "UAH",
    "bucket": "iiot_data"
}'
echo "[INFO] Configuración inicial realizada con éxito."



wait

