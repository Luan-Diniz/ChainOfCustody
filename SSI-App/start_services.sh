#!/bin/bash

echo "Starting all services in the background..."

python3 mockDbservice/mockdb_service.py &
python3 holder/holder_api.py &
python3 issuer/verifier_api.py &
python3 issuer/webhook_handler.py &

echo "All services have been started."