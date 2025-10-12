

// Dizendo ao TS para usar a resolução de módulos ES para encontrar este tipo.
// Esta é a correção para o erro de 'resolution-mode'.
//import type { DIDDocument } from 'did-resolver' with { 'resolution-mode': 'import' };
import type { Issuer, VerifiedCredential } from 'did-jwt-vc' with { 'resolution-mode': 'import' };


export interface EvidenceRecordData {
    what: string;
    who: string;
    where: string;
    when: string;
    why: string;
    how: string;
}

export interface CredentialSubjectData {
    id: string;
    evidence_hash: string;
    previous_credential_id: string | null;
    evidence_record: EvidenceRecordData;
}


/**
 * Cria uma nova Credencial Verificável (VC) no formato JWT.
 */
export async function createCredential(subject_data: CredentialSubjectData,
                                       issuer: Issuer
                                    ): Promise<string> 
{

    console.log("🔑 Gerando DID do emissor e criando a credencial...");

    // ******** Usando importação dinâmica para módulos ESM *********
    const { createVerifiableCredentialJwt } = await import('did-jwt-vc');

    // 3. Definir o payload (claims) da VC
    const vcPayload = {
        '@context': ['https://www.w3.org/2018/credentials/v1'],
        type: ['VerifiableCredential', 'Evidence'],
        issuer: issuer.did,
        issuanceDate: new Date().toISOString(),
        credentialSubject: subject_data,
    };

    // 4. Criar e assinar a VC no formato JWT
    const vcJwt = await createVerifiableCredentialJwt(vcPayload, issuer);
    
    //console.log('\n✅ Credencial JWT gerada com sucesso!');
    //console.log(vcJwt);

    return vcJwt;
}

/**
 * Verifica a autenticidade e integridade de uma Credencial Verificável em formato JWT.
 */
export async function verifyCreatedCredential(vcJwt: string): Promise<VerifiedCredential> {
    // ******** Usando importação dinâmica para módulos ESM *********
    const { verifyCredential } = await import('did-jwt-vc');
    const { Resolver } = await import('did-resolver');
    const { getResolver: getKeyResolver } = await import('key-did-resolver');

    // 1. Configurar o resolver
    const keyResolver = getKeyResolver();
    const resolver = new Resolver({
        ...keyResolver
    });

    // 2. Verificar a credencial
    try {
        const verifiedVc = await verifyCredential(vcJwt, resolver);
        console.log('\n✅ Verificação concluída com sucesso!');
        console.log('A credencial é autêntica.');
        return verifiedVc;
    } catch (error: any) {
        console.error('\n❌ Falha ao verificar a credencial:', error.message);
        throw error;
    }
}