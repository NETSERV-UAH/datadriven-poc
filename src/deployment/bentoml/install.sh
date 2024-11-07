#!/bin/bash

###################
# Install BentoML #
###################

echo "[+] Installing BentoML..."

INSTALL='sudo DEBIAN_FRONTEND=noninteractive apt-get -y -q install'
BUILD_DIR=${HOME}

# Update.
sudo apt-get update

# Install BentoML dependencies.
$INSTALL python3-pip

# Install requirements for our BentoML service.
pip install -r requirements.txt

# Install the class
export PATH=$PATH:~/.local/bin
python3.8 train.py

# Start the service.
bentoml serve -p3001 .