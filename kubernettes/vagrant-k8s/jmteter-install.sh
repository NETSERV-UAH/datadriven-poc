#!/bin/bash

sudo apt update
sudo apt install default-jdk -y

# Variables
JMETER_VERSION="5.6.3"
JMETER_DIR="/opt/jmeter"
JMETER_URL="https://downloads.apache.org/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.tgz"
BASHRC="$HOME/.bashrc"

# Crear directorio de instalación
sudo mkdir -p "$JMETER_DIR"
cd /tmp

# Descargar y extraer JMeter
wget "$JMETER_URL" -O "apache-jmeter-${JMETER_VERSION}.tgz"
tar -xzf "apache-jmeter-${JMETER_VERSION}.tgz"

# Mover a /opt
sudo mv "apache-jmeter-${JMETER_VERSION}"/* "$JMETER_DIR"

# Agregar alias al .bashrc si no existen ya
if ! grep -q "alias jmeter=" "$BASHRC"; then
  echo "" >> "$BASHRC"
  echo "# Alias para Apache JMeter" >> "$BASHRC"
  echo "alias jmeter='$JMETER_DIR/bin/jmeter'" >> "$BASHRC"
  echo "alias jmeter-server='$JMETER_DIR/bin/jmeter-server'" >> "$BASHRC"
  echo "export PATH=\$PATH:$JMETER_DIR/bin" >> "$BASHRC"
  echo "JMeter alias agregado al .bashrc"
else
  echo "Alias jmeter ya existe en el .bashrc"
fi

# Aplicar cambios al entorno actual
source "$BASHRC"

# Mostrar versión
newgrp $USER
jmeter -v

