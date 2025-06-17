#!/bin/bash
#!/bin/bash
set -e

# Variables
DASHBOARD_PORT=32000
FRONTEND_PORT=31080
CERT_DIR="/etc/nginx/cert"
DOMAIN_NAME="localhost"
NGINX_CONF="/etc/nginx/nginx.conf"

echo "[+] Instalando NGINX..."
sudo apt-get update
sudo apt-get install -y nginx openssl

echo "[+] Generando certificado autofirmado..."
sudo mkdir -p "$CERT_DIR"
sudo openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout "$CERT_DIR/nginx.key" \
  -out "$CERT_DIR/nginx.crt" \
  -subj "/CN=$DOMAIN_NAME"

echo "[+] Insertando configuración directamente en nginx.conf..."


sudo sed -i '/^http {/a \
    \n    ## BEGIN custom TLS reverse proxy ##\n\
    server {\n\
        listen 443 ssl;\n\
        server_name '"$DOMAIN_NAME"';\n\
\n\
        ssl_certificate     '"$CERT_DIR"'/nginx.crt;\n\
        ssl_certificate_key '"$CERT_DIR"'/nginx.key;\n\
\n\
        location /dashboard/ {\n\
            proxy_pass https://localhost:'"$DASHBOARD_PORT"'/;\n\
            proxy_ssl_verify off;\n\
            proxy_ssl_session_reuse on;\n\
            proxy_set_header Host $host;\n\
            proxy_set_header X-Real-IP $remote_addr;\n\
        }\n\
\n\
        location / {\n\
            proxy_pass http://localhost:'"$FRONTEND_PORT"'/;\n\
            proxy_set_header Host $host;\n\
            proxy_set_header X-Real-IP $remote_addr;\n\
        }\n\
    }\n\
    ## END custom TLS reverse proxy ##\n' "$NGINX_CONF"

echo "[+] Verificando configuración y reiniciando NGINX..."
sudo nginx -t
sudo systemctl reload nginx

echo "[+] NGINX instalado y configurado"
echo "Accede a https://$DOMAIN_NAME"



kubeadm init --pod-network-cidr=172.25.0.0/24 --token abcdef.0123456789abcdef --token-ttl 0

mkdir -p /home/vagrant/.kube
cp /etc/kubernetes/admin.conf /home/vagrant/.kube/config
chown vagrant:vagrant /home/vagrant/.kube/config

# Esperar al API server antes de aplicar Calico
until sudo -u vagrant kubectl get nodes &>/dev/null; do
  echo "Esperando al API server..."
  sleep 5
done

# Aplicar Calico como vagrant
sudo -u vagrant kubectl apply --validate=false -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml

