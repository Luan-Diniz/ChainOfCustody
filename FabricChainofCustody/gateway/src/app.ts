import express, { Request, Response } from 'express';
import axios from 'axios';
import { Contract } from '@hyperledger/fabric-gateway';
import { createGatewayConnection, channelName, chaincodeName } from './connect';
import { createIssuer, createCredentialId} from './util';
import { DatabaseHandler } from './database-handler';
import { pollForVerifiedData } from './get_verified_data';
import { create_evidence, get_chain_of_custody,
        get_credential_id_by_evidence_hash, verify_chain_of_custody,
        update_evidence, transfer_evidence_ownership } from './logic'; // We only need create_evidence for our first endpoint


const PORT = 3000;
const MONGO_URI = 'mongodb://root:password@localhost:27017/?authSource=admin';
const VERIFIER_API_URL = 'http://localhost:5017'

const identifier = '123'; // Simulates an identifier generation for a request

const app = express();
app.use(express.json()); // Middleware to parse incoming JSON request bodies

// Global variables that will be initialized once when the server starts.
let contract: Contract;
let dbHandler: DatabaseHandler;


// --- API ENDPOINTS
app.post('/create-evidence', async (req: Request, res: Response) => {
    try {
        console.log('Received request to create evidence...');

        const { evidence_hash, owner_did, tags, evidence_record } = req.body;

        if (!evidence_hash || !owner_did || !evidence_record) {
            // This path now sends a response but doesn't return the Response object.
            // The function ends here.
            res.status(400).json({ 
                error: 'Missing required fields: evidence_hash, owner_did, evidence_record' 
            });
            return;
        } else {
            const requiredKeys = ['what', 'who', 'where', 'when', 'why', 'how'];
            for (const key of requiredKeys) {
                // Check if the key is missing, not a string, or is an empty string
                if (!evidence_record[key] || typeof evidence_record[key] !== 'string' || evidence_record[key].trim() === '') {
                    res.status(400).json({ 
                        error: `Missing or invalid field in evidence_record: '${key}' must be a non-empty string.`
                    });
                    return;
                }
            }
            
            // Check if an evidence record with this hash already exists
            const existingCredentialId = await get_credential_id_by_evidence_hash(evidence_hash, dbHandler);
            if (existingCredentialId) {
                res.status(409).json({ 
                    error: 'Conflict: An evidence record with this hash already exists.',
                    credentialId: existingCredentialId
                });
                return;
            }
            
            
            // --- Fetch Credential Definition ---
            console.log('Fetching credential definition...');
            const credDefResponse = await axios.get('http://localhost:49152/credential-definition');
            const { credential_guid, connectionId } = credDefResponse.data;

            // --- Request Presentation ---
            console.log(`Requesting presentation with identifier: ${identifier}`);
            await axios.post(`${VERIFIER_API_URL}/presentation_request`, {
                connection_id: connectionId,
                cred_def_guid: credential_guid,
                level_required: 2,
                id_database: identifier
            });

            // --- Poll for Verified Data ---
            const verified_data = await pollForVerifiedData(identifier);
            console.log(verified_data['requested_proof']['revealed_attrs']);

            const subject_did = verified_data['requested_proof']['revealed_attrs']['subject_did_proof']['raw']
            const expert_name = verified_data['requested_proof']['revealed_attrs']['expert_name_proof']['raw']
            console.log(expert_name)
            const evidence_hash_cred = verified_data['requested_proof']['revealed_attrs']['evidence_hash_proof']['raw']

            if (owner_did !== subject_did) {
                    res.status(400).json({ 
                        error: `Invalid DIDs!`
                    });
                    return;
            }
        
            if (evidence_hash !== evidence_hash_cred) {
                    res.status(400).json({ 
                        error: "Invalid evidence hash!"
                    });
                    return;
            }
        

            // This is the main execution path if validation passes.
            const { issuer } = await createIssuer();
            const credentialId = await createCredentialId();

            const subjectData = {
                id: credentialId,
                evidence_hash: evidence_hash,
                previous_credential_id: null,
                evidence_record: evidence_record
            };

            const recordData = {
                evidencehash: evidence_hash,
                credentialId: credentialId,
                vcJwt: "",
                previousCredentialId: null,
                last_modifier_did: "",
                sequence: null,
                status: "active" as const,
                issuerDid: issuer.did,
                ownerDid: subject_did,
                createdAt: new Date(),
                tags: tags || []
            };

            await create_evidence(subjectData, issuer, dbHandler, recordData, contract);

            // Send a success response. No `return` needed.
            res.status(201).json({ 
                message: 'Evidence created successfully', 
                credentialId: credentialId 
            });
        }
    } catch (error) {
        console.error('Error creating evidence:', error);
        // Send an error response. No `return` needed.
        res.status(500).json({ error: 'Failed to create evidence' });
    }
});

