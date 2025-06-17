#!/bin/bash

kubeadm join 192.168.100.11:6443 --token abcdef.0123456789abcdef --discovery-token-unsafe-skip-ca-verification
