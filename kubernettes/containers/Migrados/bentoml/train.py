import pandas as pd
import bentoml
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC

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

if __name__ == "__main__":

    # Cargamos los datos
    data=pd.read_csv('dataset/manufacturing_6G_dataset.csv')
    df=pd.DataFrame(data,columns=['Timestamp', 'Operation_Mode', 'Temperature_C', 'Vibration_Hz', 'Power_Consumption_kW', 'Network_Latency_ms','Packet_Loss_%', 'Quality_Control_Defect_Rate_%', 'Production_Speed_units_per_hr', 'Predictive_Maintenance_Score', 'Error_Rate_%', 'Efficiency_Status'])


    # Paso el tipo de datos de object a datetime y me quedo con el mes solo (por seguir el criterio del anterior dataset)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df['Month'] = df['Timestamp'].dt.month

    # Ahora pongo labels a Operation Mode y Efficiency Status. Este último va a ser el warning
    le = LabelEncoder()
    df['Operation_Mode'] = le.fit_transform(df['Operation_Mode'])
    df['Efficiency_Status'] = le.fit_transform(df['Efficiency_Status'])

    #X = df[['Operation_Mode', 'Temperature_C', 'Vibration_Hz', 'Power_Consumption_kW', 'Network_Latency_ms','Packet_Loss_%', 'Quality_Control_Defect_Rate_%', 'Production_Speed_units_per_hr', 'Predictive_Maintenance_Score', 'Error_Rate_%', 'Month']]
    X = df[columnas_continuas]
    y = df['Efficiency_Status']

    # Estandarizo para el tratamiento de los datos
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
    X_final = pd.concat([X_scaled, df[columnas_discretas].reset_index(drop=True)], axis=1)

    # Selecciono el modelo SVM
    # Al ser random forest mantengo los valores de X originales
    model = SVC()
    model.fit(X_final, y)

    # Guardar el modelo y el escaler entrenado con pickle
    joblib.dump(model, 'rfc_model.pkl')
    joblib.dump(scaler, 'rfc_scaler.pkl')

    bento_model = bentoml.sklearn.save_model("rfc_class", model)
    print(f"Model saved: {bento_model}")
    bento_scaler = bentoml.picklable_model.save_model("rfc_scaler", scaler)
    print(f"Model saved: {bento_scaler}")

    # Test running inference with BentoML runner
    json_data = {'Operation_Mode': 1, 'Temperature_C': 55, 'Vibration_Hz': 2.67, 'Power_Consumption_kW': 5.24, 'Network_Latency_ms': 25,'Packet_Loss_%': 2.5, 'Quality_Control_Defect_Rate_%': 5.989, 'Production_Speed_units_per_hr': 224.74, 'Predictive_Maintenance_Score': 0.43, 'Error_Rate_%': 7.83, 'Month': 12}
    test_runner = bentoml.sklearn.get("rfc_class:latest").to_runner()
    # Dado que hice el estandarizado de los datos, tengo que estandarizar la entrada
    test_scaler = bentoml.picklable_model.load_model("rfc_scaler:latest")
    test_runner.init_local()

    json_data_df = pd.DataFrame([json_data])
    test_scaled = pd.DataFrame(scaler.transform(json_data_df[columnas_continuas]), columns=columnas_continuas)
    test_final = pd.concat([test_scaled, json_data_df[columnas_discretas].reset_index(drop=True)], axis=1)

    assert test_runner.predict.run(test_final) == model.predict(test_final)