// Shoul return only metadata information
app.post('/chain-of-custody', async (req: Request, res: Response) => {
    try {
        let { credentialId, owner_did, evidence_hash } = req.body;
        if (!owner_did) {
            res.status(400).json({ error: 'Missing required fields: owner_did' });
            return;
        }
        if (!credentialId && !evidence_hash) {
            res.status(400).json({ error: 'Must provide either credentialId field or evidence_hash field' });
            return;
        }

        if (!credentialId) {
            credentialId = await get_credential_id_by_evidence_hash(evidence_hash ,dbHandler);
            if (!credentialId) {
                res.status(404).json({ error: 'No active credential found for the given evidence_hash' });
                return;
            }
        }

        console.log(`Received request to fetch chain of custody for credential: ${credentialId}`);

        // --- Fetch Credential Definition ---
        const credDefResponse = await axios.get('http://localhost:49152/credential-definition');
        const { credential_guid, connectionId } = credDefResponse.data;

        // --- Request Presentation ---
        await axios.post(`${VERIFIER_API_URL}/presentation_request`, {
            connection_id: connectionId,
            cred_def_guid: credential_guid,
            level_required: "0",
            id_database: identifier
        });

        // --- Poll for Verified Data ---
        const verified_data = await pollForVerifiedData(identifier);
        console.log(verified_data['requested_proof']['revealed_attrs']);

        const subject_did = verified_data['requested_proof']['revealed_attrs']['subject_did_proof']['raw']
        const expert_name = verified_data['requested_proof']['revealed_attrs']['expert_name_proof']['raw']
        console.log(expert_name)

        if (owner_did !== subject_did) {
                res.status(400).json({ 
                    error: `Invalid DIDs!`
                });
                return;
        }

        const chainOfCustody = await get_chain_of_custody(credentialId, dbHandler, contract);

        // Replace the sensitive vcJwt with a placeholder for this metadata endpoint
        const metadataChain = chainOfCustody.map(link => ({
            ...link,
            databaseRecord: {
                ...link.databaseRecord,
                vcJwt: "vcJWTPlaceholder"
            }
        }));

        res.status(200).json(metadataChain);
    } catch (error: any) {
        console.error('Error fetching chain of custody:', error.message);
        
        if (error.message.includes('The chain of custody is broken')) {
            res.status(404).json({ error: error.message });
        } else {
            res.status(500).json({ error: 'Failed to fetch chain of custody' });
        }
    }
});


