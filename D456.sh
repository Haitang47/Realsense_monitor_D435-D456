#!/bin/bash

sudo tailscale up

TS_IP=$(tailscale ip -4)

echo "http://$TS_IP:5000"

python3 realsense_monitor.py
