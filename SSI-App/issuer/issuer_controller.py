from issuer_util import extract_raw_invitation
from anoncreds_schema import anoncreds_schema
from credential_data import CredentialData
import aiohttp
import json

ISSUER_AGENT_URL = "http://localhost:8080/cloud-agent"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- DID ---
async def create_did(id: str = "auth-1", purpose: str = "authentication", curve: str = "secp256k1") -> str:
    """
    Returns a longFormDid which is used to publish a DID in the blockchain.
    """
    url = f"{ISSUER_AGENT_URL}/did-registrar/dids"
    data = {
        "documentTemplate": {
            "publicKeys": [
                {"id": id, "purpose": purpose, "curve": curve}
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
    url = f"{ISSUER_AGENT_URL}/did-registrar/dids/{long_form_did}/publications"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            response.raise_for_status()
            result = await response.json()
            return result['scheduledOperation']['didRef']


# --- DIDCOMM CONNECTION
async def create_connection(new_connection_label: str) -> tuple[str, str]:
    """
    Returns the raw invitation and the connection id in the form
    (raw_invitation, connection_id).
    """
    url = f'{ISSUER_AGENT_URL}/connections'
    data = {"label": new_connection_label}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            result = await response.json()
            
            invitation_url = result['invitation']['invitationUrl']
            raw_invitation = extract_raw_invitation(invitation_url)
            connection_id = result['connectionId']

            return (raw_invitation, connection_id)



# --- SCHEMA
async def create_anoncreds_schema(author_did: str) -> str:
    """
    AnoncredSchemaV1\n
    Returns the GUID of the newly created schema.
    """
    url = f"{ISSUER_AGENT_URL}/schema-registry/schemas"

    anoncreds_schema["author"] = author_did
    anoncreds_schema["schema"]["issuerId"] = author_did

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=anoncreds_schema) as response:
            response.raise_for_status()
            result = await response.json()
            return result["guid"]


# --- CREDENTIAL DEFINITION
async def create_credential_definition(
        schema_guid: str, author_did: str,
        schemaRegistryURL: str = "http://caddy-issuer:8080/cloud-agent/") -> str: 
    """
    Returns the GUID from the newly created Credential Definition.
    """

    url = f"{ISSUER_AGENT_URL}/credential-definition-registry/definitions"
    data = {
        "name": "Forensic Evidence Credential Definition",
        "description": "Credential Definition for a forensic evidence certificate, linking an expert to a piece of evidence.",
        "version": "1.0.0",
        "tag": "forensic-evidence",
        "author": author_did,
        "schemaId": f"{schemaRegistryURL}/schema-registry/schemas/{schema_guid}/schema",
        "signatureType": "CL",
        "supportRevocation": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            result = await response.json()
            return result["guid"]
        

# --- CREDENTIAL
async def create_credential_offer_anoncreds(
        issuer_did: str, connection_id: str, credential_definition_id: str,
        credential_data: CredentialData, validity_period_in_seconds: float = 3600.0
        ) -> tuple[str, str]:
    """
        Returns the THID of the credential offer and the Issuer Record Id, in the format
        (thid, issuer_record_id).
    """

    # Change data from tutorial to suit my anoncreds schema data.
    url = f"{ISSUER_AGENT_URL}/issue-credentials/credential-offers"

    data = {
        "connectionId": connection_id,
        "credentialFormat": "AnonCreds",
        "anoncredsVcPropertiesV1": {
            "claims": {
                "expert_name": credential_data.expert_name,
                "issuing_judge_id": credential_data.issuing_judge_id,
                "evidence_hash": credential_data.evidence_hash,
                "authorization_level": credential_data.authorization_level,
                "court_jurisdiction" : credential_data.court_jurisdiction,
                "subject_did" : credential_data.subject_did
            },
            "issuingDID": issuer_did,
            "credentialDefinitionId": credential_definition_id,
            "validityPeriod": validity_period_in_seconds
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            result = await response.json()
            return result["thid"]
