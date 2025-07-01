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
  .dockerconfigjson: ewogICJhdXRocyI6IHsKICAgICJnaGNyLmlvIjogewogICAgICAidXNlcm5hbWUiOiAibWFud29sZnJhbWlvIiwKICAgICAgInBhc3N3b3JkIjogImdocF9UQU1ET3B4WTYxRFBmYkh4dlJ3VUJva1VlVXM4ekMwdGl4TTQiLAogICAgICAiZW1haWwiOiAibWlndWVsLm1hbnNvQGVkdS51YWguZXMiCiAgICB9CiAgfQp9Cgo=
EOM
EOF

