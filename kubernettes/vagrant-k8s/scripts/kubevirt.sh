#!/bin/bash

sudo -u vagrant -i bash <<EOF
export KUBEVIRT_VERSION=\$(curl -s https://api.github.com/repos/kubevirt/kubevirt/releases/latest | grep tag_name | cut -d '"' -f 4)
kubectl create -f https://github.com/kubevirt/kubevirt/releases/download/\${KUBEVIRT_VERSION}/kubevirt-operator.yaml
kubectl create -f https://github.com/kubevirt/kubevirt/releases/download/\${KUBEVIRT_VERSION}/kubevirt-cr.yaml
EOF

