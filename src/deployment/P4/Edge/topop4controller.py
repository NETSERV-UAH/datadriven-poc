import os
import sys
from time import sleep

from influxdb_client import InfluxDBClient
import requests

import ipaddress

sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 
        '../p4utils/'))
import p4runtime_lib.bmv2
import p4runtime_lib.helper
#from p4runtime_lib.error_utils import printGrpcError
#from p4runtime_lib.switch import ShutdownAllSwitchConnections

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

# Mininet sensors and AP data
mn_sensors = {"sensor-sta1": "10.0.0.1", "sensor-sta2": "10.0.0.2", "sensor-sta3": "10.0.0.3"}
mn_aps = ["ap1", "ap2", "ap3"]
mn_base_ip = "192.168.56.11"
mn_baseport = 50050

influxdb_ip = "192.168.56.12"

class Sensors_state():
    """
        Class that manages the querys to Influxdb and Bentoml
    """

    def __init__(self, *args, **kwargs):
        self.client_influxdb = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        self.influxdb_query_api = self.client_influxdb.query_api()

    def query_influxdb(self):
        """
            Function to query influxdb data
            Will return a dict with sensor_name:value
        """

        try:
            result = self.influxdb_query_api.query(DATA_QUERY)
        except Exception as e:
            print(f"Error en la recepción de la query: {e}")
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

        #print(f"Sensors state: {sensors}")
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
            #print(f"Sensor {sensor_info['name']}: {json_query}")

            response = requests.post(BENTO_URL, json=json_query, headers=BENTO_HEADERS)
            sensor_info['bentoml_response'] = int(response.json()[0])
            #print(f"Response: {sensor_info['bentoml_response']}")

        return sensors_value
#############################################################################################

def write_ipv4_forward_rule(p4info_helper, ingres_sw, dst_ip_addr, mask):
    """
        Writes the ipv4 forward rules in the aps.
        Since srcAddr and input_port are ternary they are not required
    """
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.ipv4_lpm",
        match_fields={
            "hdr.ipv4.dstAddr": (dst_ip_addr, mask),
        },
        priority=1,
        action_name="MyIngress.ipv4_forward",
        action_params={
        })
    ingres_sw.WriteTableEntry(table_entry)
    print(f"Forward rule inserted on {ingres_sw.name}")

def write_ipv4_drop_rule(p4info_helper, ingres_sw, dst_ip_addr, src_ip_addr):
    """
        Writes the ipv4 drop rules in the aps.
        srcAddr and ingress_port required to drop only srcAddr packets if is directly connected to ap.
        Priority greater than ipv4_forward to perform drop over forward.
    """
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.ipv4_lpm",
        match_fields={
            "hdr.ipv4.dstAddr": (dst_ip_addr, 32),
            "hdr.ipv4.srcAddr": (src_ip_addr, 0xFFFFFFFF),
            "standard_metadata.ingress_port": (1, 0x1FF)
        },
        priority=10,
        action_name="MyIngress.drop",
        action_params={
        })
    ingres_sw.WriteTableEntry(table_entry)
    print(f"Drop {src_ip_addr} rule inserted on {ingres_sw.name}")

def delete_ipv4_drop_rule(p4info_helper, ingres_sw, dst_ip_addr, src_ip_addr):
    """
        Purges the ipv4 drop rules in the aps.
        srcAddr and ingress_port required to match the previous written rule. 
    """
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.ipv4_lpm",
        match_fields={
            "hdr.ipv4.dstAddr": (dst_ip_addr, 32),
            "hdr.ipv4.srcAddr": (src_ip_addr, 0xFFFFFFFF),
            "standard_metadata.ingress_port": (1, 0x1FF)
        },
        priority=10,
        action_name="MyIngress.drop",
        action_params={
        })
    ingres_sw.DeleteTableEntry(table_entry)
    print(f"Drop {src_ip_addr} rule purged on {ingres_sw.name}")

def write_rule_arp(p4info_helper, ingres_sw):
    """
        Writes the rule to set ARP logic by default.
    """
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.arp_lpm",
        match_fields={
            "meta.is_arp": 1
        },
        action_name="MyIngress.flood",
        action_params={
        })
    ingres_sw.WriteTableEntry(table_entry)
    print(f"Forward rule inserted on {ingres_sw.name}")

def setup_multicast_group(p4info_helper, ingres_sw):
    """
        This function creates the by default multicast groups which are:
        Group1: [2,3]   For packets entering through port 1
        Group2: [1,2]   For packets entering through port 2
        Group3: [1,3]   For packets entering through port 3
    """
    ports = [1, 2, 3]
    for in_port in ports:
        multicast_entry = p4info_helper.buildMulticastGroupEntry(
            multicast_group_id=in_port,
            replicas=[{"egress_port": p, "instance": 0} for p in ports if p!= in_port]
        )

        ingres_sw.WritePREEntry(multicast_entry)
        print(f"Multicast group {in_port} inserted on {ingres_sw.name}")

def readTableRules(p4info_helper, ap):
    """
        Reads the table entries from all tables on the ap (switch)
    """
    print(f"\n----------- Reading tables rules for {ap.name} --------")
    for response in ap.ReadTableEntries():
        for entity in response.entities:
            entry = entity.table_entry
            table_name = p4info_helper.get_tables_name(entry.table_id)
            print(f"{table_name}: ", end=' ')
            for m in entry.match:
                print(p4info_helper.get_match_field_name(table_name, m.field_id), end=' ')
                print(f"{p4info_helper.get_match_field_value(m)},", end=' ')
            action =entry.action.action
            action_name = p4info_helper.get_actions_name(action.action_id)
            print('->', action_name, end=' ')
            for p in action.params:
                print(p4info_helper.get_action_param_name(action_name, p.param_id), end=' ')
                print('%r' % p.value, end=' ')
            print()

