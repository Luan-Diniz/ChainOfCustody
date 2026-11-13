import sys
from pathlib import Path

# Add parent directory to sys.path so i18n can be imported regardless of execution directory
sys.path.append(str(Path(__file__).resolve().parent.parent))

from issuer_controller import *
import asyncio
import aiohttp
from local_database import init_db, add_connection, get_connection
from i18n import t

async def main():
    # Initializes local database
    # it stores (connection_id, name, subject_did)
    await init_db()

    # Representing an OOB way to accept the connection invite.
    URL_DB = 'http://localhost:49152'
    HOLDER_API_URL = "http://localhost:5001"  
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    didRef = ""
    schema_guid = ""
    credential_definition_guid = ""
    connection_id = None

    while True:
        user_input = input(t("issuer_main_menu"))
        
        if user_input == '1':
            longFormDid = await create_did()
            didRef = await publish_did(longFormDid)
            print(t("did_created", did=didRef))
            url = f"{URL_DB}/trusted-issuers/{didRef}"
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        print(t("issuer_did_trusted"))
                    else:
                        error_text = await response.text()
                        print(t("error_happened", error=error_text))

            schema_guid = await create_anoncreds_schema(didRef)
            print(t("schema_created", schema=schema_guid))
            credential_definition_guid = await create_credential_definition(schema_guid, didRef)
            print(t("cred_def_created", cred_def=credential_definition_guid))

        elif user_input == '2':
            print(t("issuer_connection_intro"))
            # UNSAFE! It can suffer an injection attack.
            name = input(t("issuer_prompt_expert_name"))
            url = f"{URL_DB}/identities/{name}"
            identity_data = None
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        identity_data = await response.json()
                        print(t("issuer_identity_found", name=name))
                        print(t("issuer_identity_data", data=identity_data))
                    elif response.status == 404:
                        print(t("issuer_identity_not_found", name=name))
                    else:
                        print(t("error_status", status=response.status))
            if not identity_data:
                continue

            connection_label = input(t("issuer_prompt_connection_label"))
            raw_invitation, connection_id = await create_connection(connection_label)
            # Save this information in a local database, so the webhookhandler has access to it as well.
            await add_connection(connection_id, name, identity_data["current_did"])

            url = f"{URL_DB}/credential-definition"
            data = {"credential_def_guid": credential_definition_guid,
                    "connectionId": connection_id}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    print(t("mockdb_response_status", status=response.status))

            url = f"{HOLDER_API_URL}/receive_oob_invitation"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={"raw_invitation": raw_invitation}) as response:
                    print(t("invitation_sent_holder_status", status=response.status))
 
        elif user_input == '3':
            print(t("issuer_ensure_invitation_accepted"))
            # Should trim inputs
            validity_in_seconds = input(t("issuer_prompt_validity"))
            evidence_hash = input(t("issuer_prompt_evidence_hash"))
            court_jurisdiction = input(t("issuer_prompt_jurisdiction"))
            issuing_judge_id = input(t("issuer_prompt_judge_id"))
            print(t("access_levels_description"))
            authorization_level = input(t("issuer_prompt_auth_level"))

            name, did = await get_connection(connection_id)

            credential_data = CredentialData(
                expert_name=name, issuing_judge_id=issuing_judge_id,
                evidence_hash=evidence_hash, authorization_level=authorization_level,
                court_jurisdiction=court_jurisdiction, subject_did=did
            )

            offer_thid = await create_credential_offer_anoncreds(
                issuer_did=didRef, connection_id=connection_id,
                credential_definition_id=credential_definition_guid,
                credential_data=credential_data,
                validity_period_in_seconds=validity_in_seconds
            )
            # Notify holder. 
            url = f"{HOLDER_API_URL}/receive_credential_offer"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={"thid": offer_thid}) as response:
                    response_data = await response.json()
                    print(t("offer_sent_holder_response", response=response_data))

        else:
            print(t("exiting_program"))
            break

if __name__ == "__main__":
    asyncio.run(main())