app.post('/verify-chain-of-custody', async (req: Request, res: Response) => {
    try {
        let { credentialId, owner_did, evidence_hash } = req.body;
        if (!owner_did) {
            res.status(400).json({ error: 'Missing required fields: owner_did' });
            return;
        }
        if (!credentialId && !evidence_hash) {
            res.status(400).json({ error: 'Must provide either credentialId field or evidence_hash field' });
            return;
        }
        if (!credentialId) {
            credentialId = await get_credential_id_by_evidence_hash(evidence_hash ,dbHandler);
            if (!credentialId) {
                res.status(404).json({ error: 'No active credential found for the given evidence_hash' });
                return;
            }
        }

        console.log(`Received request to verify chain for credential: ${credentialId}`);
        // --- Fetch Credential Definition ---
        const credDefResponse = await axios.get('http://localhost:49152/credential-definition');
        const { credential_guid, connectionId } = credDefResponse.data;
        // --- Request Presentation ---
        await axios.post(`${VERIFIER_API_URL}/presentation_request`, {
            connection_id: connectionId,
            cred_def_guid: credential_guid,
            level_required: 1,
            id_database: identifier
        });
        // --- Poll for Verified Data --
        const verified_data = await pollForVerifiedData(identifier);
        console.log(verified_data['requested_proof']['revealed_attrs']);
        const subject_did = verified_data['requested_proof']['revealed_attrs']['subject_did_proof']['raw'];

        if (owner_did !== subject_did) {
            res.status(400).json({ error: `Invalid DIDs!` });
            return;
        }
        
        const chainOfCustody = await get_chain_of_custody(credentialId, dbHandler, contract);
        const verificationPayloads = await verify_chain_of_custody(chainOfCustody);

        res.status(200).json({
            message: 'Chain of custody verified successfully',
            payloads: verificationPayloads
        });

    } catch (error: any) {
        console.error('Error verifying chain of custody:', error.message);

        if (error.message.includes('The chain of custody is broken')) {
            res.status(404).json({ error: error.message });
        } else if (error.message.includes('mismatch') || error.message.includes('Failed to verify')) {
            res.status(400).json({ error: `Verification failed: ${error.message}` });
        } else {
            res.status(500).json({ error: 'Failed to verify chain of custody' });
        }
    }
});

app.post('/update-evidence', async (req: Request, res: Response) => {
    try {
        let { old_credential_id, owner_did, new_evidence_record, tags, evidence_hash} = req.body;

        if (!owner_did || !new_evidence_record) {
            res.status(400).json({ 
                error: 'Missing required fields: owner_did, new_evidence_record' 
            });
            return;
        }

        if (!old_credential_id && !evidence_hash) {
            res.status(400).json({ error: 'Must provide either old_credential_id or evidence_hash' });
            return;
        }
        
        if (!old_credential_id) {
            const retrievedCredentialId = await get_credential_id_by_evidence_hash(evidence_hash, dbHandler);
            if (!retrievedCredentialId) {
                res.status(404).json({ error: 'No active credential found for the given evidence_hash' });
                return;
            }
            old_credential_id = retrievedCredentialId;
        }

        // Fetch old record to get evidence_hash and verify ownership
        const oldRecord = await dbHandler.findRecordByCredentialId(old_credential_id);

        if (!oldRecord) {
            res.status(404).json({ error: 'Credential to be updated not found.' });
            return;
        }

        if (oldRecord.ownerDid !== owner_did) {
            res.status(403).json({ error: 'Forbidden: You are not the owner of this evidence.' });
            return;
        }

        const evidence_hash_from_record = oldRecord.evidencehash;
        if (evidence_hash_from_record != evidence_hash) {
            res.status(400).json({ error: 'Evidence hashes NOT MATCHING' });
        }

        // Perform credential verification
        console.log('Fetching credential definition for update...');
        const credDefResponse = await axios.get('http://localhost:49152/credential-definition');
        const { credential_guid, connectionId } = credDefResponse.data;

        console.log(`Requesting presentation for update with identifier: ${identifier}`);
        await axios.post(`${VERIFIER_API_URL}/presentation_request`, {
            connection_id: connectionId,
            cred_def_guid: credential_guid,
            level_required: 2,
            id_database: identifier
        });

        const verified_data = await pollForVerifiedData(identifier);
        console.log(verified_data['requested_proof']['revealed_attrs']);
        
        const subject_did = verified_data['requested_proof']['revealed_attrs']['subject_did_proof']['raw'];
        const evidence_hash_cred = verified_data['requested_proof']['revealed_attrs']['evidence_hash_proof']['raw'];

        if (owner_did !== subject_did) {
            res.status(400).json({ error: `Invalid DIDs!` });
            return;
        }
    
        if (evidence_hash !== evidence_hash_cred) {
            res.status(400).json({ error: "Invalid evidence hash! Cannot update." });
            return;
        }

        // 3. Prepare data for the new credential
        const { issuer } = await createIssuer();
        const newCredentialId = await createCredentialId();

        const subjectData = {
            id: newCredentialId,
            evidence_hash: evidence_hash, // Use the original hash
            previous_credential_id: old_credential_id, // Link to the old one
            evidence_record: new_evidence_record
        };

        const recordData = {
            evidencehash: evidence_hash,
            credentialId: newCredentialId,
            vcJwt: "",
            previousCredentialId: old_credential_id,
            last_modifier_did: "", // Logic function will set this
            sequence: null, // Logic function will set this
            status: "active" as const,
            issuerDid: issuer.did,
            ownerDid: subject_did, // The verified owner
            createdAt: new Date(),
            tags: tags || oldRecord.tags // Use new tags or fall back to old ones
        };


        await update_evidence(old_credential_id, subjectData, issuer, dbHandler, recordData, contract);

        res.status(200).json({ 
            message: 'Evidence updated successfully', 
            newCredentialId: newCredentialId 
        });

    } catch (error: any) {
        console.error('Error updating evidence:', error.message);
        res.status(500).json({ error: 'Failed to update evidence' });
    }
});

