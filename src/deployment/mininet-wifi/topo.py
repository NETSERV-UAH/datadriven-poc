#!/usr/bin/python
# -*- coding: utf-8 -*-

from mn_wifi.net import Mininet_wifi
from mininet.node import RemoteController
from mn_wifi.node import UserAP
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI


def scenario_basic():

    net = Mininet_wifi(accessPoint= UserAP)

    info("*** Creating nodes\n")
    
    info('*** Add Controller (Ryu) ***\n')
    c0 = net.addController( name = 'c0',
                            controller = RemoteController,
                            ip = '192.168.56.12',
                            protocol = 'tcp',
                            port = 6633)

    info('*** Add UserAPs ***\n')
    ap1 = net.addAccessPoint('ap1', mac='00:00:00:00:00:01',position='50,50,0')
    ap2 = net.addAccessPoint('ap2', mac='00:00:00:00:00:02',position='70,50,0')
    ap3 = net.addAccessPoint('ap3', mac='00:00:00:00:00:03',position='90,50,0')

    info('*** Add Sensors ***\n')
    sta1 = net.addStation('sta1', mac='00:00:00:00:01:01', ip='10.0.0.1/8', position='50,30,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:01:02', ip='10.0.0.2/8', position='70,30,0')
    sta3 = net.addStation('sta3', mac='00:00:00:00:01:03', ip='10.0.0.3/8', position='90,30,0')

    info("*** Configuring nodes\n")
    net.configureNodes()
    
    info('*** Add links ***\n')
    net.addLink(sta1, ap1)
    net.addLink(sta2, ap2)
    net.addLink(sta3, ap3)
    net.addLink(ap1,ap2)
    net.addLink(ap2,ap3)

    info("*** Plot the network ***\n")
    net.plotGraph(max_x=100, max_y=100)

    info('\n*** Build it ***\n')
    net.build()

    info('*** Start the controller ***\n')
    for controller in net.controllers:
        controller.start()

    info('*** Set controllers ***\n')
    net.get('ap1').start([c0])
    net.get('ap2').start([c0])
    net.get('ap3').start([c0])

    info('*** Start the IIoT Sensors ***\n')
    for sta in net.stations:
        sta.cmd(f'sudo python3 iiot_sensor.py {sta.name}')

    info('*** RUN Mininet-Wifis CLI ***\n')
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    scenario_basic()