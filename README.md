# ChainOfCustody
Chain of Custody PoC using Hyperledger Fabric with access control by Hyperledger Identus.

Fabric repository: https://github.com/hyperledger/fabric 
Identus Cloud Agent repository: https://github.com/hyperledger-identus/cloud-agent 


# Prerequisits
## Hyperledger Fabric Prerequisits:
    https://hyperledger-fabric.readthedocs.io/en/latest/prereqs.html 
## Python
    At ./SSI-App/requirements.txt


# How to Run:
PS: Install the requirements.txt Python requirements before
running Holder and Issuer interfaces.
Using a virtual environment (venv) is advised.
``
pip install -r requirements.txt
``

## Sets up Fabric network and gateway app:
    From root project folder at terminal 1:
    cd FabricChainofCustody
    ./run.sh

## Sets up Identus Agents
    From root project folder at terminal 2:
    cd identus-agent-2.0.0/st-multi
    docker compose up -d

## Sets up SSI-App services:
    From root project folder at terminal 3:
    cd SSI-App
    ./start_services.sh 

## Holder interface
    From root project folder at terminal 4:
    cd SSI-App
    python3 holder/holder_interface.py

## Issuer interface
    From root project folder at terminal 5:
    cd SSI-App
    python3 issuer/issuer_interface.py

# Cleaning environment:
    At ./FabricChainofCustody there is a stop.sh.
    At ./cloud-agent-2.0.0/examples/st-multi run docker compose down -v 
    At ./SSI-App run ./stop_services.sh

# Demo:
    1. Start all services described above.
    2. Create a DID as Holder.
    3. Create a DID, Schema and Credential Definition as Issuer.
    4. As Issuer, establish an connection with the Holder.
    5. As Issuer, issue an Anoncreds Credential to the Holder.
    6. Now the Holder can create evidences and perform other operations using
    the Chain of Custody App.
