import { randomBytes } from 'crypto';
import type { Issuer } from 'did-jwt-vc' with { 'resolution-mode': 'import' };
import type { DIDDocument } from 'did-resolver' with { 'resolution-mode': 'import' };

interface IssuerData {
    didDocument: DIDDocument,
    issuer: Issuer
}


export async function createIssuer(): Promise<IssuerData> {
    const ed25519 = await import('@transmute/did-key-ed25519');
    const { EdDSASigner } = await import('did-jwt');
    
    const { didDocument, keys } = await ed25519.generate(
        {
            secureRandom: () => randomBytes(32),      // ao inves de randomBytes(32), passar senha ou algo assim //PBKDF2, SCRYPT
        },
        { accept: 'application/did+json' }
    );
    const privateKeyJwk = keys[0].privateKeyJwk as { d: string;[key: string]: any };
    const privateKeyBytes = Buffer.from(privateKeyJwk.d, 'base64url');

    const signer = EdDSASigner(privateKeyBytes);
    const issuer: Issuer = {
        did: didDocument.id,
        signer: signer,
        alg: 'EdDSA',
    };

    return {didDocument, issuer};
}

export async function createCredentialId(): Promise<string> {
    const ed25519 = await import('@transmute/did-key-ed25519');
    const { didDocument } = await ed25519.generate(
        {
            secureRandom: () => randomBytes(32),
        },
        { accept: 'application/did+json' }
    );

    return didDocument.id;
}
