import aiohttp
import json

HOLDER_AGENT_URL = "http://localhost:8083/cloud-agent"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

async def create_did(id: str = "auth-1", purpose: str = "authentication", curve: str = "secp256k1") -> str:
    """
    Returns a longFormDid which is used to publish a DID in the blockchain.
    """
    url = f"{HOLDER_AGENT_URL}/did-registrar/dids"
    data = {
        "documentTemplate": {
            "publicKeys": [
                {
                    "id": id,
                    "purpose": purpose,
                    "curve": curve
                }
            ],
            "services": []
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            result = await response.json()
            return result['longFormDid']

async def publish_did(long_form_did: str) -> str:
    """
    Schedules an operation to publish the DID into the blockchain.
    Returns its shortened form.
    """
    url = f"{HOLDER_AGENT_URL}/did-registrar/dids/{long_form_did}/publications"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            response.raise_for_status()
            result = await response.json()
            return result['scheduledOperation']['didRef']

# --- Connection DIDCOMM---
async def accept_connection(raw_invitation: str):
    """
    Accepts a DIDComm connection invitation.
    """
    url = f"{HOLDER_AGENT_URL}/connection-invitations"
    data = {
        "invitation": raw_invitation
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            return await response.json() # Or another appropriate return value


# Credential
async def get_credential_records() -> list[dict["str", any]]:
    url = f"{HOLDER_AGENT_URL}/issue-credentials/records"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            response_data = await response.json()
            return response_data["contents"]

async def accept_credential_offer(thid: str):
    record_id=""
    credential_records = await get_credential_records()
    for credential_offer in credential_records:
        if credential_offer["thid"] == thid:
            record_id = credential_offer["recordId"]
            break
    
    url = f"{HOLDER_AGENT_URL}/issue-credentials/records/{record_id}/accept-offer"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json={}) as response:
            result = await response.json()
            return result


# --- PRESENTATION
async def retrieve_presentation_requests() -> list:
    url = f"{HOLDER_AGENT_URL}/present-proof/presentations/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            result = await response.json()
            return result["contents"]
        
async def accept_presentation_request(presentationthid: str, credential_offer_thid: str):
    # This searches wouldnt be necessary if I use a webhook for the holder as well
    presentation_requests = await retrieve_presentation_requests()
    presentation_id = ""
    for presentation_request in presentation_requests:
        if presentation_request["thid"] == presentationthid:
            presentation_id = presentation_request["presentationId"]
            break 
    
    credential_records = await get_credential_records()
    credential_record_id = ""
    for credential_record in credential_records:
        if credential_record["thid"] == credential_offer_thid:
            credential_record_id = credential_record["recordId"]
            break

    #ToDo: change that error
    if (presentation_id == ""):
        print('PRESENTATION ID IS BLANK')
        print(f"presentationid: {presentation_id} ; credentialrecordid: {credential_record_id}")
        raise Exception
    if (credential_record_id == ""):
        print('CREDENTIAL RECORD ID IS BLANK')
        print(f"presentationid: {presentation_id} ; credentialrecordid: {credential_record_id}")
        raise Exception
              
    url = f"{HOLDER_AGENT_URL}/present-proof/presentations/{presentation_id}"
    data = {
        "action": "request-accept",
        "anoncredPresentationRequest": {
            "credentialProofs": [
                {
                    "credential": f"{credential_record_id}",
                    "requestedAttribute": [
                        "expert_name_proof",
                        "evidence_hash_proof",
                        "subject_did_proof"
                    ],
                    "requestedPredicate": [
                        "auth_level_proof"
                    ]
                }
            ]
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=data) as response:
            response.raise_for_status()
            result = await response.json()
            print(json.dumps(result, indent=2))
            return
    