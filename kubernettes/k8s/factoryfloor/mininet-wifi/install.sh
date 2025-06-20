#!/bin/bash

echo "[+] Installing Mininet-Wifi..."

sudo apt-get update
sudo apt-get install -y git

git clone https://github.com/intrig-unicamp/mininet-wifi

sudo ./mininet-wifi/util/install.sh -3Wlfnv

source /etc/profile.d/env.sh

sudo python3 ./mininet-wifi/setup.py install

sudo apt-get install -y linux-modules-extra-$(uname -r)
