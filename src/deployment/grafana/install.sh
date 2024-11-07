#!/bin/bash

###################
# Install Grafana #
###################

echo "[+] Installing Grafana..."

INSTALL='sudo DEBIAN_FRONTEND=noninteractive apt-get -y -q install'
BUILD_DIR=${HOME}

# Update
sudo apt-get update

# Install Grafana dependencies
$INSTALL adduser libfontconfig1 musl

# Download the `*.deb` packaging Grafana.
wget https://dl.grafana.com/oss/release/grafana_11.3.0_amd64.deb

# Install it.
sudo dpkg -i grafana_11.3.0_amd64.deb

# Start the service (it's stopped by default).
sudo systemctl start grafana-server

# And remove the downloaded package, we don't need it any more.
rm grafana_11.3.0_amd64.deb