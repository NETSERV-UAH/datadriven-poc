#!/bin/bash

########################
# Install InfluxDB     #
########################

echo "[+] Installing InfluxDB..."

# Install needed dependencies.
sudo apt-get update

# Ubuntu/Debian AMD64
curl -O https://dl.influxdata.com/influxdb/releases/influxdb2_2.7.5-1_amd64.deb
sudo dpkg -i influxdb2_2.7.5-1_amd64.deb

# Start the InfluxDB service
sudo service influxdb start

# Install influxdb_client library for python. 
# Required for integration of ryu with influxdb
pip install influxdb-client