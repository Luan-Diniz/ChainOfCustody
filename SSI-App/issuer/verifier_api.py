# Por aqui que vai chamar a função para criar o presentation request.
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from verifier_controller import *
from verifier_controller import accept_presentation as accept_presentation_controller
import asyncio

URL_DB = 'http://localhost:49152'
HOLDER_API_URL="http://localhost:5001"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}
app = FastAPI()

id_to_store_in_database = None

@app.post("/presentation_request")
async def create_presentation_request(request: Request):
    global id_to_store_in_database
    try:
        payload = await request.json()
        connection_id = payload.get("connection_id") # Pegar os argumentos coretos
        credential_definition_guid = payload.get("cred_def_guid")
        level_required = payload.get("level_required")
        id_database = payload.get("id_database")

        if not connection_id:
            raise HTTPException(status_code=400, detail="'connection_id' key is required in the payload.")
        elif not credential_definition_guid:
            raise HTTPException(status_code=400, detail="'cred_def_guid' key is required in the payload.")
        elif not level_required:
            raise HTTPException(status_code=400, detail="'level_required' key is required in the payload.")
        elif not id_database:
            raise HTTPException(status_code=400, detail="'id_database' key is required in the payload.")

        id_to_store_in_database = id_database

        presentation_thid, presentation_id = await create_presentation_request_anoncreds(
            connection_id,  
            credential_definition_guid,
            level_required
        ) 

        print(presentation_thid)
        url = f"{HOLDER_API_URL}/receive_presentation_request"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={"presentation_thid": presentation_thid}) as response:
                response_data = await response.json()
                print(f"Tried to accept presentation, holder response: {response_data}")
    
        return JSONResponse(
            status_code=200,
            content={"status": "success", "details": response_data}
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        error_info = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "payload_received": payload if 'payload' in locals() else "Payload not parsed",
        }
        # Log completo
        print(f"❌ Internal error in /presentation_request: {error_info}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error occurred: {error_info}"
        )


@app.post("/accept_presentation")
async def accept_presentation(request: Request):
    global id_to_store_in_database
    try:
        payload = await request.json()
        presentation_id = payload.get("presentation_id") 

        if not presentation_id:
            raise HTTPException(status_code=400, detail="'presentation_id' key is required in the payload.")

        response_data = await accept_presentation_controller(presentation_id)
        print(response_data)
        

        # Get Verified Data from agent
        verified_data = await get_verified_data(presentation_id)

        # Store Verified Data to Mock Db.
        url = f"{URL_DB}/verified-data"
        data = {"identifier": id_to_store_in_database,
                "data": verified_data[0]}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                print(f"MockDB responded with status: {response.status}")

        return JSONResponse(
            status_code=200,
            content={"status": "success", "details": response_data}
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("verifier_api:app", host="localhost", port=5017, reload=True)

