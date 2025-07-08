#!/usr/bin/env python3

import uuid
import numpy as np
import time
import sys
import subprocess
import re
import requests
from datetime import datetime

class Color:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

statistics_variables = {
    'temperature': {'steps_mean': 0.001, 'std_dev': 24.477},
    'vibration': {'steps_mean': 2.25e-05, 'std_dev': 1.993},
    'power_consumption': {'steps_mean': 0.0003, 'std_dev': 3.459},
    'network_latency': {'steps_mean': -0.0003, 'std_dev': 19.95},
    'packet_loss': {'steps_mean': 0.0003, 'std_dev': 2.0384},
    'quality_control_defect_rate': {'steps_mean': -7.974e-05, 'std_dev': 4.0752},
    'production_speed_units': {'steps_mean': -0.0023, 'std_dev': 184.136},
    'predictive_maintenance_score': {'steps_mean': -3.116e-05, 'std_dev': 0.409},
    'error_rate': {'steps_mean': 0.0001, 'std_dev': 6.1185}
}

DATASET_INTERVAL = 3000

class IIoT_Sensor:
    def __init__(self, name, operation_mode, interval=1.0, influx_ip=None, influx_token=None):
        self.uuid = uuid.uuid4()
        self.name = name
        self.interval = interval
        self.operation_mode = operation_mode

        self.variables = {
            'temperature': np.random.uniform(30, 90),
            'vibration': np.random.uniform(0.1, 5),
            'power_consumption': np.random.uniform(1.5, 10),
            'network_latency':  np.random.uniform(1, 50),
            'packet_loss': np.random.uniform(0, 5),
            'quality_control_defect_rate': np.random.uniform(0, 10),
            'production_speed_units': np.random.uniform(50, 500),
            'predictive_maintenance_score': np.random.uniform(0, 1),
            'error_rate': np.random.uniform(0, 15)
        }

        self.datetime = datetime.now()
        self.temperature_alert = False

        if influx_ip.startswith("http"):
            self.INFLUX_URL_API = influx_ip.rstrip("/") + "/api/v2"
        else:
            self.INFLUX_URL_API = f"http://{influx_ip}/api/v2"

        self.INFLUX_ORG_ID = None
        self.INFLUX_BUCKET = None
        self.INFLUX_TOKEN = influx_token
        self.SENSOR_TOKEN = ""

        if not self.check_connectivity():
            print(f"{Color.RED}[ERROR]{Color.END} No connectivity to InfluxDB API ({self.INFLUX_URL_API}). Exiting.")
            sys.exit(1)

        self.run()

    def scan_aps(self, interface):
        try:
            result = subprocess.check_output(["iw", "dev", interface, "scan"], stderr=subprocess.DEVNULL).decode()
            aps = []
            current_ap = {}
            for line in result.splitlines():
                line = line.strip()
                if line.startswith("BSS"):
                    if current_ap:
                        aps.append(current_ap)
                        current_ap = {}
                    current_ap["associated"] = "associated" in line
                elif "SSID:" in line:
                    current_ap["SSID"] = line.split("SSID:")[1].strip()
                elif "signal:" in line:
                    signal = re.search(r"-?\d+\.?\d*", line)
                    if signal:
                        current_ap["Signal"] = float(signal.group())
            if current_ap:
                aps.append(current_ap)
            return aps
        except subprocess.CalledProcessError as e:
            print("Error scanning APs:", e)
            return []

    def connect_new_ap(self, aps, interface):
        available_aps = [ap for ap in aps if not ap.get('associated', False)]
        if not available_aps:
            print(f"{Color.GREEN}[INFO]{Color.END} No other APs available.")
            return
        best_ap = max(available_aps, key=lambda ap: ap.get('Signal', -100))
        print(f"{Color.GREEN}[INFO]{Color.END} Connecting to {best_ap['SSID']}")
        subprocess.run(["iw", "dev", interface, "disconnect"], check=True)
        subprocess.run(["iw", "dev", interface, "connect", best_ap['SSID']], check=True)

    def check_connectivity(self, timeout=20):
        health_url = self.INFLUX_URL_API.replace("/api/v2", "/health")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                r = requests.get(health_url, timeout=5)
                if r.status_code == 200:
                    print(f"{Color.GREEN}[INFO]{Color.END} Connectivity to InfluxDB API verified.")
                    return True
            except:
                print(f"{Color.YELLOW}[WARNING]{Color.END} Retrying InfluxDB connection...")
            time.sleep(2)
        return False

    def update_variables(self, new_variables):
        self.variables = new_variables
        self.datetime = datetime.now()
        print(f"{Color.GREEN}[UPDATE]{Color.END}[{Color.BLUE}{self.name}{Color.END}] Sensor updated at {self.datetime}")

        headers = {
            "Authorization": f"Token {self.SENSOR_TOKEN}",
            "Content-type": "text/plain; charset=utf-8",
            "Accept": "application/json"
        }

        data = f"tempSensors,sensor_name={self.name},sensor_id={self.uuid} operation_mode={self.operation_mode},temperature={self.variables['temperature']},vibration={self.variables['vibration']},power_consumption={self.variables['power_consumption']},network_latency={self.variables['network_latency']},packet_loss={self.variables['packet_loss']},quality_control_defect_rate={self.variables['quality_control_defect_rate']},production_speed_units={self.variables['production_speed_units']},predictive_maintenance_score={self.variables['predictive_maintenance_score']},error_rate={self.variables['error_rate']} {time.time_ns()}"

        url = f"{self.INFLUX_URL_API}/write?org={self.INFLUX_ORG_ID}&bucket={self.INFLUX_BUCKET}&precision=ns"
        try:
            requests.post(url, headers=headers, data=data, timeout=0.5)
        except requests.exceptions.RequestException as e:
            print(f"{Color.RED}[ERROR]{Color.END} Could not write to InfluxDB: {e}")
            iface = self.name.split('-')[1] + "-wlan0"
            aps = self.scan_aps(iface)
            self.connect_new_ap(aps, iface)

    def oauth_get_token(self):
        headers = {
            "Authorization": f"Token {self.INFLUX_TOKEN}",
            "Content-type": "application/json"
        }
        data = {
            "status": "active",
            "description": f"sensor-{self.name}",
            "orgID": self.INFLUX_ORG_ID,
            "permissions": [
                {"action": "read", "resource": {"orgID": self.INFLUX_ORG_ID, "type": "buckets"}},
                {"action": "write", "resource": {"orgID": self.INFLUX_ORG_ID, "type": "buckets", "name": "iiot_data"}}
            ]
        }
        r = requests.post(f"{self.INFLUX_URL_API}/authorizations", headers=headers, json=data)
        self.SENSOR_TOKEN = r.json()["token"]

    def oauth_get_INFLUX_ORG_ID(self):
        headers = {"Authorization": f"Token {self.INFLUX_TOKEN}"}
        r = requests.get(f"{self.INFLUX_URL_API}/orgs", headers=headers)
        self.INFLUX_ORG_ID = next((org["id"] for org in r.json().get("orgs", []) if org["name"] == "UAH"), None)

    def oauth_get_INFLUX_BUCKET(self):
        headers = {"Authorization": f"Token {self.INFLUX_TOKEN}"}
        r = requests.get(f"{self.INFLUX_URL_API}/buckets", headers=headers)
        self.INFLUX_BUCKET = next((b["id"] for b in r.json().get("buckets", []) if b["name"] == "iiot_data"), None)

    def simulate_variables_variation(self, time_interval, previous_variables):
        factor_std_dev = np.sqrt(time_interval / DATASET_INTERVAL)
        new_vars = {}
        for var in self.variables:
            rand = np.random.normal(statistics_variables[var]['steps_mean'],
                                    statistics_variables[var]['std_dev'] * factor_std_dev)
            inertia = 0.3 * (self.variables[var] - previous_variables[var])
            delta = 0.7 * rand + inertia
            new = self.variables[var] + delta * time_interval
            if var in ['packet_loss', 'quality_control_defect_rate', 'error_rate']:
                new = np.clip(new, 0, 100)
            elif var == 'predictive_maintenance_score':
                new = np.clip(new, 0, 1)
            elif var in ['vibration', 'power_consumption', 'network_latency','production_speed_units']:
                new = np.clip(new, 0, None)
            new_vars[var] = new
        return new_vars

    def run(self):
        prev_vars = self.variables
        self.oauth_get_INFLUX_ORG_ID()
        self.oauth_get_INFLUX_BUCKET()
        self.oauth_get_token()
        while True:
            try:
                self.update_variables(self.simulate_variables_variation(self.interval, prev_vars))
                prev_vars = self.variables
                time.sleep(self.interval)
            except (KeyboardInterrupt, SystemExit):
                print("Exiting...")
                break

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(f"{Color.RED}[USAGE]{Color.END} python3 sensor_script.py <name> <mode> <influx_ip:port> <token>")
        sys.exit(1)
    name = sys.argv[1]
    mode = int(sys.argv[2])
    influx_ip = sys.argv[3]
    token = sys.argv[4]
    sensor = IIoT_Sensor(name, mode, interval=2.0, influx_ip=influx_ip, influx_token=token)

