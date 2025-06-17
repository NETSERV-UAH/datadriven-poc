# Procesos previos

## Actualización del sistema

```bash
sudo apt update
sudo apt upgrade
```

Actualiza la base de datos de paquetes y luego instala las últimas versiones disponibles para todos los paquetes del sistema.

## Instalación de herramientas base

```bash
sudo apt install apt-transport-https ca-certificates curl software-properties-common
```

Instala herramientas necesarias para permitir el uso de HTTPS en los repositorios, certificados, y `curl` para descargas.

## Eliminación de instalaciones anteriores de Docker (si existen)

```bash
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
```

Elimina posibles instalaciones previas de Docker o herramientas relacionadas para evitar conflictos.

## Agregar la clave GPG oficial de Docker

```bash
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

Esto configura el repositorio de Docker con seguridad.

## Agregar el repositorio oficial de Docker a APT

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
```

## Instalar Docker y herramientas relacionadas

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## Permitir ejecutar Docker sin sudo

```bash
sudo groupadd docker
sudo usermod -aG docker $USER
```

## Reiniciar el sistema

```bash
sudo reboot
```

## Verificar instalación de Docker

```bash
docker run hello-world
```

## Instalar XRDP para escritorio remoto

```bash
sudo apt-get install xrdp
sudo systemctl enable xrdp
```

## Cambiar a XFCE como entorno de escritorio (más ligero)

```bash
sudo apt remove ubuntu-gnome-desktop --purge
sudo apt autoremove
sudo apt install xfce4 -y
sudo apt install lightdm -y
sudo dpkg-reconfigure lightdm
```

## Instalar Wireshark y configurar permisos

```bash
sudo apt-get install wireshark
sudo usermod -a -G wireshark $USER
```

## Descargar herramientas de análisis de red (GhostWire, PacketFlix)

```bash
mkdir ghostWire
cd ghostWire
wget https://github.com/siemens/cshargextcap/releases/download/v0.10.7/cshargextcap_0.10.7_linux_amd64.deb
chmod +x cshargextcap_0.10.7_linux_amd64.deb
sudo apt install ./cshargextcap_0.10.7_linux_amd64.deb

mkdir packetflix
cd packetflix
wget https://github.com/siemens/edgeshark/raw/main/deployments/wget/docker-compose.yaml
cd ..
mkdir ghostwire
cd ghostwire
wget https://github.com/siemens/ghostwire/raw/main/deployments/wget/docker-compose.yaml
```





