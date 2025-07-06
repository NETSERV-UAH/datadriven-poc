#!/usr/bin/env python3

import uuid, pickle
import numpy as np
#import pandas as pd
import time
import sys, os, subprocess
import re
import requests
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

    # Estas variaciones están sacadas del dataset.
    # Se han tomado calculando el salto de un registro con el siguiente para cada machine ID
    # El salto de tiempo medio de cada intervalo es de unos 50 minutos
    # Entonces su simulación en segundos como se va a hacer aquí es algo irreal
    # Otra opción sería hacer un ajuste de si la variación es en 50 minutos, en 10 segundos será tal.
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

DATASET_INTERVAL = 3000 # 50min Intervalo entre registros del dataset

class IIoT_Sensor(object):
    """
                Class to define IIoT Sensor
        """
    def __init__(self, name, operation_mode, interval=1.0):
        self.uuid = uuid.uuid4()
        self.name = name
        self.interval = interval
        # Variables
        #self.operation_mode = np.random.uniform()
        #self.temperature = float(self.init_temperature())

        # Inicializo los valores basandome en la distribución uniforme mostrada en Kaggle
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
        self.operation_mode = operation_mode

        self.datetime = datetime.now()
        self.temperature_alert = False
        self.INFLUX_URL_API = "http://192.168.56.12:8086/api/v2"
        self.INFLUX_ORG_ID = ""
        self.INFLUX_BUCKET = ""
        self.INFLUX_TOKEN = "3hv3m8nphSlHRbVbKQ7o5Hrm0S4FhLDhu8WWGt9abXHQ26Ked4hGDSRqtZsYC-hc2gS9snCLjN5p9OnoYBeRYA=="
        self.SENSOR_TOKEN = ""

        # Verifica la conectividad antes de continuar
        if not self.check_connectivity():
            print(f"{Color.RED}[ERROR]{Color.END} No connectivity to InfluxDB API ({self.INFLUX_URL_API}). Exiting.")
            sys.exit(1)

        self.run()

    def scan_aps(self, interface):
        try:
            result = subprocess.check_output(["iw", "dev", interface, "scan"], stderr=subprocess.DEVNULL)
            result = result.decode("utf-8")

            aps = []
            current_ap = {}

            for line in result.splitlines():
                line = line.strip()

                if line.startswith("BSS"):
                    if current_ap:
                        aps.append(current_ap)
                        current_ap={}
                    current_ap["associated"] = True if "associated" in line else False

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
            print("Error al ejecutar iw scan:", e)
            return []

    def connect_new_ap(self, aps, interface):
        available_aps = [ap for ap in aps if ap['associated'] == False]

        if not available_aps:
            print(f"{Color.GREEN}[INFO]{Color.END} No other aps available.")
        else:
            best_ap = max(available_aps, key=lambda ap: ap['Signal'])
            print(f"{Color.GREEN}[INFO]{Color.END} Conecting to {best_ap['SSID']}")
            subprocess.run(["iw", "dev", interface, "disconnect"], check=True)
            subprocess.run(["iw", "dev", interface, "connect", best_ap['SSID']], check=True)

    def check_connectivity(self, timeout=20):
        """Check if the API is reachable before proceeding with OAuth."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://192.168.56.12:8086" + "/health", timeout=5)
                if response.status_code == 200:
                    print(f"{Color.GREEN}[INFO]{Color.END} Connectivity to InfluxDB API verified.")
                    return True
                else:
                    print(f"{Color.YELLOW}[WARNING]{Color.END} InfluxDB API returned status {response.status_code}. Retrying...")
            except requests.exceptions.RequestException as e:
                print(f"{Color.RED}[ERROR]{Color.END} Unable to reach InfluxDB API: {e}. Retrying...")
            time.sleep(2)
        return False

    def update_variables(self, new_variables):

        self.variables = new_variables
        self.datetime = datetime.now()
        print(f"{Color.GREEN}[UPDATE]{Color.END}[{Color.BLUE}{self.name}{Color.END}] Sensor variables updated to {self.variables} at {self.datetime}.")

        # Enviamos la temp a la bbdd
        headers = {
            "Authorization": f"Token {self.SENSOR_TOKEN}",
            "Content-type": "text/plain; charset=utf-8",
            "Accept": "application/json"
        }

        data = f"tempSensors,sensor_name={self.name},sensor_id={self.uuid} operation_mode={self.operation_mode},temperature={self.variables['temperature']},vibration={self.variables['vibration']},power_consumption={self.variables['power_consumption']},network_latency={self.variables['network_latency']},packet_loss={self.variables['packet_loss']},quality_control_defect_rate={self.variables['quality_control_defect_rate']},production_speed_units={self.variables['production_speed_units']},predictive_maintenance_score={self.variables['predictive_maintenance_score']},error_rate={self.variables['error_rate']} {time.time_ns()}"

        # Realiza la solicitud POST
        url = self.INFLUX_URL_API + f"/write?org={self.INFLUX_ORG_ID}&bucket={self.INFLUX_BUCKET}&precision=ns"
        try:
            response = requests.post(url, headers=headers, data=data, timeout=0.5)
        except requests.exceptions.RequestException as e:
            print(f"{Color.RED}[ERROR]{Color.END} Unable to reach database. Switch might be dropping packets: {e}")
            sta = self.name.split('-')[1]
            # Desconectamos la estación para que haga rel associate to otro ap
            available_aps = self.scan_aps(f"{sta}-wlan0")
            print(available_aps)
            self.connect_new_ap(available_aps, f"{sta}-wlan0")
            try:
                response = requests.post(url, headers=headers, data=data, timeout = 0.5) # Le quito el timeout porque si no lo pilla, lo detecto luego en el siguiente mensaje
            except requests.exceptions.RequestException as e:
                print(f"{Color.RED}[ERROR]{Color.END} No se ha podido conectar aún\n{e}\n")


    def oauth_get_token(self):

        # Define los HEADERS de la peti
        headers = {
            "Authorization": f"Token {self.INFLUX_TOKEN}",
            "Content-type": "application/json"
        }

        # Define los datos
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
                        "name": self.INFLUX_BUCKET
                    }
                }
            ]
        }

        # Realiza la solicitud POST
        url = self.INFLUX_URL_API + "/authorizations"
        response = requests.post(url, headers=headers, json=data)

        # Parsea la respuesta JSON
        parsed_response = response.json()

        # Guardamos el token dado
        self.SENSOR_TOKEN = parsed_response["token"]



    def oauth_get_INFLUX_ORG_ID(self):

        # Define los HEADERS de la peti
        headers = {
            "Authorization": f"Token {self.INFLUX_TOKEN}",
            "Content-type": "application/json"
        }

         # Define los datos
        data = {
            "name": "UAH"
        }

        # Realiza la solicitud POST
        url = self.INFLUX_URL_API + "/orgs"
        response = requests.get(url, headers=headers, json=data)

        # Parsea la respuesta JSON
        parsed_response = response.json()

        # Guardamos el token dado
        self.INFLUX_ORG_ID = parsed_response["orgs"][0]["id"]


    def oauth_get_INFLUX_BUCKET(self):

        # Define los HEADERS de la peti
        headers = {
            "Authorization": f"Token {self.INFLUX_TOKEN}",
            "Content-type": "application/json"
        }

         # Define los datos
        data = {
            "org": "UAH",
            "name": "iiot_data"
        }

        # Realiza la solicitud POST
        url = self.INFLUX_URL_API + "/buckets"
        response = requests.get(url, headers=headers, json=data)

        # Parsea la respuesta JSON
        parsed_response = response.json()

        # Guardamos el token dado
        self.INFLUX_BUCKET = next((item['id'] for item in parsed_response['buckets'] if item['name'] == 'iiot_data'), None)


    def simulate_variables_variation(self, time_interval, previous_variables):
        """
        Simulates realistic temperature variation based on time interval and location,
        considering inertia from previous variations.
        """

        # Factor de conversión de la desviación típica al time_interval real (el del dataset es 50 minutos)
        factor_std_dev = np.sqrt(time_interval/DATASET_INTERVAL)

        new_variables = dict()
        for variable in self.variables:
            # Calcula la variación aleatoria basada en una distribución normal
            random_variation = np.random.normal(statistics_variables[variable]['steps_mean'], statistics_variables[variable]['std_dev']*factor_std_dev)

            # Calcula la nueva variación como la suma de la variación aleatoria y la inercia anterior
            new_variation = np.random.choice([-1, 1]) * 0.7 * random_variation + 0.3 * (self.variables[variable] - previous_variables[variable])

            # Calcula el nuevo valor
            new_variables[variable] = self.variables[variable] + new_variation * time_interval
            if variable in ['packet_loss', 'quality_control_defect_rate', 'error_rate']:
                # Son variables en porcentaje por lo que las limito
                new_variables[variable] = np.clip(new_variables[variable], 0, 100)
            elif variable == 'predictive_maintenance_score':
                # Esta variable en el dataset va de 0 a 1 así que también la limito
                new_variables[variable] = np.clip(new_variables[variable], 0, 1)
            elif variable in ['vibration', 'power_consumption', 'network_latency','production_speed_units']:
                new_variables[variable] = np.clip(new_variables[variable], 0, None)

        return new_variables


    def run(self):

        previous_variables = self.variables

        # Oauth process
        self.oauth_get_INFLUX_ORG_ID()
        self.oauth_get_INFLUX_BUCKET()
        self.oauth_get_token()

        while(True):
            try:

                self.update_variables(self.simulate_variables_variation(self.interval, previous_variables))
                previous_variables = self.variables
                time.sleep(self.interval)
            except (KeyboardInterrupt, SystemExit):
                print("Exiting...")
                break

if __name__ == "__main__":
    # Nombre de la estación, time_interval
    sensor1 = IIoT_Sensor(sys.argv[1], int(sys.argv[2]) if len(sys.argv) >= 3 else 0, 2.0)
