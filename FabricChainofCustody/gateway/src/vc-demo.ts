// src/vc-demo.ts

import crypto from 'crypto';
import * as ed25519 from '@transmute/did-key-ed25519';

// Dizendo ao TS para usar a resolução de módulos ES para encontrar este tipo
import type { Issuer } from 'did-jwt-vc' with { 'resolution-mode': 'import' };

export async function runVcDemo(): Promise<void> {
    console.log("💡 Iniciando a demonstração de Credenciais Verificáveis (VC)...");

    // ******** Usando importação dinâmica para um módulo ESM *********
    const { createVerifiableCredentialJwt, verifyCredential} = await import('did-jwt-vc');
    const { EdDSASigner } = await import('did-jwt');
    const { Resolver } = await import('did-resolver');
    const getKeyResolver = (await import('key-did-resolver')).getResolver;

    // ******** Gerando o did:key do emissor *********
    const { didDocument, keys } = await ed25519.generate(
        {
            secureRandom: () => {
                return crypto.randomBytes(32);
            },
        },
        { accept: 'application/did+json' }
    );

    console.log('DID Gerado:', didDocument.id);

    const privateKeyJwk = keys[0].privateKeyJwk as { d: string;[key: string]: any };
    const privateKeyBytes = Buffer.from(privateKeyJwk.d, 'base64url');

    // ******** Preparando o Emissor (Issuer) *********
    const signer = EdDSASigner(privateKeyBytes);

    const issuer: Issuer = {
        did: didDocument.id,
        signer: signer,
        alg: 'EdDSA',
    };

    // ******** Definindo o payload da VC *********
    const vcPayload = {
        '@context': ['https://www.w3.org/2018/credentials/v1'],
        type: ['VerifiableCredential', 'Evidence'],
        issuer: issuer.did, // O DID do emissor
        issuanceDate: new Date().toISOString(), // Data no formato ISO 8601
        credentialSubject: {
            id: 'did:example:ebfeb1f712ebc6f1c276e12ec21',
            status: 'active',
            previous_credential_id: null,
            evidence_record: {
                what: "Um HD externo da marca Seagate, modelo Expansion, capacidade de 2TB, S/N: NA8K9J7H, cor preta. O dispositivo foi encontrado conectado a um desktop.",
                who: "Coletado pelo Perito Policial Tiago Bastos (ID Funcional 9845-B), na presença das testemunhas arroladas no Termo de Apreensão.",
                where: "No escritório de um apartamento residencial localizado na Rua Lauro Linhares, 1200, Apto 501, Trindade, Florianópolis - SC.",
                when: "Apreendido no dia 15 de agosto de 2025, exatamente às 15:47 (horário de Brasília), durante o cumprimento de um mandado de busca e apreensão.",
                why: "Para ser submetido à análise forense digital, pois há suspeita de que armazene planilhas de contabilidade e documentos relacionados a uma investigação de lavagem de dinheiro.",
                how: "O dispositivo foi desconectado de forma segura do computador, fotografado, acondicionado em embalagem antiestática e lacrado com o lacre de segurança número SP-SC-08152025-007. Todo o processo foi documentado no formulário de cadeia de custódia."
            }
        },
    };

    // ******** Criando e assinando a VC no formato JWT *********
    console.log('\nCriando a Credencial JWT...');
    const vcJwt = await createVerifiableCredentialJwt(vcPayload, issuer);
    console.log('\n✅ Credencial JWT gerada com sucesso!');
    console.log(vcJwt);

    // ******** Verificando a Credencial *********
    console.log('\n--------------------------------------------------');
    console.log('Iniciando a verificação da Credencial...');

    const keyResolver = getKeyResolver();
    const resolver = new Resolver({
        ...keyResolver
    });

    try {
        const verifiedVc = await verifyCredential(vcJwt, resolver);
        console.log('\n✅ Verificação concluída com sucesso!');
        console.log('A credencial é autêntica.');
        console.log('\nPayload da Credencial Verificada:');
        console.log(JSON.stringify(verifiedVc, null, 2));

    } catch (error: any) {
        console.error('\n❌ Falha ao verificar a credencial:', error.message);
    }
}