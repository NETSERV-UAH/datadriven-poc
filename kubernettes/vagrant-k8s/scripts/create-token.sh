#!/bin/bash
set -e

PORT=$(sudo -u vagrant kubectl -n kubernetes-dashboard get svc kubernetes-dashboard -o jsonpath='{.spec.ports[0].nodePort}')

# Obtener el token
TOKEN=$(sudo -u vagrant kubectl -n kubernetes-dashboard create token admin-user)

echo "Dashboard disponible en: https://<IP-NODO-MASTER>:$PORT"
echo "Token de acceso:"
echo "$TOKEN"

