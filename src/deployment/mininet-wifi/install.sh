#!/bin/bash

########################
# Install MiniNet-Wifi #
########################

echo "[+] Installing Mininet-Wifi..."

# Install needed dependencies.
sudo apt-get update
sudo apt-get install -y git

# Clonamos el repositorio de Mininet
git clone https://github.com/intrig-unicamp/mininet-wifi

# Lanzamos el script de instalación (Openflow 1.3 - Ryu - Wireshark dissector)
sudo ./mininet-wifi/util/install.sh -3Wlfnv

# Para esta versión que intala vagrant de ubuntu el kernel que trae
# no lleva el modulo mac80211_hwsim por tanto hay que añadirlo
sudo apt-get install -y linux-modules-extra-5.4.0-113-generic