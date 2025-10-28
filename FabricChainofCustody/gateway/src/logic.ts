import { Contract } from '@hyperledger/fabric-gateway';
import { createHash } from 'crypto';
import { createCredential, CredentialSubjectData, verifyCreatedCredential } from './vc-handler';
import type { Issuer, VerifiedCredential } from 'did-jwt-vc' with { 'resolution-mode': 'import' };

import { DatabaseHandler, CustodyCredentialRecord } from './database-handler';

const utf8Decoder = new TextDecoder();


export async function create_evidence(
                subject_data: CredentialSubjectData, issuer: Issuer,
                dbHandler: DatabaseHandler, RecordData: CustodyCredentialRecord, contract: Contract): Promise<string> {

        // Creates credential and store in database.
        const vcJwt = await createCredential(subject_data, issuer);
        RecordData.vcJwt = vcJwt;
        RecordData.last_modifier_did = RecordData.ownerDid;
        RecordData.sequence = 1;
        RecordData.evidencehash = subject_data.evidence_hash;

        await dbHandler.createRecord(RecordData);

        const credentialHash = createHash('sha256').update(vcJwt).digest('hex');
        // Stores some data in blockchain.
        await createAsset(contract, RecordData.credentialId, RecordData.ownerDid, RecordData.issuerDid, credentialHash);

        return RecordData.credentialId;
}

export async function transfer_evidence_ownership(
    credential_id: string, new_owner_did: string,
    dbHandler: DatabaseHandler, contract: Contract): Promise<void> {
    // Change owner --> in blockchain data and db data.
    // Changes owner, but not the "last_modifier_did" field
    await dbHandler.updateRecordOwner(credential_id, new_owner_did);

    // blockchain operation
    await transferOwnership(contract, credential_id, new_owner_did);
}

export async function update_evidence(old_credential_did: string,
                subject_data: CredentialSubjectData, issuer: Issuer,
                dbHandler: DatabaseHandler, newRecordData: CustodyCredentialRecord,
                contract: Contract): Promise<void> 
{ 
    const credential_record = await dbHandler.findRecordByCredentialId(old_credential_did);
    if (credential_record?.sequence) {
        // Calculates sequence number
        newRecordData.sequence = credential_record.sequence + 1;
    }


    // Creates new credential.
    const vcJwt = await createCredential(subject_data, issuer);
    newRecordData.vcJwt = vcJwt;
    newRecordData.evidencehash = subject_data.evidence_hash;
    newRecordData.last_modifier_did = newRecordData.ownerDid;
    newRecordData.previousCredentialId = old_credential_did;


    await dbHandler.createRecord(newRecordData);

    const credentialHash = createHash('sha256').update(vcJwt).digest('hex');
    // Stores data of the new credential in blockchain.
    await createAsset(contract, newRecordData.credentialId, newRecordData.ownerDid,
                        newRecordData.issuerDid, credentialHash
                    );

    // Change status of old credential in database
    await dbHandler.updateRecordStatus(old_credential_did, "revoked");
    
    // Change status of old credential in blockchain.
    await revokeAsset(contract, old_credential_did);
}

/**
 * Retrieves the entire chain of custody for a given credential ID.
 * It traverses the credential history by recursively looking up the previous credential ID.
 * @param {string} credential_id The starting credential ID.
 * @param {DatabaseHandler} dbHandler An instance of the database handler to fetch credential records.
 * @param {Contract} contract The contract instance to interact with the ledger.
 * @returns {Promise<Array<{databaseRecord: CustodyCredentialRecord, ledgerData: Asset}>>} A promise that resolves with a list of tuples, 
 * where each tuple contains the typed database record and the corresponding typed ledger data.
 */
