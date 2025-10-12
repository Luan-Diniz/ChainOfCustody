# ChainOfCustody
Chain of Custody PoC using Hyperledger Fabric with access control by Hyperledger Identus.


# How to Run:
## Sets up Fabric network and gateway app:
    From root project folder at terminal 1:
    cd FabricChainofCustody
    ./run.sh


## Sets up SSI-App services:
    From root project folder at terminal 2:
    cd SSI-App
    ./start_services.sh 

## Holder interface
    From root project folder at terminal 3:
    cd SSI-App
    python3 holder/holder_interface.py

## Issuer interface
    From root project folder at terminal 4:
    cd SSI-App
    python3 issuer/issuer_interface.py

# Demo:
    1. Start all services described above.
    2. Create a DID as Holder.
    3. Create a DID, Schema and Credential Definition as Issuer.
    4. As Issuer, establish an connection with the Holder.
    5. As Issuer, issue an Anoncreds Credential to the Holder.
    6. Now the Holder can create evidences and perform other operations using
    the Chain of Custody App.

# ToDo:  -python requirements and add link to fabrics requisites.