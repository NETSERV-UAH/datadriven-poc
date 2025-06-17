# Despliegue de kubernetets k8s + kubeadm con Vagrant
En este apartdo se explica como se realiza el despliegue de Kubernettes en su verison k8s con vagratn para automatizarlo. Se decide hacer uso de un sistema multinodo para poder hacer uso de las funciones de alta disponibilidad de Kubernettes (HA). Para ello se requiere disponer de tres nodos distintos inteconectados entre si como un kubernettes cluster.

### Requisitos:
Para poder realizar el despliegie en vagrant se hará uso dl virtualizador qemu de linux y de los addons de vagrant para el mismo. El objetivo es que la instalacion sea ligera pero la potencia no se vea mermada. Para ello se hará so de las siguientes librerias:
- qemu-kvm 
- libvirt-daemon-system 
- libvirt-clients
- bridge-utils
- vagrant
- vagrant-libvirt

#### Instalacion: 

```bash
 sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils vagrant vagrant-libvirt 
 ```
### Directorio del despliegue en vagrant
Para poder realizar el desplegue de los tres nodos necesarios para poder hacer uso de las funciones de HA de k8s se debe especificar en primer lugar el tipo de VMs que alojarán el clúster, así como el número de los mismos, el direccionamiento, el OS, etc.
Para ello se hace uso del ```vagrantfile```. Este para poder realizar las instalaciones necesarias en cada nodo debe dipsoner de una serie de scripts que permitan al los diferentes nodos instalar k8s, instalar kubeadm como orquestador y realizar los despliegues. 
- El nodo master además debe publicarse como tal
- Los nodos worker deben adscribirse al master
- Debe declpararse una red homogenea entre ellos (Calico)
 
```
Vagrantfile
scripts/
├── entry-node-1.sh   # master
├── entry-node-2.sh   # worker
└── entry-node-3.sh   # worker
```
### Aprovisionado de las VMs (vargrantfile):
En este fichero se definen:
- El direccionamiento de las tres maquinas
    - Red privada con el host, cuyas ips son las indicadas.
- La red ```vagrant-private``` donde se alojaran estas VMs.
- Se configuran las capacidades de cada una de ellas
    - Ram: 2GB
    - CPUs: 2 Cores
    - Disco: 64 GB (depende del proveedor de la box)

Finalmente accede al script de start de cada una de ellas empleando n.vm.provision

### Fichero de provisioning ```vagrantfile```:
``` bash
Vagrant.configure("2") do |config|
  nodes = [
    { name: "node-1", ip: "192.168.100.11" }, # Nodo master
    { name: "node-2", ip: "192.168.100.12" }, # Slave 1
    { name: "node-3", ip: "192.168.100.13" } # Slave 2
  ]
  config.vm.box = "generic/ubuntu2204" # S.O Ubuntu 22.04
  config.vm.box_check_update = false

  nodes.each do |node|
    config.vm.define node[:name] do |n|
      n.vm.hostname = node[:name]
      n.vm.network "private_network",
                   ip: node[:ip],
                   libvirt__network_name: "vagrant-private",
                   libvirt__dhcp_enabled: false
      n.vm.provider :libvirt do |v|
        v.memory = 2048
        v.cpus = 2
      end
      n.vm.provision "shell", path: "scripts/entry-#{node[:name]}.sh"
    end
  end
end
```

# Instalacion de k8s parte comun 
(https://kubernetes.io/docs/setup/) Para debian/ubuntu

### 1. Actualizamos los repositosrios 
``` bash
apt update && apt upgrade -y
apt install -y curl apt-transport-https ca-certificates gnupg lsb-release containerd
```
### 2. Actualizamos la configuracion de containerd (Se usa en vez de Docker)
``` bash
mkdir -p /etc/containerd
containerd config default | tee /etc/containerd/config.toml >/dev/null
systemctl restart containerd
systemctl enable containerd
```
### 3. Descativamos la swap (exigido por k8s)
``` bash
swapoff -a
sed -i '/ swap / s/^/#/' /etc/fstab
```
### 4. Cargamos overlay para usar sistemas de archivos en overlay y br_netfilter, que permite que los paquetes de red que pasan por bridges (puentes) sean visibles por las reglas de iptables.
``` bash
cat <<EOF | tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
```
### 5. Cargamos los módulos en el kernel

``` bash
modprobe overlay
modprobe br_netfilter
```

``` bash
cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
```

``` bash
sysctl --system
```

``` bash 
mkdir -p /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /" > /etc/apt/sources.list.d/kubernetes.list
``` 

``` bash 
apt update
apt install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl
```

# Parte del nodo master (node-1)

``` bash
kubeadm init --pod-network-cidr=192.168.0.0/16 --token abcdef.0123456789abcdef --token-ttl 0
```
``` bash
mkdir -p /home/vagrant/.kube
cp /etc/kubernetes/admin.conf /home/vagrant/.kube/config
chown vagrant:vagrant /home/vagrant/.kube/config
```

``` bash
kubectl --kubeconfig=/etc/kubernetes/admin.conf apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml
```




## Comandos útiles en vagrant

|Comando|Descripcion|
|---|---|
|Apagar todas las VMs| ``` vagrant halt ``` |
|Apagar una sola VM|  ```vagrant halt <nombre>``` |
|Destruir (eliminar) todo| ```vagrant destroy -f``` |
|Reiniciar todo|```vagrant reload```|
|Levantar de nuevo|```vagrant up```|
|Ver estado de las VMs|```vagrant status```|