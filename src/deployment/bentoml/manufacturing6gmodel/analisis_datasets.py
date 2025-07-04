import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

RANDOM_STATE = 33 # Semilla
np.random.seed(RANDOM_STATE)

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

    print(df.head())
    print(df.info())

    # Paso el tipo de datos de object a datetime y me quedo con el mes solo (por seguir el criterio del anterior dataset)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df['Month'] = df['Timestamp'].dt.month

    # Ahora pongo labels a Operation Mode y Efficiency Status. Este último va a ser el warning
    le = LabelEncoder()
    df['Operation_Mode'] = le.fit_transform(df['Operation_Mode'])
    df['Efficiency_Status'] = le.fit_transform(df['Efficiency_Status'])

    X = df[columnas_continuas]
    Y = df['Efficiency_Status']

    # Estandarizo para el tratamiento de los datos
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
    X_final =  pd.concat([X_scaled, df[columnas_discretas].reset_index(drop=True)], axis=1)

    # Entreno modelo
    X_train, X_test, y_train, y_test = train_test_split(X_final, Y, test_size=0.2, random_state=RANDOM_STATE, stratify=Y) # Stratify con y para que contengan de los tres casos del label

    models = {
    "Logistic Regression": LogisticRegression(),        # 0.9146
    "K-Nearest Neighbors": KNeighborsClassifier(),      # 0.9108
    "Support Vector Machine": SVC(),                    # 0.9747
    "Decision Tree": DecisionTreeClassifier(),          # 1.0000
    "Random Forest": RandomForestClassifier(),          # 1.0000
    "Gradient Boosting": GradientBoostingClassifier(),  # 1.0000
    "Naive Bayes": GaussianNB(),                        # 0.9597
    }

    results = {}

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        results[name] = accuracy
        print(f"{name}: {accuracy:.4f}")
        print(classification_report(y_test, y_pred))
