#!/bin/bash

########################
# Install MiniNet-Wifi #
########################

echo "[+] Installing Mininet-Wifi..."

# Install needed dependencies.
sudo apt-get update
sudo apt-get install -y git

# Clonamos el repositorio de Mininet
# git clone https://github.com/intrig-unicamp/mininet-wifi

# Como me estaba dando problemas el último commit de mn_wifi hago un clone de mi repo, así lo aprovecho para P4 también
git clone https://github.com/JavierDiazF/mininet-wifi.git

# Lanzamos el script de instalación (Openflow 1.3 - Ryu - Wireshark dissector)
sudo ./mininet-wifi/util/install.sh -3Wlfnv

# Para esta versión que intala vagrant de ubuntu el kernel que trae
# no lleva el modulo mac80211_hwsim por tanto hay que añadirlo
sudo apt-get install -y linux-modules-extra-$(uname -r)