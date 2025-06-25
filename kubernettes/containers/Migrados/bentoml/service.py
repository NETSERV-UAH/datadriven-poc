from __future__ import annotations
import bentoml
import pandas as pd
from bentoml.sklearn import load_model

@bentoml.service()
class RandomForestClassifierService:
    def __init__(self):
        self.model = load_model("rfc_class:latest")

    @bentoml.api
    def predict(self, input_data: dict):
        df = pd.DataFrame([input_data])
        result = self.model.predict(df)
        return result.tolist()

