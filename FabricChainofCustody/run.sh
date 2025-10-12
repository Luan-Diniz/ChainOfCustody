#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- 1. Tearing down previous environment ---"
./stop.sh

echo "--- 2. Starting MongoDB ---"
docker compose -f docker-compose-mongo.yml up -d

# It's good practice to wait a moment for the database to be ready
echo "Waiting 5 seconds for MongoDB to initialize..."
sleep 5

echo "--- 3. Starting Hyperledger Fabric & Deploying Chaincode ---"
# This script now has its own internal sleep, so we just run it
./run_network.sh

echo "--- 4. Building and Starting the Gateway Application ---"
cd gateway
npm install
npm run build
npm start