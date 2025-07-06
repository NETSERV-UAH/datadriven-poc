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
wget -q https://dl.grafana.com/oss/release/grafana_11.3.0_amd64.deb

# Install it.
sudo dpkg -i grafana_11.3.0_amd64.deb

# Add provisioning files
sudo mv /home/vagrant/grafana/grafana.ini /etc/grafana/grafana.ini
sudo mv /home/vagrant/grafana/influxdb_datasource.yaml /etc/grafana/provisioning/datasources/influxdb_datasource.yaml
sudo mv /home/vagrant/grafana/influxdb_dashboard.yaml /etc/grafana/provisioning/dashboards/default.yaml
sudo mv /home/vagrant/grafana/dashboard.json /etc/grafana/provisioning/dashboards/dashboard.json
sudo mv /home/vagrant/grafana/dashboard_6g.json /etc/grafana/provisioning/dashboards/dashboard_6g.json

# Start the service (it's stopped by default).
sudo systemctl start grafana-server

# And remove the downloaded package, we don't need it any more.
rm grafana_11.3.0_amd64.deb