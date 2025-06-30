# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# DOCKER optimized version designed for running in kubernettes eviroment
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import tcp, ipv4
from influxdb_client import InfluxDBClient
import datetime
import json
import requests
import os
from urllib.parse import urlparse, urlunparse

def resolve_dns_with_os(url):
'''
Esta funcion resuelve los nombres de dominio por DNS. hace uso de os.system para ejecutar comandos de tipo getent en la terminal ya que si no no resuelve a coreDNS de kubernettes. en caso de que se resolviese este problema se podría hacer uso de gethostbyname de la liberia socket

Se le proporcionan URLs completas en formato string y las devuelve sustituyendo eñ nomre de domino excusivamente
'''
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port
    try:
        stream = os.popen(f"getent hosts {hostname}")
        output = stream.read()
        ip = output.split()[0]
        new_netloc = f"{ip}:{port}" if port else ip
        return urlunparse((parsed.scheme, new_netloc, parsed.path, '', '', ''))
    except Exception as e:
        return url  # fallback to original URL if error

# Parameters for flows
IDLE_TIMEOUT_S = 30
HARD_TIMEOUT_S = 30
dropped_sensors = list()

# Config from environment variables with fallback defaults
INFLUXDB_URL = resolve_dns_with_os(os.getenv("INFLUXDB_URL", "http://influxdb.datadriven.svc.cluster.local:8086"))
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "3hv3m8nphSlHRbVbKQ7o5Hrm0S4FhLDhu8WWGt9abXHQ26Ked4hGDSRqtZsYC-hc2gS9snCLjN5p9OnoYBeRYA==")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "UAH")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "iiot_data")

BENTO_URL = resolve_dns_with_os(os.getenv("BENTO_URL", "http://bentoml.datadriven.svc.cluster.local:3001/predict"))
BENTO_HEADERS = {"content-type": "application/json"}

DATA_RANGE = "-1m"
DATA_WINDOW = "1m"
DATA_MEASUREMENT = "tempSensors"
DATA_FIELD = "temp"
DATA_FUNCTION = "mean"

DATA_QUERY = f'''
from(bucket: "{INFLUXDB_BUCKET}") 
    |> range(start: {DATA_RANGE}) 
    |> filter(fn: (r) => r["_measurement"] == "{DATA_MEASUREMENT}") 
    |> filter(fn: (r) => r["_field"] == "{DATA_FIELD}") 
    |> aggregateWindow(every: {DATA_WINDOW}, fn: {DATA_FUNCTION}, createEmpty: false)
    |> yield(name: "{DATA_FUNCTION}")
    '''

mac_sensors = {
    "00:00:00:00:01:01": "sensor-sta1",
    "00:00:00:00:01:02": "sensor-sta2",
    "00:00:00:00:01:03": "sensor-sta3"
}

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.client_influxdb = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        self.influxdb_query_api = self.client_influxdb.query_api()
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id, 
                                    idle_timeout=idle_timeout, hard_timeout=hard_timeout,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    idle_timeout=idle_timeout, hard_timeout=hard_timeout,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        try:
            if self.mac_to_port[dpid][src] != in_port:
                self.logger.info(f"Roaming detectado en {dpid}: paquete de {src} en puerto {in_port}")
        except KeyError:
            pass

        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD
        
        actions = [parser.OFPActionOutput(out_port)]
        idle_timeout = 0
        hard_timeout = 0

        if src in mac_sensors or dst in mac_sensors:
            idle_timeout = IDLE_TIMEOUT_S
            hard_timeout = HARD_TIMEOUT_S

            if eth.ethertype == ether_types.ETH_TYPE_ARP:
                out_port = ofproto.OFPP_FLOOD
                actions = [parser.OFPActionOutput(out_port)]
            elif eth.ethertype == ether_types.ETH_TYPE_IP:
                ip = pkt.get_protocol(ipv4.ipv4)
                sensor_detected = mac_sensors.get(src) or mac_sensors.get(dst)
                self.logger.info(f"Sensor {sensor_detected} IIOT packet: {ip.src} -> {ip.dst} in port {in_port}")
                actions = self.intercept_stations_traffic(src, sensor_detected, actions)

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=eth.ethertype)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id, idle_timeout=idle_timeout, hard_timeout=hard_timeout)
                return
            else:
                self.add_flow(datapath, 1, match, actions, None, idle_timeout=idle_timeout, hard_timeout=hard_timeout)

        data = None  
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def intercept_stations_traffic(self, src, sensor_detected, actions):
        self.logger.info(f"Sensores droppeados: {dropped_sensors}")
        if src not in dropped_sensors:
            sensors_value = self.query_influxdb()
            if sensors_value:
                sensors_response = self.query_bentoml(sensors_value)
                try:
                    respuesta = sensors_response[mac_sensors[src]]['bentoml_response']
                    self.logger.info(f"Sensor {sensor_detected} con respuesta {respuesta}")
                    if respuesta == 1:
                        actions = []
                        dropped_sensors.append(src)
                        self.logger.info(f"Sensor {sensor_detected} dropeado según bentoml_response")
                except KeyError:
                    self.logger.error(f"No hay datos de {sensor_detected}")
            else:
                self.logger.info(f"Influxdb database aún vacía")
        else:
            self.logger.info(f"Sensor {src} ya estaba dropeado, no consultando influxdb")
            dropped_sensors.remove(src)

        return actions

    def query_influxdb(self):
    '''
    Funcion para hacer llamadas a la BBDD de influx alojada en la URL INFLUXDB_URL
    debe tener el token funcionando y estar correctamente configurada    
    '''
        try:
            result = self.influxdb_query_api.query(DATA_QUERY)
        except Exception as e:
            self.logger.error(f"Error en la consulta a InfluxDB: {e}")
            return None

        sensors = {record.values.get("sensor_name"): {
            "name": record.values.get('sensor_name'),
            "temp": record.get_value(),
            "month": int(record.get_time().strftime('%m')),
            "location": record.values.get('location')}
            for table in result for record in table}
        return sensors

    def query_bentoml(self, sensors_value):
        for sensor_info in sensors_value.values():
            json_query = {
                "input_data": {
                    "temp": sensor_info['temp'],
                    "out/in_encoded": sensor_info['location'],
                    "Month": sensor_info['month']
                }
            }
            response = requests.post(BENTO_URL, json=json_query, headers=BENTO_HEADERS)
            sensor_info['bentoml_response'] = int(response.json()[0])
        return sensors_value

