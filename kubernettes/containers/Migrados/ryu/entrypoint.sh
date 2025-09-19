#!/bin/bash

set -e

ryu-manager /root/ryu_controller.py &

wait
