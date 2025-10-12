from holder_controller import *
import asyncio
import json

async def main():
    URL_DB = 'http://localhost:49152'
    URL_COC= 'http://localhost:3000'
    headers = {"Content-Type": "application/json"}

    didRef = ""
    name = ""

    while True:
        name = input("(LogIn) Digite seu nome completo:\n")  
        url = f"{URL_DB}/identities/{name}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    identity_data = await response.json()
                    didRef = identity_data["current_did"]
                    print("Seu DID atual:", didRef)
                elif response.status == 404:
                    print(f"Atenção! Nome não registrado no banco de dados.")
                    print("Crie um DID!")
                else:
                    print(f"An error occurred. Status: {response.status}")


        
        user_input = input("""Selecione:
                            \t1. Criar DID.
                            \t2. Operação no Sistema de Cadeia de Custódia
                            \t0. Sair\n""")
        
        
        if user_input == '1':
            longFormDid = await create_did()
            didRef = await publish_did(longFormDid)

            print(f'DID criado: {didRef}')
            url = f"{URL_DB}/identities"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={"name":name, "did":didRef}) as response:
                    if response.status == 201:
                        await response.json()
                        print(f"DID atualizado no sistema.")
                    else:
                        error_text = await response.text()
                        print(f"Error happened: {error_text}")

        elif user_input == '2':
            if didRef=="":
                print('Crie um DID antes! E tenha uma credencial para acesso!')
                continue 
            user_input = input("""Selecione:
                    \t1. Criar Evidência.
                    \t2. Atualizar Evidência.
                    \t3. Consulta metadados Cadeia de Custódia
                    \t4. Verificar Cadeia de Custódia e obter payloads
                    \t5. Mudar owner Cadeia de Custódia
                    \t0. Sair\n""") 
            if user_input == '1': 
                tags_input = input('Digite tags (separadas por vírgula) se desejar, ou aperte enter: ')
                tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
                evidence_hash = input('Digite o hash da evidência: ')
                print("Responda...")
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
                    "owner_did" : didRef,
                    "evidence_hash" : evidence_hash,
                    "evidence_record" : evidence_record,
                    "tags": tags
                }

                url = f"{URL_COC}/create-evidence"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 201:
                            response_data = await response.json()
                            print(f"CreateEvidence response: {response_data}")
                        else:
                            error_text = await response.text()
                            print(f"Error happened: {error_text}")

            elif user_input == '2':
                tags_input = input('Digite tags (separadas por vírgula) se desejar, ou aperte enter: ')
                tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
                evidence_hash = input('Digite o hash da evidência: ')
                print("Responda...")
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
                    "owner_did" : didRef,
                    "evidence_hash" : evidence_hash,
                    "new_evidence_record" : new_evidence_record,
                    "tags": tags
                }

                url = f"{URL_COC}/update-evidence"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            print(f"UpdateEvidence response: {response_data}")
                        else:
                            error_text = await response.text()
                            print(f"Error happened: {error_text}")



            elif user_input == '3': 
                evidence_hash = input('Digite o hash da evidência: ')
                data = {
                    "owner_did" : didRef,
                    "evidence_hash" : evidence_hash,
                }
                url = f"{URL_COC}/chain-of-custody"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            
                            print(f"Chain of Custody Metadata: ")
                            print("\n--- INÍCIO DA CADEIA DE CUSTÓDIA ---")
                            for index, link in enumerate(response_data):
                                print(f"\n------------------ Elo {index + 1} ------------------")
                                print("\n[+] Registro do Banco de Dados:")
                                print(json.dumps(link.get('databaseRecord', {}), indent=2))
                                print("\n[+] Dados do Ledger (Blockchain):")
                                print(json.dumps(link.get('ledgerData', {}), indent=2))
                            print("\n------------------ FIM DA CADEIA ------------------\n")
                        else:
                            error_text = await response.text()
                            print(f"Error happened: {error_text}")




            elif user_input == '4':
                evidence_hash = input('Digite o hash da evidência: ')
                data = {
                    "owner_did" : didRef,
                    "evidence_hash" : evidence_hash,
                }
                url = f"{URL_COC}/verify-chain-of-custody"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            
                            print(f"Chain of Custody Payloads: ")
                            print(f"----- INÍCIO PAYLOADS -----")
                            print(json.dumps(response_data, indent=2))
                            print(f"----- FIM PAYLOADS -----")
                        else:
                            error_text = await response.text()
                            print(f"Error happened: {error_text}")


            elif user_input == '5':
                evidence_hash = input('Digite o hash da evidência: ')
                new_owner_did = input("Digite o did do novo 'dono' da evidência: ")
                data = {
                    "evidence_hash" : evidence_hash,
                    "current_owner_did": didRef,
                    "new_owner_did": new_owner_did
                }

                url = f"{URL_COC}/transfer-ownership"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            response_data = await response.json()
                            
                            print(f"Transfer Ownership response: {response_data}")
                        else:
                            error_text = await response.text()
                            print(f"Error happened: {error_text}")
            else:
                break



        else:
            print("Saindo do programa...")
            break



if __name__ == "__main__":
    asyncio.run(main())

