vagrant up
vagrant provision node-1 --provision-with=master
vagrant provision node-2 --provision-with=worker
vagrant provision node-3 --provision-with=worker
vagrant provision node-1 --provision-with=dashboard
vagrant provision node-1 --provision-with=metrics-server
vagrant provision node-1 --provision-with=kubevirt
vagrant provision node-1 --provision-with=project
