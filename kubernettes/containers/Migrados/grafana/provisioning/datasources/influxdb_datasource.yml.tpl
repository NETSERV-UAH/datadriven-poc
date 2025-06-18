apiVersion: 1
datasources:
  - name: Prueba
    version: 2
    type: influxdb
    access: proxy
    url: {{ env "INFLUX_URL" }}
    user: {{ env "INFLUX_USER" }}
    password: {{ env "INFLUX_PASSWORD" }}
    jsonData:
      httpMode: POST
      defaultBucket: iiot_data
      organization: UAH
      version: Flux
    secureJsonData:
      token: {{ env "INFLUX_TOKEN" }}

