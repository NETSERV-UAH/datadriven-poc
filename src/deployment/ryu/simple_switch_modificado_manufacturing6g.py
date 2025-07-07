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
#import bentoml

# Parametros flows
IDLE_TIMEOUT_S = 30 #s
HARD_TIMEOUT_S = 30 #s
dropped_sensors = list()

# Configuración InfluxDB
INFLUXDB_URL = "http://192.168.56.12:8086"
INFLUXDB_TOKEN = "3hv3m8nphSlHRbVbKQ7o5Hrm0S4FhLDhu8WWGt9abXHQ26Ked4hGDSRqtZsYC-hc2gS9snCLjN5p9OnoYBeRYA=="
INFLUXDB_ORG = "UAH"
INFLUXDB_BUCKET = "iiot_data"


# InfluxDB data
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

# Bentoml data
BENTO_URL = "http://192.168.56.13:3001/predict"
BENTO_HEADERS = {"content-type": "application/json"}

mac_sensors = {"00:00:00:00:01:01": "sensor-sta1", "00:00:00:00:01:02": "sensor-sta2", "00:00:00:00:01:03": "sensor-sta3"}
influxdb_ip = "192.168.56.12"

class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)

        # Influxdb
        self.client_influxdb = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        self.influxdb_query_api = self.client_influxdb.query_api()

        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
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
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src

        dpid = format(datapath.id, "d").zfill(16)
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        """
        try:
            if self.mac_to_port[dpid][src] != in_port:
                self.logger.info(f"Se ha detectado en {dpid} un paquete con origen {src} entrando por un puerto que no es el que debía {in_port}. Posible roaming")
        except KeyError:
            pass
        """
        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]
        # Pongo a 0 los timeout para que por defecto sean para siempre
        idle_timeout = 0
        hard_timeout = 0

        if src in mac_sensors.keys() or dst in mac_sensors.keys(): # and eth.ethertype == ether_types.ETH_TYPE_IP and in_port == 1: El in_port == 1 es si quitamos el s1 para identificar si está directamente conectado o no
            # Entro en esta parte tanto para arp como ip

            # Al ser de los equipos que van a estar moviéndose los pongo un temporizador
            # Idle_tiemout and hard_timeout set porque son paquetes de influxdb
            idle_timeout = IDLE_TIMEOUT_S
            hard_timeout = HARD_TIMEOUT_S

            # Si es ARP lo pongo para que haga FLOOD. De esta forma siempre va a hacer descubrimiento ARP
            if eth.ethertype == ether_types.ETH_TYPE_ARP:
                out_port = ofproto.OFPP_FLOOD
                actions = [parser.OFPActionOutput(out_port)]
            elif eth.ethertype == ether_types.ETH_TYPE_IP:
                # Añadir una comparación de ip.dst (opcional)
                sensor_detected = mac_sensors[src] if src in mac_sensors.keys() else mac_sensors[dst]
                ip = pkt.get_protocol(ipv4.ipv4)
                self.logger.info(f"Sensor {sensor_detected} IIOT packet found in {ip.src} -> {ip.dst} in port {in_port}")
                # Si el origen es el sensor y el puerto 1 entonces es directo.
                # Si el destino es el sensor y el purto de salida también es 1 entonces es directo.
                # Al ser directo es cuando miro la base de datos. Si no es directo, entonces no valoro que dropee porque es un ap intermedio
                if (src in mac_sensors.keys() and in_port == 1) or (dst in mac_sensors.keys() and out_port == 1):
                    actions = self.intercept_stations_traffic(src, sensor_detected, actions)

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=eth.ethertype) # Añado el ethertype para que me diferencie los ARP de los IP
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
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
            # Query influxdb for sensors state (temperature mean)
            sensors_value = self.query_influxdb()
            if sensors_value:
                # Query bentoml for infer actions
                sensors_response = self.query_bentoml(sensors_value)
                try:
                    respuesta = sensors_response[mac_sensors[src]]['bentoml_response']
                    self.logger.info(f"Sensor {sensor_detected} con respuesta {respuesta}")
                    if sensors_response[mac_sensors[src]]["bentoml_response"] == 1: # Solo si está low
                        actions = []
                        dropped_sensors.append(src)
                        self.logger.info(f"{sensors_response[mac_sensors[src]]} packet dropped since {sensors_response[mac_sensors[src]]['bentoml_response']} received")
                except KeyError:
                    self.logger.error(f"Aún no hay datos de {sensor_detected}")
                self.logger.info(f"La acción es la siguiente {actions}")
            else:
                self.logger.info(f"Influxdb database still empty: {sensors_value}")
        else:
            self.logger.info(f"Sensor {src} estaba dropeado y no se ha consultado influxdb")
            dropped_sensors.remove(src)

        return actions

    def query_influxdb(self):
        """
            Function to query influxdb data
            Will return a dict with sensor_name:value
        """

        try:
            result = self.influxdb_query_api.query(DATA_QUERY)
        except Exception as e:
            self.logger.error(f"Error en la recepción de la query: {e}")
        sensors = dict()
        for table in result:
            for record in table:
                # Pruebo si existe el diccionariom, si no, lo creo
                try:
                    sensors[record.values.get("sensor_name")][record.get_field()] = record.get_value()
                # Si no existe la entrada del diccionario con el nombre del sensor del que se han recibido los registros, se crea
                except Exception as e:
                    sensors[record.values.get("sensor_name")] = dict()
                    sensors[record.values.get("sensor_name")]["name"] = record.values.get("sensor_name")
                    sensors[record.values.get("sensor_name")]["month"] = int(record.get_time().strftime('%m'))
                    # Una vez creado el diccionario ya puedo guardar el valor
                    sensors[record.values.get("sensor_name")][record.get_field()] = record.get_value()


        #self.logger.info(f"Sensors state: {sensors}")
        return sensors

    def query_bentoml(self, sensors_value):
        """
            Function to query bentoml and see if any action is required
        """

        for sensor_info in sensors_value.values():
            json_query = {
                "Operation_Mode": sensor_info['operation_mode'],
                "Temperature_C": sensor_info['temperature'],
                "Vibration_Hz": sensor_info['vibration'],
                "Power_Consumption_kW": sensor_info['power_consumption'],
                "Network_Latency_ms": sensor_info['network_latency'],
                "Packet_Loss_%": sensor_info['packet_loss'],
                "Quality_Control_Defect_Rate_%": sensor_info['quality_control_defect_rate'],
                "Production_Speed_units_per_hr": sensor_info['production_speed_units'],
                "Predictive_Maintenance_Score": sensor_info['predictive_maintenance_score'],
                "Error_Rate_%": sensor_info['error_rate'],
                "Month": sensor_info['month']
                }
            #self.logger.info(f"Sensor {sensor_info['name']}: {json_query}")

            response = requests.post(BENTO_URL, json=json_query, headers=BENTO_HEADERS)
            sensor_info['bentoml_response'] = int(response.json()[0])
            #self.logger.info(f"Response: {sensor_info['bentoml_response']}")

        return sensors_value

