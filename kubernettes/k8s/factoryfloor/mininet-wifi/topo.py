#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController
from mn_wifi.node import UserAP
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference

sensors_out_in = {"sta1": 0, "sta2": 1, "sta3": 0}

def scenario_basic():
    RYU_CONTROLLER_IP = os.environ.get("RYU_CONTROLLER_IP", "192.168.56.12")
    RYU_CONTROLLER_PORT = int(os.environ.get("RYU_CONTROLLER_PORT", "6633"))
    INFLUXDB_IP = os.environ.get("INFLUXDB_IP", "192.168.56.12")
    INFLUXDB_PORT = int(os.environ.get("INFLUXDB_PORT", "6633"))
    INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN", "")

    net = Mininet_wifi(accessPoint=UserAP, ac_method='llf', link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")

    info('*** Add Controller (Ryu) ***\n')
    c0 = net.addController(name='c0', controller=RemoteController, ip=RYU_CONTROLLER_IP, protocol='tcp', port=RYU_CONTROLLER_PORT)

    info('*** Add UserAPs ***\n')
    ap1 = net.addAccessPoint('ap1', mac='00:00:00:00:00:01', ssid="ssid-ap1", position='50,50,0')
    
    info('*** Add Sensors ***\n')
    sta1 = net.addStation('sta1', mac='00:00:00:00:01:01', ip='10.0.0.1/8', position='50,30,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:01:02', ip='10.0.0.2/8', position='70,30,0')
    sta3 = net.addStation('sta3', mac='00:00:00:00:01:03', ip='10.0.0.3/8', position='90,30,0')

    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3.5)

    info("*** Configuring nodes\n")
    net.configureNodes()

    info('*** Add NAT ***\n')
    nat0 = net.addNAT('nat0')
    nat0.configDefault()

    info('*** Add links ***\n')
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap1)
    net.addLink(sta3, ap1)

    info("*** Plot the network ***\n")
    net.plotGraph(max_x=100, max_y=100)

    info('\n*** Build it ***\n')
    net.build()

    info('*** Setup bridge in ap1 ***\n')
    ap1.cmd('ovs-vsctl add-br br-ap1')
    ap1.cmd('ovs-vsctl add-port br-ap1 ap1-wlan1')
    ap1.cmd('ovs-vsctl add-port br-ap1 ap1-eth2')

    info('*** Start the controller ***\n')
    for controller in net.controllers:
        controller.start()

    info('*** Set controllers for APs ***\n')
    ap1.start([c0])

    info('*** Start the IIoT Sensors ***\n')
    for sta in net.stations:
        sensor_location = sensors_out_in[sta.name]
        sta.cmd('sudo ip route add default via 10.0.0.4')
        sta.cmd(
            f'python3 iiot_sensor.py sensor-{sta.name} {sensor_location} http://{INFLUXDB_IP}:{INFLUXDB_PORT}/api/v2 {INFLUXDB_TOKEN} > {sta.name}.log & disown'
        )

    info('*** RUN Mininet-Wifi CLI ***\n')
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    scenario_basic()
