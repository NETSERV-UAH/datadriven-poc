#!/bin/bash

########################
# Config  InfluxDB     #
########################

curl http://localhost:8086/api/v2/setup --data '{"username": "jorge", "password": "ELPORRAS", "token": "3hv3m8nphSlHRbVbKQ7o5Hrm0S4FhLDhu8WWGt9abXHQ26Ked4hGDSRqtZsYC-hc2gS9snCLjN5p9OnoYBeRYA==", "bucket": "iiot_data", "org": "UAH"}'
