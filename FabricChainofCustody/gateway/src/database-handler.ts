import { MongoClient, ObjectId, Collection, Db } from 'mongodb';

/**
 * Interface for the custody credential record in MongoDB.
 */
export interface CustodyCredentialRecord {
    _id?: ObjectId;
    evidencehash: string;
    credentialId: string;
    vcJwt: string;
    previousCredentialId: string | null;
    last_modifier_did: string;
    sequence: null | number;
    status: 'active' | 'revoked';
    issuerDid: string;
    ownerDid: string;
    createdAt: Date;
    tags: string[];
}

/**
 * A class to handle all database operations for the chain of custody.
 */
export class DatabaseHandler {
    private client: MongoClient;
    private dbName: string = 'chain_of_custody_db';
    private collectionName: string = 'evidence_records';
    private db: Db | undefined;
    private recordsCollection: Collection<CustodyCredentialRecord> | undefined;

    constructor(uri: string) {
        this.client = new MongoClient(uri);
    }

    /**
     * Connects to the MongoDB server and initializes the database and collection objects.
     */
    public async connect(): Promise<void> {
        try {
            await this.client.connect();
            this.db = this.client.db(this.dbName);
            this.recordsCollection = this.db.collection<CustodyCredentialRecord>(this.collectionName);
            console.log('Conectado com sucesso ao MongoDB');
        } catch (error) {
            console.error("Falha ao conectar ao MongoDB:", error);
            throw error;
        }
    }

    /**
     * Disconnects from the MongoDB server.
     */
    public async disconnect(): Promise<void> {
        await this.client.close();
        console.log('\nConexão com o MongoDB fechada.');
    }

    /**
     * Creates a new custody record in the database.
     * @param record The record to create, without the _id.
     * @returns The ObjectId of the newly created record.
     */
    public async createRecord(record: Omit<CustodyCredentialRecord, '_id'>): Promise<ObjectId> {
        if (!this.recordsCollection) throw new Error("A coleção não foi inicializada. Chame connect() primeiro.");
        const result = await this.recordsCollection.insertOne(record);
        return result.insertedId;
    }

    /**
     * Finds a record by its ObjectId.
     * @param id The ObjectId of the record to find.
     * @returns The found record or null.
     */
    public async findRecordByCredentialId(credentialId: string): Promise<CustodyCredentialRecord | null> {
        if (!this.recordsCollection) throw new Error("A coleção não foi inicializada. Chame connect() primeiro.");
        return this.recordsCollection.findOne({ credentialId: credentialId });
    }

    /**
     * Updates a record's status and adds a tag.
     * @param id The ObjectId of the record to update.
     * @param newStatus The new status to set.
     */
    public async updateRecordStatus(credential_id: string, newStatus: CustodyCredentialRecord['status']): Promise<void> {
        if (!this.recordsCollection) throw new Error("A coleção não foi inicializada. Chame connect() primeiro.");
        await this.recordsCollection.updateOne(
            { credentialId: credential_id },
            {
                $set: { status: newStatus },
            }
        );
    }

        /**
     * Finds the active credential ID for a given evidence hash.
     * Assumes that only one credential for a given evidence hash can be active at any time.
     * @param evidencehash The hash of the evidence to search for.
     * @returns The credentialId of the active record, or null if no active record is found.
     */
    public async findActiveCredentialByEvidenceHash(evidencehash: string): Promise<string | null> {
        if (!this.recordsCollection) {
            throw new Error("A coleção não foi inicializada. Chame connect() primeiro.");
        }

        // Find the one document that matches the hash and has an 'active' status.
        const record = await this.recordsCollection.findOne({
            evidencehash: evidencehash,
            status: 'active'
        });

        // If a record is found, return its credentialId, otherwise return null.
        return record ? record.credentialId : null;
    }

    /**
     * Updates a record's owner DID.
     * @param credential_id The credentialId of the record to update.
     * @param newOwnerDid The new owner DID to set.
     */
    public async updateRecordOwner(credential_id: string, newOwnerDid: string): Promise<void> {
        if (!this.recordsCollection) {
            throw new Error("A coleção não foi inicializada. Chame connect() primeiro.");
        }
        
        // Encontra o documento pelo credentialId e atualiza o campo ownerDid.
        await this.recordsCollection.updateOne(
            { credentialId: credential_id },
            {
                $set: { ownerDid: newOwnerDid },
            }
        );
    }
}

