import { createGatewayConnection, channelName, chaincodeName } from './connect';
import { createIssuer, createCredentialId} from './util';
import { DatabaseHandler, CustodyCredentialRecord } from './database-handler';
import { create_evidence, transfer_evidence_ownership,
        update_evidence, verify_chain_of_custody, get_chain_of_custody, 
        get_credential_id_by_evidence_hash, readAssetByID,
        } from './logic'
//simport { log } from 'console';


async function main(): Promise<void> {

    // Establish the connection with the gateway and retrieve client and gateway objects.
    const { gateway, client } = await createGatewayConnection();

    const EVIDENCE_HASH = 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2';
    const OWNER_DID = 'did:example:owner';
    const OWNER2_DID = 'did:example:owner2';
    const uri = 'mongodb://root:password@localhost:27017/?authSource=admin';
    const dbHandler = new DatabaseHandler(uri);

    const {issuer} = await createIssuer();

    const credentialId = await createCredentialId();



    const my_subject = {
            id: credentialId,
            evidence_hash: EVIDENCE_HASH,
            previous_credential_id: null,
            evidence_record: {
                what: "Um HD externo de uma marca genérica, modelo Exemplo-A, capacidade de 1TB, S/N: XYZ-12345, cor preta. O dispositivo foi encontrado conectado a um notebook.",
                who: "Coletado pelo Perito Criminal (Matrícula 12345-X), na presença de testemunhas instrumentais, conforme termo de coleta.",
                where: "Em um escritório comercial localizado na Avenida Principal, 1000, Sala 50, Centro, Cidade Exemplo - UF.",
                when: "Apreendido no dia 10 de janeiro de 2025, por volta das 14:30 (horário local), durante um procedimento de busca autorizada.",
                why: "Para ser submetido à análise forense digital como parte de uma investigação criminal, pois suspeita-se que o dispositivo possa conter dados de interesse para o caso.",
                how: "O dispositivo foi desconectado seguindo os procedimentos operacionais padrão, fotografado, acondicionado em embalagem apropriada e lacrado com o lacre de segurança número 2025-ABC-001. O processo foi registrado no formulário de cadeia de custódia."
            }
        };

    const RecordData: Omit<CustodyCredentialRecord, '_id'> = {
                evidencehash: "",    // Will be copied from the credential.
                credentialId: credentialId,
                vcJwt: "",
                previousCredentialId: null,
                last_modifier_did: "",
                sequence: null,
                status: "active",
                issuerDid: issuer.did,
                ownerDid: OWNER_DID,
                createdAt: new Date(),
                tags: ["coleta", "hd_externo", "caso_157-2025"]
    };

    await dbHandler.connect();

    try {
        // Get a network instance representing the channel where the smart contract is deployed.
        const network = gateway.getNetwork(channelName);

        // Retrieve the smart contract from the network.
        const contract = network.getContract(chaincodeName);

        // *************** DEMO ***********************
        await create_evidence(my_subject, issuer,  dbHandler, RecordData, contract);
        await readAssetByID(contract, credentialId);
        //console.log(await dbHandler.findRecordByCredentialId(credentialId));

        await transfer_evidence_ownership(credentialId, OWNER2_DID, dbHandler, contract);
        await readAssetByID(contract, credentialId);

        //console.log(await dbHandler.findRecordByCredentialId(credentialId));
        
        // Creating another credential for testing update.
        const newcredentialId = await createCredentialId();
        const new_my_subject = {
            id: newcredentialId,
            evidence_hash: EVIDENCE_HASH,
            previous_credential_id: null,
            evidence_record: {
                what: "Novo what.",
                who: "Novo who.",
                where: "Novo where.",
                when: "Novo when.",
                why: "Novo why.",
                how: "Novo how."
            }
        };
        const newRecordData: Omit<CustodyCredentialRecord, '_id'> = {
                    evidencehash: EVIDENCE_HASH,
                    credentialId: newcredentialId,
                    vcJwt: "",
                    previousCredentialId: null,
                    last_modifier_did: "",
                    sequence: null,
                    status: "active",
                    issuerDid: issuer.did,
                    ownerDid: OWNER_DID,
                    createdAt: new Date(),
                    tags: ["coleta", "hd_externo", "caso_157-2025"]
        };
        const old_credential_did = credentialId;
        await update_evidence(old_credential_did, new_my_subject, issuer, dbHandler, newRecordData, contract);

        const actual_credential_id = await get_credential_id_by_evidence_hash(EVIDENCE_HASH ,dbHandler);
        if (actual_credential_id){
            const chain_of_custody = await get_chain_of_custody(actual_credential_id, dbHandler, contract);

            // ********************************* PRINT CHAIN OF CUSTODY ******************************************
            console.log("\n--- INÍCIO DA CADEIA DE CUSTÓDIA ---");
            // Itera sobre cada elo da cadeia
            chain_of_custody.forEach((link, index) => {
                console.log(`\n------------------ Elo ${index + 1} ------------------`);
                // Imprime o registro do banco de dados de forma legível
                console.log("\n[+] Registro do Banco de Dados:");
                console.log(JSON.stringify(link.databaseRecord, null, 2));
                // Imprime os dados do ledger de forma legível
                console.log("\n[+] Dados do Ledger (Blockchain):");
                console.log(JSON.stringify(link.ledgerData, null, 2));
            });
            console.log("\n------------------ FIM DA CADEIA ------------------\n");


            const payload = await verify_chain_of_custody(chain_of_custody);
            // Pegar vcJWT e decodificar.
            console.log("\n ----------------- PAYLOADS ------------------------")
            console.log(JSON.stringify(payload, null, 2));
            console.log("\n ----------------- FIM DOS PAYLOADS ------------------------")
        }        
        
    } finally {
        // Close the connection with the gateway and gRPC client.
        await dbHandler.disconnect();
        gateway.close();
        client.close();
    }

}

main().catch((error: unknown) => {
    console.error('******** FAILED to run the application:', error);
    process.exitCode = 1;
});
