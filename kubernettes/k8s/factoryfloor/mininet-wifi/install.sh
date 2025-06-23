#!/bin/bash

echo "[+] Installing Mininet-Wifi..."

apt-get update
apt-get install -y git

git clone https://github.com/intrig-unicamp/mininet-wifi

./mininet-wifi/util/install.sh -3Wlfnv

source /etc/profile.d/env.sh

cd /mininet-wifi/

python3 ./setup.py install

cd /

apt-get install -y linux-modules-extra-$(uname -r)
