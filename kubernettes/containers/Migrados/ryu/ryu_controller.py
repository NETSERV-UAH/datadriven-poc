#!/usr/bin/python
# -*- coding: utf-8 -*-
# Ryu Controller - Kubernetes-ready version with dynamic sensor mapping
# Autor: Javier Diaz-Fuentes

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
import re
from urllib.parse import urlparse, urlunparse

# Utilidad para resolver DNS con getent (Kubernetes)
def resolve_dns_with_os(url):
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port
    try:
        stream = os.popen(f"getent hosts {hostname}")
        output = stream.read()
        ip = output.split()[0]
        new_netloc = f"{ip}:{port}" if port else ip
        return urlunparse((parsed.scheme, new_netloc, parsed.path, '', '', ''))
    except Exception:
        return url

# Timeout de flows
IDLE_TIMEOUT_S = 30
HARD_TIMEOUT_S = 30
dropped_sensors = list()

# Configuración por entorno
INFLUXDB_URL = resolve_dns_with_os(os.getenv("INFLUXDB_URL", "http://192.168.56.12:8086"))
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "...")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "UAH")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "iiot_data")

BENTO_URL = resolve_dns_with_os(os.getenv("BENTO_URL", "http://192.168.56.13:3001/predict"))
BENTO_HEADERS = {"content-type": "application/json"}

# Consulta a InfluxDB
DATA_RANGE = "-1m"
DATA_WINDOW = "1m"
DATA_MEASUREMENT = "tempSensors"
DATA_FUNCTION = "mean"

DATA_QUERY = f'''
from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: {DATA_RANGE})
    |> filter(fn: (r) => r["_measurement"] == "{DATA_MEASUREMENT}")
    |> filter(fn: (r) => r["_field"] == "error_rate" or r["_field"] == "network_latency" or r["_field"] == "operation_mode" or r["_field"] == "packet_loss" or r["_field"] == "power_consumption" or r["_field"] == "predictive_maintenance_score" or r["_field"] == "production_speed_units" or r["_field"] == "quality_control_defect_rate" or r["_field"] == "temperature" or r["_field"] == "vibration")
    |> aggregateWindow(every: {DATA_WINDOW}, fn: {DATA_FUNCTION}, createEmpty: false)
    |> yield(name: "{DATA_FUNCTION}")
'''

mac_sensor_pattern = re.compile(r"00:00:00:00:(\d\d):(\d\d)")

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.client_influxdb = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        self.influxdb_query_api = self.client_influxdb.query_api()
        self.mac_to_port = {}
        self.mac_sensors = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None, idle_timeout=0, hard_timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, buffer_id=buffer_id or ofproto.OFP_NO_BUFFER,
            priority=priority, match=match, instructions=inst,
            idle_timeout=idle_timeout, hard_timeout=hard_timeout
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dst, src = eth.dst, eth.src
        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # Registrar MAC como sensor si aplica
        for mac in (src, dst):
            if mac not in self.mac_sensors:
                match = mac_sensor_pattern.match(mac)
                if match:
                    ap_id, sta_id = int(match.group(1), 16), int(match.group(2), 16)
                    self.mac_sensors[mac] = f"sensor-sta_{ap_id}_{sta_id}"
                    self.logger.info(f"Registrado sensor dinámico: {mac} -> {self.mac_sensors[mac]}")

        out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)
        actions = [parser.OFPActionOutput(out_port)]
        idle_timeout = hard_timeout = 0

        if src in self.mac_sensors or dst in self.mac_sensors:
            idle_timeout = IDLE_TIMEOUT_S
            hard_timeout = HARD_TIMEOUT_S

            if eth.ethertype == ether_types.ETH_TYPE_ARP:
                out_port = ofproto.OFPP_FLOOD
                actions = [parser.OFPActionOutput(out_port)]
            elif eth.ethertype == ether_types.ETH_TYPE_IP:
                ip = pkt.get_protocol(ipv4.ipv4)
                sensor_detected = self.mac_sensors.get(src) or self.mac_sensors.get(dst)
                self.logger.info(f"Sensor {sensor_detected} IIOT packet {ip.src} -> {ip.dst}")
                if (src in self.mac_sensors and in_port == 1) or (dst in self.mac_sensors and out_port == 1):
                    actions = self.intercept_stations_traffic(src, sensor_detected, actions)

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=eth.ethertype)
            self.add_flow(datapath, 1, match, actions, msg.buffer_id, idle_timeout, hard_timeout)

        out = parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id,
            in_port=in_port, actions=actions,
            data=None if msg.buffer_id != ofproto.OFP_NO_BUFFER else msg.data
        )
        datapath.send_msg(out)

    def intercept_stations_traffic(self, src, sensor_detected, actions):
        self.logger.info(f"Sensores droppeados: {dropped_sensors}")
        if src not in dropped_sensors:
            sensors_value = self.query_influxdb()
            if sensors_value:
                sensors_response = self.query_bentoml(sensors_value)
                try:
                    response = sensors_response[self.mac_sensors[src]]['bentoml_response']
                    if response == 1:
                        actions = []
                        dropped_sensors.append(src)
                        self.logger.info(f"{sensor_detected} DROPEADO por bentoml_response = 1")
                except KeyError:
                    self.logger.warning(f"No hay respuesta aún para {sensor_detected}")
            else:
                self.logger.info("InfluxDB aún sin datos")
        else:
            self.logger.info(f"{sensor_detected} ya estaba dropeado. Permitido de nuevo.")
            dropped_sensors.remove(src)
        return actions

    def query_influxdb(self):
        try:
            result = self.influxdb_query_api.query(DATA_QUERY)
        except Exception as e:
            self.logger.error(f"Error en la query InfluxDB: {e}")
            return None

        sensors = {}
        for table in result:
            for record in table:
                name = record.values.get("sensor_name")
                if name not in sensors:
                    sensors[name] = {
                        "name": name,
                        "month": int(record.get_time().strftime('%m'))
                    }
                sensors[name][record.get_field()] = record.get_value()
        return sensors

    def query_bentoml(self, sensors_value):
        for sensor in sensors_value.values():
            json_query = {
                "input_data": {
                    "Operation_Mode": sensor['operation_mode'],
                    "Temperature_C": sensor['temperature'],
                    "Vibration_Hz": sensor['vibration'],
                    "Power_Consumption_kW": sensor['power_consumption'],
                    "Network_Latency_ms": sensor['network_latency'],
                    "Packet_Loss_%": sensor['packet_loss'],
                    "Quality_Control_Defect_Rate_%": sensor['quality_control_defect_rate'],
                    "Production_Speed_units_per_hr": sensor['production_speed_units'],
                    "Predictive_Maintenance_Score": sensor['predictive_maintenance_score'],
                    "Error_Rate_%": sensor['error_rate'],
                    "Month": sensor['month']
                }
            }
            try:
                resp = requests.post(BENTO_URL, json=json_query, headers=BENTO_HEADERS)
                sensor['bentoml_response'] = int(resp.json()[0])
            except Exception as e:
                self.logger.error(f"Error al consultar BentoML para {sensor['name']}: {e}")
        return sensors_value

