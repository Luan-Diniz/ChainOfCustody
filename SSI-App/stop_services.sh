#!/bin/bash

echo "Stopping all services..."

pkill -f mockDbservice/mockdb_service.py
pkill -f issuer/webhook_handler.py
pkill -f holder/holder_api.py
pkill -f issuer/verifier_api.py &

echo "All services have been stopped."