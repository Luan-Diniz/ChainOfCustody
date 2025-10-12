
import aiohttp, json

# Using the same URL as the ISSUER.
VERIFIER_AGENT_URL = "http://localhost:8080/cloud-agent"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


# --- PRESENTATION
async def create_presentation_request_anoncreds(connectionId: str, credential_definition_guid: str, level_required: int | str) -> tuple[str,str]:
    """
        level_required: is the authorization level required
        \t0: Restricted read only
        \t1: Read-Only
        \t2: Read and Write
        \t99: ADMIN


        Returns (THID, PRESENTATION_ID_ISSUER)
    """


    url = f"{VERIFIER_AGENT_URL}/present-proof/presentations"

    data = {
    "connectionId": connectionId,
    "credentialFormat": "AnonCreds",
    "anoncredPresentationRequest": {
        "name": "proof_of_expertise_and_authorization",
        "version": "1.0",
        "nonce": "1234567890123456789", # Should be random
        "requested_attributes": {
            "expert_name_proof": {
                "name": "expert_name",
                "restrictions": [{   # Url should be configurable
                    "cred_def_id": f"http://caddy-issuer:8080/cloud-agent/credential-definition-registry/definitions/{credential_definition_guid}/definition"
                }]
            },
            "evidence_hash_proof": {
                "name": "evidence_hash",
                "restrictions": [{
                    "cred_def_id": f"http://caddy-issuer:8080/cloud-agent/credential-definition-registry/definitions/{credential_definition_guid}/definition"
                }]
            },
            "subject_did_proof": {
                "name": "subject_did",
                "restrictions": [{
                    "cred_def_id": f"http://caddy-issuer:8080/cloud-agent/credential-definition-registry/definitions/{credential_definition_guid}/definition"
                }]
            }
        },
        "requested_predicates": {
            "auth_level_proof": {
                "name": "authorization_level",
                "p_type": ">=",
                "p_value": int(level_required),
                "restrictions": [{
                    "cred_def_id": f"http://caddy-issuer:8080/cloud-agent/credential-definition-registry/definitions/{credential_definition_guid}/definition"
                }]
            }
        }
    },
    "proofs": [],
    "options": None
}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            result = await response.json()
            return result["thid"], result["presentationId"]


async def accept_presentation(presentationId: str):
    url = f"{VERIFIER_AGENT_URL}/present-proof/presentations/{presentationId}"
    data = {
        "action": "presentation-accept"
      }
    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=data) as response:
            response.raise_for_status()
            result = await response.json()
            print(json.dumps(result, indent=2))

async def get_verified_data(presentationId: str):
    url = f"{VERIFIER_AGENT_URL}/present-proof/presentations/{presentationId}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            result = await response.json()
            return result["data"]
            #print(json.dumps(result, indent=2))