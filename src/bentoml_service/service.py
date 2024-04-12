import bentoml
from bentoml.io import JSON
import pandas as pd

rfc_runner = bentoml.sklearn.get("rfc_class:latest").to_runner()

svc = bentoml.Service("random_forest_classifier", runners=[rfc_runner])

input_spec = JSON.from_sample({"temp": 40.0, "out/in_encoded": 0, "Month": 12})


@svc.api(input=input_spec, output=JSON())
def predict(input_json):
    df = pd.DataFrame([input_json])
    return rfc_runner.predict.run(df)
