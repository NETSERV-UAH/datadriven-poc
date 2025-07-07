#!/usr/bin/python
# -*- coding: utf-8 -*-

# Código de la branch orientada a trabajar con docker en un entorno basado en kubernetes
# Autor Javier Diaz-Fuentes

import os
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController
from mn_wifi.node import OVSAP
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference

# Variables de entorno
RYU_CONTROLLER_IP = os.environ.get("RYU_CONTROLLER_IP", "FAIL_ADDR")
RYU_CONTROLLER_PORT = int(os.environ.get("RYU_CONTROLLER_PORT", "6633"))
INFLUXDB_IP = os.environ.get("INFLUXDB_IP", "FAIL_ADDR")
INFLUXDB_PORT = int(os.environ.get("INFLUXDB_PORT", "8086"))
INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN", "")
STAS_PER_AP = int(os.environ.get("STAS_PER_AP", "1"))  # Puede ser 0

# Nombres de APs definidos estáticamente
AP_NAMES = ["ap1", "ap2", "ap3"]

def scenario_basic():
    '''
    Definición del escenario en Mininet-WiFi
    '''
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

    info('*** Add Access Points ***\n')
    aps = {}
    for i, ap_name in enumerate(AP_NAMES, start=1):
        aps[ap_name] = net.addAccessPoint(
            ap_name,
            mac=f'00:00:00:00:00:0{i}',
            ssid=f"ssid-{ap_name}",
            dpid=str(i)
        )

    info('*** Add Stations and Links ***\n')
    sensors_out_in = {}
    sta_counter = 1

    if STAS_PER_AP > 0:
        for ap_idx, ap_name in enumerate(AP_NAMES, start=1):
            ap = aps[ap_name]
            for sta_idx in range(1, STAS_PER_AP + 1):
                sta_name = f'sta_{ap_idx}_{sta_idx}'
                sta_ip = f'10.0.0.{sta_counter}/8'
                sta_mac = f'00:00:00:00:{ap_idx:02x}:{sta_idx:02x}'
                station = net.addStation(sta_name, ip=sta_ip, mac=sta_mac)
                net.addLink(station, ap)

                # Alternar 0 y 1 para sensor_location
                sensors_out_in[sta_name] = (sta_counter + 1) % 2
                sta_counter += 1

    info("*** Configuring nodes\n")
    net.configureNodes()
    net.addNAT().configDefault()

    info('\n*** Build it ***\n')
    net.build()

    info('*** Start the controller ***\n')
    for controller in net.controllers:
        controller.start()

    info('*** Start APs with controller ***\n')
    for ap in aps.values():
        ap.start([c0])

    if STAS_PER_AP > 0:
        info('*** Start the IIoT Sensors ***\n')
        for sta in net.stations:
            sensor_location = sensors_out_in[sta.name]
            influx_url = f"{INFLUXDB_IP}:{INFLUXDB_PORT}"
            operation_mode = sta_counter % 3
            sta.cmd(f'python3 sensor_script.py sensor-{sta.name} {operation_mode} {influx_url} {INFLUXDB_TOKEN} > {sta.name}.log & disown')
    else:
        info('*** No stations to start sensors on (STAS_PER_AP=0) ***\n')

    info('*** RUN Mininet-WiFi CLI ***\n')
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    scenario_basic()

