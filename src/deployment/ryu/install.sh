#!/bin/bash

###################
# Install Ryu #
###################

echo "[+] Installing Ryu..."

INSTALL='sudo DEBIAN_FRONTEND=noninteractive apt-get -y -q install'
BUILD_DIR=${HOME}

# Update
sudo apt-get update

# Install Ryu dependencies
$INSTALL autoconf automake git g++ libtool python3 make gcc python3-pip python3-dev libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev

# Fetch RYU
cd $BUILD_DIR/
git clone https://github.com/davidcawork/ryu.git ryu
cd ryu

# Install ryu
sudo pip3 install -r tools/pip-requires -r tools/optional-requires \
    -r tools/test-requires
sudo python3 setup.py install