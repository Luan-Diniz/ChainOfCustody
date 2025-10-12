from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from async_mock_db import AsyncMockDB  

# --- FastAPI App & Mock DB Instance ---
app = FastAPI(title="Async MockDB Service")
db = AsyncMockDB()


# --- Pydantic Models ---
class IdentityIn(BaseModel):
    name: str
    did: str

class DIDUpdate(BaseModel):
    new_did: str

class CredentialDefinitionPayload(BaseModel):
    credential_def_guid: str
    connectionId: str
class VerifiedData(BaseModel):
    identifier: str
    data: str


# --- API Routes ---
@app.post("/identities", status_code=201)
async def add_identity(identity: IdentityIn):
    """
        This endpoint handles both creation and updates (upsert).
    """
    await db.add_identity(identity.name, identity.did)

    return {"status": "success", "name": identity.name}

@app.get("/identities")
async def list_identities():
    identities = await db.list_identities()

    return identities

@app.get("/identities/{name}")
async def get_identity(name: str):
    identity = await db.get_identity(name)
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    return identity


@app.get("/trusted-issuers")
async def get_trusted_issuers():
    issuers = await db.get_trusted_issuers()

    return {"trusted_issuers": issuers}

@app.post("/trusted-issuers/{issuer}")
async def add_trusted_issuer(issuer: str):
    await db.add_trusted_issuer(issuer)
    issuers = await db.get_trusted_issuers()

    return {"trusted_issuers": issuers}

@app.post("/credential-definition")
async def set_credential_definition(payload: CredentialDefinitionPayload):
    """
    Receives and stores the latest credential definition GUID and the associated 
    issuer-holder connection ID.
    """
    await db.update_credential_definition_guid(
        credential_definition_guid=payload.credential_def_guid,
        connectionId=payload.connectionId
    )
    return {"message": "Credential definition info updated successfully."}

@app.get("/credential-definition")
async def get_credential_definition():
    """
    Retrieves the currently stored credential definition GUID and connection ID.
    """
    guid, conn_id = await db.get_credential_definition_guid()
    
    if not guid or not conn_id:
        raise HTTPException(
            status_code=404, 
            detail="Credential definition info has not been set yet."
        )
        
    return {"credential_guid": guid, "connectionId": conn_id}

@app.get("/verified-data/{identifier}")
async def get_verified_data(identifier: str):
    data = await db.get_verified_data(identifier)
    if not data:
        raise HTTPException(status_code=404, detail="Verified data not found")

    return data

@app.post("/verified-data")
async def add_verified_data(payload: VerifiedData):
    await db.add_verified_data(payload.identifier, payload.data)
    return {"message": "Successfully added that verified data."}

# --- Uvicorn Runner ---
# uvicorn mockdb_service:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mockdb_service:app", host="localhost", port=49152, reload=True)


