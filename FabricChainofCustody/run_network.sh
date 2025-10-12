#!/bin/bash

echo "Bringing up Fabric network and creating channel..."
cd network
./network.sh up createChannel -c mychannel -ca

echo "Pausing for 15 seconds to let the network stabilize..."
sleep 15

echo "Deploying chaincode..."
./network.sh deployCC -ccn basic -ccp ../chaincode/ -ccl go

echo "Fabric network is up and chaincode is deployed."