def printCounter(p4info_helper, sw, counter_name, index):
    """
    Reads the specified counter at the specified index from the switch.
    In this case it will read the traffic counters, print it and return back.
    
    :param p4info_helper: the P4Info helper
    :param sw:  the switch connection
    :param counter_name: the name of the counter from the P4 program
    :param index: the counter index (based on sensor ip)
    """
    for response in sw.ReadCounters(p4info_helper.get_counters_id(counter_name), index):
        for entity in response.entities:
            counter = entity.counter_entry
            print("%s %s %d: %d packets (%d bytes)" % (
                sw.name, counter_name, index,
                counter.data.packet_count, counter.data.byte_count
            ))
    return counter.data.packet_count
            
def main():
    p4info_helper = p4runtime_lib.helper.P4InfoHelper("build/basic.p4.p4info.txt")

    # This dictionary will manage almost all relevant parameters of the aps and the connected stations
    aps_dictionary = dict()
    counter = 0
    for ap in mn_aps:
        counter = counter + 1
        port = mn_baseport + counter

        aps_dictionary[ap] = dict()
        aps_dictionary[ap]['name'] = ap
        #Initialize counters of sensors traffic
        aps_dictionary[ap]['actual_counter'] = dict()
        aps_dictionary[ap]['last_counter'] = dict()
        aps_dictionary[ap]['dropped_sensors'] = list()
        for sta in mn_sensors.keys():
            aps_dictionary[ap]['actual_counter'][sta] = 0
            aps_dictionary[ap]['last_counter'][sta] = 0

        aps_dictionary[ap]['p4reference'] = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name=ap,
            address= mn_base_ip + ':' + str(port),
            device_id= counter,
            proto_dump_file= 'logs/ap' + str(counter) + '-p4runtime.log')

        aps_dictionary[ap]['p4reference'].MasterArbitrationUpdate()
        aps_dictionary[ap]['p4reference'].SetForwardingPipelineConfig(p4info=p4info_helper.p4info, bmv2_json_file_path="build/basic.json")
        print(f"Installed P4 Program using SetFowrwandingPipelineConfig on {aps_dictionary[ap]['name']}")

        # Insert multicast groups
        setup_multicast_group(p4info_helper, ingres_sw=aps_dictionary[ap]['p4reference'])

        # IPv4 Rules
        write_ipv4_forward_rule(p4info_helper, ingres_sw=aps_dictionary[ap]['p4reference'], dst_ip_addr=influxdb_ip, mask=32)
        write_ipv4_forward_rule(p4info_helper, ingres_sw=aps_dictionary[ap]['p4reference'], dst_ip_addr="10.0.0.0", mask=24) # mask /8

        # ARP Rules
        write_rule_arp(p4info_helper, ingres_sw=aps_dictionary[ap]['p4reference'])

    # Print Installed Tables
    for ap in mn_aps:
        readTableRules(p4info_helper, aps_dictionary[ap]['p4reference'])

    # Initialize object to manage Influxdb and Ryu queries
    sensors_state = Sensors_state()

    connected_aps = dict() # Dictionary to search which is the AP connected to each STA
    while True:
        sleep(30)
        print('\n----- Reading traffic counters -----')
        for ap in mn_aps:
            for sta, sta_ip in mn_sensors.items():
                # Index to query aps counters based on stations ips
                sta_index = int(ipaddress.IPv4Address(sta_ip)) & 0xFFFF
                aps_dictionary[ap]['last_counter'][sta] = aps_dictionary[ap]['actual_counter'][sta]
                aps_dictionary[ap]['actual_counter'][sta] = printCounter(p4info_helper, aps_dictionary[ap]['p4reference'], "MyIngress.StationsTrafficCounter", sta_index)
                if aps_dictionary[ap]['actual_counter'][sta] != aps_dictionary[ap]['last_counter'][sta]:
                    retransmited_packets = aps_dictionary[ap]['actual_counter'][sta] - aps_dictionary[ap]['last_counter'][sta]
                    print(f"AP {aps_dictionary[ap]['name']} is directly connected to {sta}")
                    connected_aps[sta] = aps_dictionary[ap]['name']
        
        print('\n----- Purging drop records -----')
        for ap in mn_aps:
            print(f"Dropped sensors in {ap}: {aps_dictionary[ap]['dropped_sensors']}")
            for dropped_sensor in aps_dictionary[ap]['dropped_sensors']:
                delete_ipv4_drop_rule(p4info_helper, aps_dictionary[ap]['p4reference'], influxdb_ip, mn_sensors[dropped_sensor])
            # Clear dropped sensors
            aps_dictionary[ap]['dropped_sensors'].clear()
        
        print('\n----- Reading sensors state -----')
        sensors_value = sensors_state.query_influxdb()
        if sensors_value:
            sensors_response = sensors_state.query_bentoml(sensors_value)
            
            try:
                for sensor in sensors_response.values():
                    if sensor["bentoml_response"]:
                        write_ipv4_drop_rule(p4info_helper, aps_dictionary[connected_aps[sensor["name"]]]['p4reference'], influxdb_ip, mn_sensors[sensor["name"]])
                        aps_dictionary[connected_aps[sensor["name"]]]['dropped_sensors'].append(sensor["name"])
                        print(f"Added drop rule for {sensor['name']} in {aps_dictionary[connected_aps[sensor['name']]]['name']} after bentoml response {sensor['bentoml_response']}")
                    respuesta = sensor["bentoml_response"]
            except KeyError as e:
                print(f"No response of bentoml regarding {e}")
            

if __name__ == '__main__':
    main()


