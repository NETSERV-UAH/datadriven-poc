#!/bin/bash

set -e
echo "[Info] Arrancando servicio de BentoML"
bentoml serve -p3001 . &
wait