app.post('/transfer-ownership', async (req: Request, res: Response) => {
    try {
        let { credential_id, evidence_hash, current_owner_did, new_owner_did } = req.body;

        let level_required = 2; // Level 2 if you are the owner.

        if (!current_owner_did || !new_owner_did) {
            res.status(400).json({
                error: 'Missing required fields: current_owner_did, new_owner_did'
            });
            return;
        }

        if (!credential_id && !evidence_hash) {
            res.status(400).json({
                error: 'Must provide either credential_id or evidence_hash'
            });
            return;
        }
        
        if (!credential_id) {
            const retrievedCredentialId = await get_credential_id_by_evidence_hash(evidence_hash, dbHandler);
            if (!retrievedCredentialId) {
                res.status(404).json({ error: 'No active credential found for the given evidence_hash' });
                return;
            }
            credential_id = retrievedCredentialId;
        }


        // 1. Fetch the record to verify current ownership
        const record = await dbHandler.findRecordByCredentialId(credential_id);

        if (!record) {
            res.status(404).json({ error: 'Credential not found.' });
            return;
        }

        if (evidence_hash && record.evidencehash !== evidence_hash) {
            res.status(400).json({ error: 'The provided evidence_hash does not match the record being updated.' });
            return;
        }

        if (record.ownerDid !== current_owner_did) {
            level_required = 99;
        }

        // 2. Perform DID verification for the current owner
        console.log('Fetching credential definition for ownership transfer...');
        const credDefResponse = await axios.get('http://localhost:49152/credential-definition');
        const { credential_guid, connectionId } = credDefResponse.data;

        console.log(`Requesting presentation for transfer with identifier: ${identifier}`);
        await axios.post(`${VERIFIER_API_URL}/presentation_request`, {
            connection_id: connectionId,
            cred_def_guid: credential_guid,
            level_required: level_required, // 2 if are the owner, otherwise 99 required (admin)
            id_database: identifier
        });

        const verified_data = await pollForVerifiedData(identifier);
        console.log(verified_data['requested_proof']['revealed_attrs']);
        const subject_did = verified_data['requested_proof']['revealed_attrs']['subject_did_proof']['raw'];

        if (level_required !== 99 && current_owner_did !== subject_did) {
            res.status(400).json({ error: `Invalid DIDs! Verification failed.` });
            return;
        }

        // 3. Call the logic function to perform the transfer
        await transfer_evidence_ownership(credential_id, new_owner_did, dbHandler, contract);

        res.status(200).json({
            message: 'Ownership transferred successfully',
            credentialId: credential_id,
            newOwner: new_owner_did
        });

    } catch (error: any) {
        console.error('Error transferring ownership:', error.message);
        res.status(500).json({ error: 'Failed to transfer ownership' });
    }
});

// ===================================================================================
// SERVER INITIALIZATION
// ===================================================================================

// Async function to handle the setup process
const startServer = async () => {
    try {
        console.log('Initializing server...');

        // Connect to MongoDB
        dbHandler = new DatabaseHandler(MONGO_URI);
        await dbHandler.connect();

        // Connect to Hyperledger Fabric Gateway
        const { gateway } = await createGatewayConnection();
        const network = gateway.getNetwork(channelName);
        contract = network.getContract(chaincodeName);
        
        // Start listening for HTTP requests
        app.listen(PORT, () => {
            console.log(`Server is running and listening on http://localhost:${PORT}`);
        });

    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
};

// Calling the function that starts the server
startServer();