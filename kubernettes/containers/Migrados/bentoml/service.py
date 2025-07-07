from __future__ import annotations
import bentoml
import pandas as pd
from bentoml.sklearn import load_model as load_sklearn_model
from bentoml.picklable_model import load_model as load_pickle_model


columnas_continuas = [
    'Temperature_C',
    'Vibration_Hz',
    'Power_Consumption_kW',
    'Network_Latency_ms',
    'Packet_Loss_%',
    'Quality_Control_Defect_Rate_%',
    'Production_Speed_units_per_hr',
    'Predictive_Maintenance_Score',
    'Error_Rate_%'
]

columnas_discretas = ['Operation_Mode', 'Month']

@bentoml.service()
class RandomForestClassifierService:
    def __init__(self):
        self.model = load_sklearn_model("rfc_class:latest")
        self.scaler = load_pickle_model("rfc_scaler:latest")

    @bentoml.api
    def predict(self, input_data: dict) -> list[int]:
        df = pd.DataFrame([input_data])

        # Estandarizar columnas continuas
        scaled_continuas = pd.DataFrame(
            self.scaler.transform(df[columnas_continuas]),
            columns=columnas_continuas
        )

        # Combinar con columnas discretas
        df_final = pd.concat(
            [scaled_continuas, df[columnas_discretas].reset_index(drop=True)],
            axis=1
        )

        prediction = self.model.predict(df_final)
        return prediction.tolist()