export async function get_chain_of_custody(credential_id: string, dbHandler: DatabaseHandler, contract: Contract):
    Promise<Array<{databaseRecord: CustodyCredentialRecord, ledgerData: Asset}>> {
    // This list will store the combined data from the database and the ledger.
    const chainOfCustody: Array<{databaseRecord: CustodyCredentialRecord, ledgerData: Asset}> = [];
    
    // Start with the initial credential ID provided.
    let current_cred_id: string | null = credential_id;
    
    do {
        // Fetch the record from your local database.
        const cred_record = await dbHandler.findRecordByCredentialId(current_cred_id) as CustodyCredentialRecord;
        
        // Fetch the corresponding asset data from the ledger
        const ledger_data = await readAssetByID(contract, current_cred_id);
        
        // Store the combined results as an object in our list.
        chainOfCustody.push({ 
            databaseRecord: cred_record, 
            ledgerData: ledger_data 
        });
        
        // Check if a previous credential exists to continue the chain.
        if (cred_record && cred_record.previousCredentialId) {
            current_cred_id = cred_record.previousCredentialId;
        } else if (cred_record) {
            // If there's a record but no previous ID, the chain ends here.
            current_cred_id = null;
        } 
        else {
            // If no record is found at all, the chain is broken.
            throw new Error(`The chain of custody is broken. Could not find a record for credential ID: ${current_cred_id}`);
        }
    
    } while (current_cred_id);

    // Return the complete list of records.
    return chainOfCustody;
}

 export async function verify_chain_of_custody(
        chain_of_custody: Array<{databaseRecord: CustodyCredentialRecord, ledgerData: Asset}>
    ) : Promise<Array<VerifiedCredential>> {

    let payloads: Array<VerifiedCredential> = [];
    for (const [index, link] of chain_of_custody.entries()) {
        try {
            // Verify whether the credential hash matches the one stored in the ledger
            const calculatedHash = createHash('sha256').update(link.databaseRecord.vcJwt).digest('hex');

            if (link.ledgerData.credential_id !== link.databaseRecord.credentialId) {
                throw new Error(`Credentials id do not match at index ${index}.`);
            }

            if (calculatedHash !== link.ledgerData.credential_hash) {
                // Throws a specific error if the hash does not match
                throw new Error(`Hash mismatch for credential at index ${index}.`);
            }

            // 2. Verify the authenticity and integrity of the JWT credential
            const verified_credential = await verifyCreatedCredential(link.databaseRecord.vcJwt);
            payloads.push(verified_credential);
            

        } catch (error: any) {
            // Capture verification errors either from hash either from credential.
            console.error(`Failed to verify credential ${index} in the chain of custody:`, error.message);
            throw error; 
        }
    }

    return payloads;
 }


export async function get_credential_id_by_evidence_hash(
    evidence_hash: string, dbHandler: DatabaseHandler) : Promise<string | null> {
    const credential_id = await dbHandler.findActiveCredentialByEvidenceHash(evidence_hash);
    
    return credential_id;
}





// --- SMART CONTRACT COMMUNICATION

interface Asset {
    status: string;
    timestamp: string;
    owner_did: string;
    issuer_did: string;
    credential_id: string;
    credential_hash: string;
    last_modifier_did: string;
}
/**
 * Create a new credential asset in blockchain
 * assetID is the credential ID (did)
 */
export async function createAsset(contract: Contract, assetID: string, owner_did: string,
     issuer_did: string, credential_hash: string): Promise<void> {
    //console.log('\n--> Submit Transaction: CreateAsset, creates a new credential');
    const status = 'active';
    const timestamp = new Date().toISOString();

    await contract.submitTransaction(
        'CreateAsset',
        assetID,
        status,
        issuer_did,
        owner_did,
        credential_hash,
        timestamp,
    );

    //console.log(`*** Credential ${assetID} successfully created`);
}

/**
 * Reads a credential by its ID from the ledger and returns it as a typed Asset object.
 * @param {Contract} contract The contract instance.
 * @param {string} assetId The ID of the asset to read.
 * @returns {Promise<Asset>} A promise that resolves with the typed asset object.
 */
export async function readAssetByID(contract: Contract, assetId: string): Promise<Asset> {

    // console.log(`\n--> Evaluate Transaction: ReadAsset for ID: ${assetId}`);
    const resultBytes = await contract.evaluateTransaction('ReadAsset', assetId);
    
    const resultJson = utf8Decoder.decode(resultBytes);
    // We cast the parsed JSON to our Asset interface to get type safety.
    const result = JSON.parse(resultJson) as Asset;
    
    return result;
}

/**
 * TransferOwnership
*/
export async function transferOwnership(contract: Contract, assetId: string, newOwnerDid: string): Promise<void> {
    //console.log('\n--> Submit Transaction: transferOwnership');
    await contract.submitTransaction('TransferOwnership', assetId, newOwnerDid);   
    //console.log(`*** Credential ${assetId} owner changed to ${newOwnerDid}`);
}

/**
 * Revoke an existing credential
*/
export async function revokeAsset(contract: Contract, assetId: string): Promise<void> {
    //console.log('\n--> Submit Transaction: RevokeAsset, changes status to revoked');
    await contract.submitTransaction('RevokeAsset', assetId);
    //console.log(`*** Credential ${assetId} successfully revoked`);
}