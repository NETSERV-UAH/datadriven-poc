#!/bin/bash

sudo -u vagrant bash << 'EOF'

## ns ##
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/factoryfloor/ff-ns.yaml

## ns ##
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/datadriven/datadriven-ns.yaml

kubectl apply -f - <<'EOM'
apiVersion: v1
kind: Secret
metadata:
  name: ghcr-secret
  namespace: datadriven
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: ewoJImF1dGhzIjogewoJCSJnaGNyLmlvIjogewoJCQkiYXV0aCI6ICJiV0Z1ZDI5c1puSmhiV2x2T21kb2NGOWFNM1phT0RkNFJuQlNWMlJQYVVOeVltUTFPVmgyVDFnNGNHbGFiV1V3Y2xNMFV6RT0iCgkJfSwKCQkiaHR0cHM6Ly9pbmRleC5kb2NrZXIuaW8vdjEvIjogewoJCQkiYXV0aCI6ICJiV0Z1ZDI5c1puSmhiV2x2T25Gd2MybE9UVkkzSXc9PSIKCQl9Cgl9Cn0=
EOM
EOF

