apiVersion: 1

datasources:
  - name: Prueba
    type: influxdb
    access: proxy
    url: "${INFLUX_URL}"
    user: "${INFLUX_USER}"
    password: "${INFLUX_PASSWORD}"
    isDefault: true
    jsonData:
      httpMode: POST
      defaultBucket: "${INFLUX_BUCKET}"
      organization: "${INFLUX_ORG}"
      version: Flux
    secureJsonData:
      token: "${INFLUX_TOKEN}"

