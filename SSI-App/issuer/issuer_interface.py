from issuer_controller import *
import asyncio
import aiohttp
from local_database import init_db, add_connection, get_connection

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
    connection_id=None

    while True:
        user_input = input("""Selecione:
                            \t1. Criar DID, Schema e Credential Definition.
                            \t2. Criar conexão e enviar para Holder.  
                            \t3. Assinar Credencial
                            \t0. Sair\n""")
        
        if user_input == '1':
            longFormDid = await create_did()
            didRef = await publish_did(longFormDid)
            print(f'DID criado: {didRef}')
            url = f"{URL_DB}/trusted-issuers/{didRef}"
            async with aiohttp.ClientSession() as session:
                async with session.post(url) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        print(f"DID adicionado à lista de Issuers confiáveis!")
                    else:
                        error_text = await response.text()
                        print(f"   Error happened: {error_text}")

            schema_guid = await create_anoncreds_schema(didRef)
            print(f'Schema criado: {schema_guid}')
            credential_definition_guid = await create_credential_definition(schema_guid, didRef)
            print(f'Credential Definition criado: {credential_definition_guid}')


        elif user_input == '2':
            print("Para que a conexão prossiga e a credencial seja gerada responda...")
            # UNSAFE! It can suffer an injection attack.
            name = input("Qual o nome completo do perito que receberá a credencial? \n")
            url = f"{URL_DB}/identities/{name}"
            identity_data = None
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        identity_data = await response.json()
                        print(f"Sucesso! A identidade de '{name}' foi encontrada.")
                        print("   Dados:", identity_data)
                    elif response.status == 404:
                        print(f"A identidade '{name}' não foi encontrada no banco de dados. \
                                O perito precisa cadastrar um DID!")
                    else:
                        print(f"Error happened. Status: {response.status}") 
            if not identity_data:
                continue

            connection_label = input("Dê um rótulo para esta nova conexão: ")
            raw_invitation, connection_id = await create_connection(connection_label)
            # Save this information in a local database, so the webhookhandler has access to it as well.
            await add_connection(connection_id, name, identity_data["current_did"])

            url = f"{URL_DB}/credential-definition"
            data = {"credential_def_guid": credential_definition_guid,
                    "connectionId": connection_id}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    print(f"MockDB responded with status: {response.status}")

            url = f"{HOLDER_API_URL}/receive_oob_invitation"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={"raw_invitation": raw_invitation}) as response:
                    print(f"Invitation sent. Holder agent responded with status: {response.status}")
 
        elif user_input == '3':
            print('Esteja certo de que o perito aceitou sua solicitação.')
            #Should trim inputs
            validity_in_seconds = input('Qual será o tempo de validade da credencial gerada (em segundos)? ')
            evidence_hash = input('Qual o hash da evidência digital? ')
            court_jurisdiction = input('Digite a jurisdição do tribunal (ex: Comarca de Florianópolis, 4ª Vara Federal): ')
            issuing_judge_id = input('Qual seu identificador (id)? ')
            print(""" Níveis de Acesso 
                  \t0 (Restricted Read-only): Apenas alguns dados e metadados poderão ser lidos.
                  \t1 (Read-Only): Todos os dados da cadeia de custódia poderão ser visualizados
                  \t2 (Read and Write): Tem acesso à cadeia de custódia e pode adicionar dados.
                  \t99 (ADMIN): Acesso total para modificações, apenas deve ser usados em casos extremos.
                                (Como para transferir a custódia de uma evidência de um perito que não está mais elegível 
                                a utilizar este ecossistema a outro.)
                  """)
            authorization_level = input('Qual o nível de acesso o perito terá à evidência (digite somente um número)? ')

            name, did = await get_connection(connection_id)


            credential_data = CredentialData(
                expert_name=name,issuing_judge_id=issuing_judge_id,
                evidence_hash=evidence_hash, authorization_level=authorization_level,
                court_jurisdiction=court_jurisdiction, subject_did=did
            )

            offer_thid = await create_credential_offer_anoncreds(
                            issuer_did=didRef, connection_id=connection_id,
                            credential_definition_id= credential_definition_guid,
                            credential_data=credential_data,
                            validity_period_in_seconds=validity_in_seconds
                        )
            # Notify holder. 
            url = f"{HOLDER_API_URL}/receive_credential_offer"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json={"thid": offer_thid}) as response:
                    response_data = await response.json()
                    print(f"Invitation sent. Holder agent responded with: {response_data}")

        else:
            print("Saindo do programa...")
            break

if __name__ == "__main__":
    asyncio.run(main())