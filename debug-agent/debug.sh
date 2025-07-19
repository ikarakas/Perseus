#!/bin/bash
# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
# Run agent with debug logging

source venv/bin/activate
python agent.py --log-level DEBUG
