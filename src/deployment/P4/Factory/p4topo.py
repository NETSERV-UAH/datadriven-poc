#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

from mn_wifi.net import Mininet_wifi
#from mn_wifi.node import UserAP, OVSAP
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.bmv2 import P4AP, P4Host
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 
        './p4runtime/'))
from p4runtime_ap import P4RuntimeAP

# Set sta1 and sta3 as outside and sta2 as inside
sensors_out_in = {"sta1": 0, "sta2": 1, "sta3": 0}

# Required for P4 Runtime
bmv2_exe = 'simple_switch_grpc'

def configureP4AP(**switch_args):
    """ Helper class that is called by mininet to initialize
        the virtual P4 switches. The purpose is to ensure each
        switch's thrift server is using a unique port.
    """
    if "sw_path" in switch_args and 'grpc' in switch_args['sw_path']:
        # If grpc appears in the BMv2 switch target, we assume will start P4Runtime
        class ConfiguredP4RuntimeAP(P4RuntimeAP):
            def __init__(self, *opts, **kwargs):
                kwargs.update(switch_args)
                P4RuntimeAP.__init__(self, *opts, **kwargs)

            def describe(self):
                print("%s -> gRPC port: %d" % (self.name, self.grpc_port))

        return ConfiguredP4RuntimeAP
    else:
        class ConfiguredP4AP(P4AP):
            next_thrift_port = 9090
            def __init__(self, *opts, **kwargs):
                global next_thrift_port
                kwargs.update(switch_args)
                kwargs['thrift_port'] = ConfiguredP4AP.next_thrift_port
                ConfiguredP4AP.next_thrift_port += 1
                P4AP.__init__(self, *opts, **kwargs)

            def describe(self):
                print("%s -> Thrift port: %d" % (self.name, self.thrift_port))

        return ConfiguredP4AP


def scenario_basic():
    # Quito accessPoint= UserAP, para que no haya que poner cls=OVSAP en cada addAccessPoint
    # ac_method='llf', link=wmediumd, wmediumd_mode=interference para en teoría que se permita la reasociacion a otro AP. AUnque no funciona
    net = Mininet_wifi()

    info("*** Creating nodes\n")

    info("*** Creating P4Runtime Switches")
    apclass = configureP4AP(sw_path=bmv2_exe, json_path='basic.json', log_console=True)
    
    info('*** Add P4APs ***\n')
    ap1 = net.addAccessPoint('ap1', cls=apclass, netcfg=True, ip='10.0.1.1', mac='00:00:00:00:01:01', json='basic_json', grpc_port=50051, device_id=1, ssid="ssid-ap1", position='50,50,0')
    ap2 = net.addAccessPoint('ap2', cls=apclass, netcfg=True, ip='10.0.1.2', mac='00:00:00:00:01:02', json='basic_json', grpc_port=50052, device_id=2, ssid="ssid-ap2", position='70,50,0')
    ap3 = net.addAccessPoint('ap3', cls=apclass, netcfg=True, ip='10.0.1.3', mac='00:00:00:00:01:03', json='basic_json', grpc_port=50053, device_id=3, ssid="ssid-ap3", position='90,50,0')

    info('*** Add Sensors ***\n')
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:01', ip='10.0.0.1/8', position='50,30,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:02', ip='10.0.0.2/8', position='70,30,0')
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:03', ip='10.0.0.3/8', position='90,30,0')

    info("*** Configuring nodes\n")
    net.configureNodes()
    net.addNAT(mac='00:00:00:00:00:04').configDefault()
    
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

    info('*** Set controllers ***\n')
    net.start()
    #net.get('ap1').start()
    #net.get('ap2').start()
    #net.get('ap3').start()

    info('*** Start the IIoT Sensors ***\n')
    for sta in net.stations:
        sensor_location = sensors_out_in[sta.name]
        sta.cmd('sudo ip route add default via 10.0.0.4')
        #sta.cmd(f'python3 iiot_sensor.py sensor-{sta.name} {sensor_location} > {sta.name}.log & disown')

    info('*** RUN Mininet-Wifis CLI ***\n')
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    scenario_basic()
