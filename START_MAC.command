#!/bin/bash
cd "$(dirname "$0")"
echo "Installing dependencies..."
pip3 install pillow requests -q
echo "Starting deskymon..."
python3 deskymon_mac.py
