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
sudo pip3 install webob>=1.2 eventlet==0.33.3 msgpack>=0.4.0 netaddr oslo.config>=2.5.0 ovs>=2.6.0 packaging==20.9 routes tinyrpc==1.0.4