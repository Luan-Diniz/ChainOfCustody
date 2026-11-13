import sys
from pathlib import Path

# Add parent directory to sys.path so i18n can be imported regardless of execution directory
sys.path.append(str(Path(__file__).resolve().parent.parent))

from holder_controller import *
import asyncio
import json
from i18n import t

async def main():
    URL_DB = 'http://localhost:49152'
    URL_COC = 'http://localhost:3000'
    headers = {"Content-Type": "application/json"}

    didRef = ""
    name = ""

    while True:
        name = input(t("holder_login_prompt"))
        url = f"{URL_DB}/identities/{name}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    identity_data = await response.json()
                    didRef = identity_data["current_did"]
                    print(t("holder_current_did", did=didRef))
                elif response.status == 404:
                    print(t("holder_name_not_registered"))
                    print(t("holder_create_a_did"))
                else:
                    print(t("error_status", status=response.status))

        user_input = input(t("holder_main_menu"))
        
        if user_input == '1':
            longFormDid = await create_did()
            didRef = await publish_did(longFormDid)

            print(t("did_created", did=didRef))
            url = f"{URL_DB}/identities"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={"name": name, "did": didRef}) as response:
                    if response.status == 201:
                        await response.json()
                        print(t("holder_did_updated"))
                    else:
                        error_text = await response.text()
                        print(t("error_happened", error=error_text))

        elif user_input == '2':
            if didRef == "":
                print(t("holder_need_did_and_cred"))
                continue 
            user_input = input(t("holder_coc_menu"))
            if user_input == '1': 
                tags_input = input(t("prompt_tags"))
                tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
                evidence_hash = input(t("prompt_evidence_hash"))
                print(t("prompt_answer_questions"))
                what = input("What? ")
                who = input("Who? ")
                where = input("Where? ")
                when = input("When? ")
                why = input("Why? ")
                how = input("How? ")

                evidence_record = {
                    "what": what,
                    "who": who,
                    "where": where,
                    "when": when,
                    "why": why,
                    "how": how
                }

                data = {
                    "owner_did": didRef,
                    "evidence_hash": evidence_hash,
                    "evidence_record": evidence_record,
                    "tags": tags
                }

                url = f"{URL_COC}/create-evidence"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 201:
                            response_data = await response.json()
                            print(t("create_evidence_response", response=response_data))
                        else:
                            error_text = await response.text()
                            print(t("error_happened", error=error_text))

            elif user_input == '2':
                tags_input = input(t("prompt_tags"))
                tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
                evidence_hash = input(t("prompt_evidence_hash"))
                print(t("prompt_answer_questions"))
                what = input("What? ")
                who = input("Who? ")
                where = input("Where? ")
                when = input("When? ")
                why = input("Why? ")
                how = input("How? ")

                new_evidence_record = {
                    "what": what,
                    "who": who,
                    "where": where,
                    "when": when,
                    "why": why,
                    "how": how
                }

                data = {
                    "owner_did": didRef,
                    "evidence_hash": evidence_hash,
                    "new_evidence_record": new_evidence_record,
                    "tags": tags
                }

                url = f"{URL_COC}/update-evidence"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            print(t("update_evidence_response", response=response_data))
                        else:
                            error_text = await response.text()
                            print(t("error_happened", error=error_text))

            elif user_input == '3': 
                evidence_hash = input(t("prompt_evidence_hash"))
                data = {
                    "owner_did": didRef,
                    "evidence_hash": evidence_hash,
                }
                url = f"{URL_COC}/chain-of-custody"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            
                            print(t("chain_metadata_header"))
                            print(t("chain_start"))
                            for index, link in enumerate(response_data):
                                print(t("chain_link", link_num=index + 1))
                                print(t("chain_db_record"))
                                print(json.dumps(link.get('databaseRecord', {}), indent=2))
                                print(t("chain_ledger_data"))
                                print(json.dumps(link.get('ledgerData', {}), indent=2))
                            print(t("chain_end"))
                        else:
                            error_text = await response.text()
                            print(t("error_happened", error=error_text))

            elif user_input == '4':
                evidence_hash = input(t("prompt_evidence_hash"))
                data = {
                    "owner_did": didRef,
                    "evidence_hash": evidence_hash,
                }
                url = f"{URL_COC}/verify-chain-of-custody"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            
                            print(t("chain_payloads_header"))
                            print(t("payloads_start"))
                            print(json.dumps(response_data, indent=2))
                            print(t("payloads_end"))
                        else:
                            error_text = await response.text()
                            print(t("error_happened", error=error_text))

            elif user_input == '5':
                evidence_hash = input(t("prompt_evidence_hash"))
                new_owner_did = input(t("prompt_new_owner_did"))
                data = {
                    "evidence_hash": evidence_hash,
                    "current_owner_did": didRef,
                    "new_owner_did": new_owner_did
                }

                url = f"{URL_COC}/transfer-ownership"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            print(t("transfer_ownership_response", response=response_data))
                        else:
                            error_text = await response.text()
                            print(t("error_happened", error=error_text))
            else:
                break

        else:
            print(t("exiting_program"))
            break

if __name__ == "__main__":
    asyncio.run(main())
