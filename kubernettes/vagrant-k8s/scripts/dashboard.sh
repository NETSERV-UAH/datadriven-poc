#!/bin/bash
set -e

# Esperar a que el API esté listo
until sudo -u vagrant kubectl get nodes &>/dev/null; do
  echo "Esperando al API server..."
  sleep 5
done

# Despliegue del dashboard
sudo -u vagrant kubectl apply --validate=false -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Crear cuenta de servicio admin
cat <<EOF | sudo -u vagrant kubectl apply --validate=false -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin-user
  namespace: kubernetes-dashboard
EOF

# Asignar permisos admin
cat <<EOF | sudo -u vagrant kubectl apply --validate=false -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: admin-user
  namespace: kubernetes-dashboard
EOF

# Cambiar tipo de servicio a NodePort
sudo -u vagrant kubectl -n kubernetes-dashboard patch svc kubernetes-dashboard \
  -p '{"spec":{"type":"NodePort","ports":[{"port":443,"targetPort":8443,"nodePort":32000}]}}'

# Obtener el puerto asignado
PORT=$(sudo -u vagrant kubectl -n kubernetes-dashboard get svc kubernetes-dashboard -o jsonpath='{.spec.ports[0].nodePort}')

# Obtener el token
TOKEN=$(sudo -u vagrant kubectl -n kubernetes-dashboard create token admin-user)

echo "Dashboard disponible en: https://<IP-NODO-MASTER>:$PORT"
echo "Token de acceso:"
echo "$TOKEN"

