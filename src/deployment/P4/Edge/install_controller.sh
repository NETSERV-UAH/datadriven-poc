#!/bin/bash

###################################
# Install P4 for RemoteController #
###################################

# P4runtime_lib installation from p4lang/tutorials
git clone https://github.com/p4lang/tutorials
cp -r tutorials/utils/* p4utils/
# La idea es que se elimine todo pues solo necesito lo que está en p4utils
# rm -rf tutorials

# Bmv2 installation
#. /etc/os-release
#echo "deb http://download.opensuse.org/repositories/home:/p4lang/xUbuntu_${VERSION_ID}/ /" | sudo tee /etc/apt/sources.list.d/home:p4lang.list
#curl -fsSL "https://download.opensuse.org/repositories/home:p4lang/xUbuntu_${VERSION_ID}/Release.key" | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/home_p4lang.gpg > /dev/null
#sudo apt update
#sudo apt install p4lang-bmv2 -y

# P4C installation
source /etc/lsb-release
echo "deb http://download.opensuse.org/repositories/home:/p4lang/xUbuntu_${DISTRIB_RELEASE}/ /" | sudo tee /etc/apt/sources.list.d/home:p4lang.list
curl -fsSL https://download.opensuse.org/repositories/home:p4lang/xUbuntu_${DISTRIB_RELEASE}/Release.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/home_p4lang.gpg > /dev/null
sudo apt-get update
sudo apt install p4lang-p4c -y

# Add this line to avoid allow_unknown_field error 
pip install --upgrade protobuf==3.20.3