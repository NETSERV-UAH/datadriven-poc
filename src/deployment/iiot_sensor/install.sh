#!/bin/bash

########################
# Install IIoT_Sensor  #
########################

echo "[+] Installing IIoT_Sensor..."

# Install needed dependencies.
sudo apt-get update

# Install numpy
pip3 install numpy