import axios, { isAxiosError } from 'axios';

// --- Configuration ---
const VERIFIER_API_BASE_URL = 'http://localhost:5017';
const MOCKDB_API_BASE_URL = 'http://localhost:49152';


// --- TypeScript Interfaces ---
export interface CredentialDefinition {
    credential_guid: string;
    connectionId: string;
}

export interface PresentationRequestSuccessResponse {
    status: string;
    details: any;
}


// --- API Client Functions ---
/**
 * Fetches the current credential definition data.
 * @returns A Promise that resolves with the credential definition or null if it fails.
 */
export async function getCredentialDefinition(): Promise<CredentialDefinition | null> {
    const url = `${MOCKDB_API_BASE_URL}/credential-definition`;
    console.log(`🔷 Fetching credential definition from: ${url}`);
    
    try {
        const response = await axios.get<CredentialDefinition>(url);
        console.log('✅ Successfully fetched credential definition:', response.data);
        return response.data;
    } catch (error) {
        console.error('❌ Error fetching credential definition:');
        if (isAxiosError(error)) {
            console.error('Status:', error.response?.status);
            console.error('Data:', error.response?.data);
        } else {
            console.error(error);
        }

        return null;
    }
}

/**
 * Sends a request to the Verifier API to initiate a presentation request.
 * @returns A Promise that resolves with the success response or null if it fails.
 */
export async function requestPresentation(
    connectionId: string,
    credDefGuid: string,
    levelRequired: string | number
): Promise<PresentationRequestSuccessResponse | null> {
    const url = `${VERIFIER_API_BASE_URL}/presentation_request`;
    const payload = {
        connection_id: connectionId,
        cred_def_guid: credDefGuid,
        level_required: levelRequired,
    };
    
    console.log(`🔷 Sending presentation request to: ${url}`);
    console.log(`   Payload: ${JSON.stringify(payload, null, 2)}`);

    try {
        const response = await axios.post<PresentationRequestSuccessResponse>(url, payload);
        console.log('✅ Successfully initiated presentation request:', response.data);
        return response.data;
    } catch (error) {
        console.error('❌ Error requesting presentation:');
        if (isAxiosError(error)) {
            console.error('Status:', error.response?.status);
            console.error('Data:', error.response?.data);
        } else {
            console.error(error);
        }

        return null;
    }
}


/*
// --- Example Usage (Updated to handle null) ---
// This shows how your main application should now check for null.

async function main() {
    // 1. Get the credential definition info needed for the request
    const credDefInfo = await getCredentialDefinition();
    
    // CHANGED: Check if the result is null before proceeding.
    if (!credDefInfo) {
        console.error("\n--- Demo Failed ---");
        console.error("Could not retrieve credential definition. Halting execution.");
        return; // Exit the function gracefully
    }
    
    // 2. Use that info to make the presentation request
    const presentationResult = await requestPresentation(
        credDefInfo.connectionId,
        credDefInfo.credential_guid,
        "Level 5" // Example level required
    );
    
    // CHANGED: Check the final result for null as well.
    if (!presentationResult) {
        console.error("\n--- Demo Failed ---");
        console.error("Presentation request failed.");
        return;
    }
    
    console.log("\n--- Demo Complete ---");
    console.log("Final Presentation Result:", presentationResult);
}

main();
*/