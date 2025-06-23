#!/usr/bin/env python3

import uuid, time, sys, os, requests
import numpy as np
from datetime import datetime

# Códigos de colores ANSI
class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class IIoT_Sensor(object):
    def __init__(self, name, inside=True, temperature_path="temperatures.pkl", interval=1.0,
                 influx_ip=None, influx_token=None):
        self.uuid = uuid.uuid4()
        self.name = name
        self.location = inside
        self.interval = interval
        self.temperature_path = temperature_path
        self.temperature = float(self.init_temperature())
        self.datetime = datetime.now()
        self.temperature_alert = False
        self.INFLUX_URL_API = influx_ip
        self.INFLUX_ORG_ID = None
        self.INFLUX_BUCKET = None
        self.INFLUX_TOKEN = influx_token
        self.SENSOR_TOKEN = ""

        if not self.check_connectivity():
            print(f"{Color.RED}[ERROR]{Color.END} No connectivity to InfluxDB API ({self.INFLUX_URL_API}). Exiting.")
            sys.exit(1)

        self.run()

    def check_connectivity(self, timeout=20):
        """Check if the API is reachable before proceeding with OAuth."""
        health_url = self.INFLUX_URL_API.replace("/api/v2", "/health")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    print(f"{Color.GREEN}[INFO]{Color.END} Connectivity to InfluxDB API verified.")
                    return True
                else:
                    print(f"{Color.YELLOW}[WARNING]{Color.END} InfluxDB API returned status {response.status_code}. Retrying...")
            except requests.exceptions.RequestException as e:
                print(f"{Color.RED}[ERROR]{Color.END} Unable to reach InfluxDB API: {e}. Retrying...")
            time.sleep(2)
        return False

    def init_temperature(self):
        return np.random.randint(29, 31) if self.location else np.random.randint(35, 42)

    def update_temperature(self, new_temperature):
        self.temperature = float(new_temperature)
        self.datetime = datetime.now()
        print(f"{Color.GREEN}[UPDATE]{Color.END}[{Color.BLUE}{self.name}{Color.END}] Sensor temperature updated to {self.temperature} °C at {self.datetime}.")

        headers = {
            "Authorization": f"Token {self.SENSOR_TOKEN}",
            "Content-type": "text/plain; charset=utf-8",
            "Accept": "application/json"
        }

        data = f"tempSensors,sensor_name={self.name},sensor_id={self.uuid},location={int(self.location)} temp={self.temperature} {time.time_ns()}"
        url = self.INFLUX_URL_API + f"/write?org={self.INFLUX_ORG_ID}&bucket={self.INFLUX_BUCKET}&precision=ns"

        try:
            response = requests.post(url, headers=headers, data=data, timeout=0.5)
        except requests.exceptions.RequestException as e:
            print(f"{Color.RED}[ERROR]{Color.END} Unable to reach database. Switch might be dropping packets: {e}")
            sta = self.name.split('-')[1]
            os.system(f"iw dev {sta}-wlan0 disconnect")
            time.sleep(3)
            os.system(f"iw dev {sta}-wlan0 connect ssid-ap2")

    def oauth_get_token(self):
        headers = {
            "Authorization": f"Token {self.INFLUX_TOKEN}",
            "Content-type": "application/json"
        }

        data = {
            "status": "active",
            "description": f"iott-device-{self.name}",
            "orgID": self.INFLUX_ORG_ID,
            "permissions": [
                {
                    "action": "read",
                    "resource": {
                        "orgID": self.INFLUX_ORG_ID,
                        "type": "buckets"
                    }
                },
                {
                    "action": "write",
                    "resource": {
                        "orgID": self.INFLUX_ORG_ID,
                        "type": "buckets",
                        "name": "iiot_data"
                    }
                }
            ]
        }

        url = self.INFLUX_URL_API + "/authorizations"
        response = requests.post(url, headers=headers, json=data)
        parsed_response = response.json()
        self.SENSOR_TOKEN = parsed_response["token"]

    def oauth_get_INFLUX_ORG_ID(self):
        headers = {
            "Authorization": f"Token {self.INFLUX_TOKEN}",
            "Content-type": "application/json"
        }

        url = self.INFLUX_URL_API + "/orgs"
        response = requests.get(url, headers=headers)
        parsed_response = response.json()
        self.INFLUX_ORG_ID = next((org["id"] for org in parsed_response["orgs"] if org["name"] == "UAH"), None)

    def oauth_get_INFLUX_BUCKET(self):
        headers = {
            "Authorization": f"Token {self.INFLUX_TOKEN}",
            "Content-type": "application/json"
        }

        url = self.INFLUX_URL_API + "/buckets"
        response = requests.get(url, headers=headers)
        parsed_response = response.json()
        self.INFLUX_BUCKET = next((item['id'] for item in parsed_response['buckets'] if item['name'] == 'iiot_data'), None)

    def simulate_temperature_variation(self, time_interval, previous_temperature):
        average_variation = 0.05 if self.location else -0.03
        std_deviation = 0.01
        random_variation = np.random.normal(average_variation, std_deviation)
        new_variation = np.random.choice([-1, 1]) * 0.7 * random_variation + 0.3 * (self.temperature - previous_temperature)
        return self.temperature + new_variation * time_interval

    def run(self):
        previous_temperature = self.temperature

        # Obtener orgID y bucketID automáticamente
        self.oauth_get_INFLUX_ORG_ID()
        self.oauth_get_INFLUX_BUCKET()
        self.oauth_get_token()

        while True:
            try:
                self.update_temperature(self.simulate_temperature_variation(self.interval, previous_temperature))
                previous_temperature = self.temperature
                time.sleep(self.interval)
            except (KeyboardInterrupt, SystemExit):
                print("Exiting...")
                break

    def __str__(self):
        return f"-----------------------------------------------------\nSensor ID: {self.uuid}\n\t[+] Name: {self.name}\n\t[+] Temperature: {self.temperature} °C\n\t[+] Date: {self.datetime}\n\t[+] Location: {'Inside' if self.location else 'Outside'}\n\t[+] Temperature Warning: {'Yes' if self.temperature_alert else 'No'}\n-----------------------------------------------------"

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(f"{Color.RED}[USAGE]{Color.END} python3 iiot_sensor.py <name> <inside(0|1)> <influx_ip> <token>")
        sys.exit(1)

    name = sys.argv[1]
    location = int(sys.argv[2])
    influx_ip = sys.argv[3]
    token = sys.argv[4]

    sensor1 = IIoT_Sensor(name, location, 'temperatures.pkl', 2.0, influx_ip=influx_ip, influx_token=token)

