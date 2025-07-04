import bentoml
#import joblib
from bentoml.io import JSON
import pandas as pd

# Columnas que al ser continuas voy a estandarizar
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
# Columnas de valores discretos, no los estandarizo
columnas_discretas = ['Operation_Mode', 'Month']

rfc_runner = bentoml.sklearn.get("rfc_class:latest").to_runner()
rfc_scaler = bentoml.picklable_model.load_model("rfc_scaler:latest")

svc = bentoml.Service("support_vector_machine_classifier", runners=[rfc_runner])

input_spec = JSON.from_sample({'Operation_Mode': 1, 'Temperature_C': 55, 'Vibration_Hz': 2.67, 'Power_Consumption_kW': 5.24, 'Network_Latency_ms': 25,'Packet_Loss_%': 2.5, 'Quality_Control_Defect_Rate_%': 5.989, 'Production_Speed_units_per_hr': 224.74, 'Predictive_Maintenance_Score': 0.43, 'Error_Rate_%': 7.83, 'Month': 12})


@svc.api(input=input_spec, output=JSON())
def predict(input_json):
    df = pd.DataFrame([input_json])
    # Estandarizo las columnas continuas y concateno las discretas
    scaled_df = pd.DataFrame(rfc_scaler.transform(df[columnas_continuas]), columns=columnas_continuas)
    df_final = pd.concat([scaled_df, df[columnas_discretas].reset_index(drop=True)], axis=1)
    return rfc_runner.predict.run(df_final)
