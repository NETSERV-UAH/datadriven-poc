#!/usr/bin/env python3

import uuid, pickle
import numpy as np
#import pandas as pd
import time
import sys
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

class IIoT_Sensor(object):
    """
		Class to define IIoT Sensor
	"""
    def __init__(self, name, inside=True, temperature_path="temperatures.pkl", interval=1.0):
        self.uuid = uuid.uuid4()
        self.name = name
        self.location = inside
        self.interval = interval
        self.temperature_path = temperature_path
        self.temperature = float(self.init_temperature())
        self.datetime = datetime.now()
        self.temperature_alert = False
        self.INFLUX_URL_API = "http://192.168.56.12:8086/api/v2"
        self.INFLUX_ORG_ID = ""
        self.INFLUX_BUCKET = ""
        self.INFLUX_TOKEN = "3hv3m8nphSlHRbVbKQ7o5Hrm0S4FhLDhu8WWGt9abXHQ26Ked4hGDSRqtZsYC-hc2gS9snCLjN5p9OnoYBeRYA=="
        self.SENSOR_TOKEN = ""
        self.run()


    def init_temperature(self):

        return np.random.randint(29,31) if self.location else np.random.randint(35,42)


    def update_temperature(self, new_temperature):

        self.temperature = float(new_temperature)
        self.datetime = datetime.now()
        print(f"{Color.GREEN}[UPDATE]{Color.END}[{Color.BLUE}{self.name}{Color.END}] Sensor temperature updated to {self.temperature} °C at {self.datetime}.")

        # Enviamos la temp a la bbdd
        headers = {
            "Authorization": f"Token {self.SENSOR_TOKEN}",
            "Content-type": "text/plain; charset=utf-8",
            "Accept": "application/json"
        }

        data = f"tempSensors,sensor_name={self.name},sensor_id={self.uuid} temp={self.temperature} {time.time_ns()}"

        # Realiza la solicitud POST
        url = self.INFLUX_URL_API + f"/write?org={self.INFLUX_ORG_ID}&bucket={self.INFLUX_BUCKET}&precision=ns"
        response = requests.post(url, headers=headers, data=data)



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
        self.INFLUX_BUCKET = parsed_response["buckets"][2]["id"]


    def simulate_temperature_variation(self, time_interval, previous_temperature):
        """
        Simulates realistic temperature variation based on time interval and location,
        considering inertia from previous variations.
        """
        # Define las variaciones promedio y las desviaciones estándar según la ubicación
        if self.location:
            average_variation = 0.05
            std_deviation = 0.01
        else:
            average_variation = -0.03
            std_deviation = 0.01
        
        # Calcula la variación aleatoria basada en una distribución normal
        random_variation = np.random.normal(average_variation, std_deviation)

        # Calcula la nueva variación como la suma de la variación aleatoria y la inercia anterior
        new_variation = np.random.choice([-1, 1]) * 0.7 * random_variation + 0.3 * (self.temperature - previous_temperature)

        # Calcula la nueva temperatura
        new_temperature = self.temperature + new_variation * time_interval

        return new_temperature


    def run(self):

        previous_temperature = self.temperature
        
        # Oauth process
        self.oauth_get_INFLUX_ORG_ID()
        self.oauth_get_INFLUX_BUCKET()
        self.oauth_get_token()

        while(True):
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
    sensor1 = IIoT_Sensor(sys.argv[1], False, 'temperatures.pkl', 2.0)
