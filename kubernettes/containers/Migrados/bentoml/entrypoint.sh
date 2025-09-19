#!/bin/bash

set -e
echo "[Info] Arrancando servicio de BentoML"
exec bentoml serve -p3001 .
