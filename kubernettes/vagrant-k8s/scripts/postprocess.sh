#!/bin/bash

sudo -u vagrant -i bash <<'EOF'

###################
## factory-floor ##
###################

## mininet-vm ##
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/factoryfloor/ff-vm-disk.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/factoryfloor/ff-vm.yaml
kubectl apply -f https://raw.githubusercontent.com/NETSERV-UAH/datadriven-poc/refs/heads/k8s-deploy-datadriven/kubernettes/k8s/factoryfloor/ff-vm-ssh-service.yaml

EOF
