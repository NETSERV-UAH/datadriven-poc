import pandas as pd
import bentoml
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder


if __name__ == "__main__":

    # Cargamos los datos
    data=pd.read_csv('dataset/IIOT-temp-warn-max.csv')
    df=pd.DataFrame(data,columns=['room_id/id', 'noted_date', 'temp', 'out/in', 'Month', 'name_months','temp_warn'])

    # Codificar la columna 'out/in' a valores numéricos
    le = LabelEncoder()
    df['out/in_encoded'] = le.fit_transform(df['out/in'])

    # Características: Temperatura, Ubicación (dentro o fuera), Mes
    X = df[['temp', 'out/in_encoded', 'Month']]
    y = df['temp_warn']  # Etiquetas: Warnings correspondientes (0 o 1)

    # Entrenar el modelo
    model = RandomForestClassifier()
    model.fit(X, y)

    # Guardar el modelo entrenado con pickle
    joblib.dump(model, 'rfc_model.pkl')

    bento_model = bentoml.sklearn.save_model("rfc_class", model)
    print(f"Model saved: {bento_model}")

    # Test running inference with BentoML runner
    json_data = {'temp': [40.4], 'out/in_encoded': [0], 'Month': [12]}
    test_runner = bentoml.sklearn.get("rfc_class:latest").to_runner()
    test_runner.init_local()
    assert test_runner.predict.run(pd.DataFrame(json_data)) == model.predict(pd.DataFrame(json_data))