#!/usr/bin/python
# -*- coding: utf-8 -*-

# Código de la branch orientada a trabajar con docker en un entorno basado en kubernetes
# Autor Javier Diaz-Fuentes

import os
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController
from mn_wifi.node import UserAP
from mn_wifi.node import OVSAP
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference

# Configuración por variables de entorno
RYU_CONTROLLER_IP = os.environ.get("RYU_CONTROLLER_IP", "FAIL_ADDR")
RYU_CONTROLLER_PORT = int(os.environ.get("RYU_CONTROLLER_PORT", "6633"))
INFLUXDB_IP = os.environ.get("INFLUXDB_IP", "FAIL_ADDR")
INFLUXDB_PORT = int(os.environ.get("INFLUXDB_PORT", "8086"))  # ← corregido: Influx suele usar 8086
INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN", "")

# Set sta1 and sta3 as outside and sta2 as inside
sensors_out_in = {"sta1": 0, "sta2": 1, "sta3": 0}

def scenario_basic():
    '''
    Definicion del escenario en mininet
    '''
# En esta implementacion de usa OSVAP por que si no las conexiones no se realizan correctamente entre el AP y el controlador implementado con ryu en un contenedor
    net = Mininet_wifi(accessPoint=OVSAP, ac_method='llf', link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    
    info('*** Add Controller (Ryu) ***\n')
    c0 = net.addController(
        name='c0',
        controller=RemoteController,
        ip=RYU_CONTROLLER_IP,
        protocol='tcp',
        port=RYU_CONTROLLER_PORT
    )

    info('*** Add UserAPs ***\n')
    # Se añade el parámetro dpid - Herencia del branch de javi
    ap1 = net.addAccessPoint('ap1', mac='00:00:00:00:00:01', ssid="ssid-ap1", position='50,50,0', dpid='1')
    ap2 = net.addAccessPoint('ap2', mac='00:00:00:00:00:02', ssid="ssid-ap2", position='70,50,0', dpid='2')
    ap3 = net.addAccessPoint('ap3', mac='00:00:00:00:00:03', ssid="ssid-ap3", position='90,50,0', dpid='3')

    info('*** Add Sensors ***\n')
    sta1 = net.addStation('sta1', mac='00:00:00:00:01:01', ip='10.0.0.1/8', position='50,30,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:01:02', ip='10.0.0.2/8', position='70,30,0')
    sta3 = net.addStation('sta3', mac='00:00:00:00:01:03', ip='10.0.0.3/8', position='90,30,0')

    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3.5)

    info("*** Configuring nodes\n")
    net.configureNodes()
    net.addNAT().configDefault()
    
    info('*** Add links ***\n')
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap2)
    net.addLink(sta3, ap3)
    net.addLink(ap1, ap2)
    net.addLink(ap2, ap3)

    info('\n*** Build it ***\n')
    net.build()

    info('*** Start the controller ***\n')
    for controller in net.controllers:
        controller.start()

    info('*** Set controllers ***\n')
    ap1.start([c0])
    ap2.start([c0])
    ap3.start([c0])

    info('*** Start the IIoT Sensors ***\n')
    for sta in net.stations:
        sensor_location = sensors_out_in[sta.name]
        influx_url = f"{INFLUXDB_IP}:{INFLUXDB_PORT}"
        sta.cmd(f'python3 iiot_sensor.py sensor-{sta.name} {sensor_location} {influx_url} {INFLUXDB_TOKEN} > {sta.name}.log & disown')

    info('*** RUN Mininet-Wifis CLI ***\n')
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    scenario_basic()
