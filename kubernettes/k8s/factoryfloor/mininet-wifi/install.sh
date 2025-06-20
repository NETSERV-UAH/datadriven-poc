#!/bin/bash

echo "[+] Installing Mininet-Wifi..."

sudo apt-get update
sudo apt-get install -y git

git clone https://github.com/intrig-unicamp/mininet-wifi

sudo ./mininet-wifi/util/install.sh -3Wlfnv

sudo apt-get install -y linux-modules-extra-$(uname -r)
