from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from holder_controller import *
import asyncio

app = FastAPI()

credential_offer_thid = ""

@app.post("/receive_oob_invitation")
async def receive_invitation(request: Request):
    """
    Receives an out-of-band invitation, validates it, and passes it to the holder controller.
    """
    try:
        payload = await request.json()
        raw_invitation = payload.get("raw_invitation")

        if not raw_invitation:
            raise HTTPException(status_code=400, detail="'raw_invitation' key is required in the payload.")

        response_data = await accept_connection(raw_invitation)
        
        print(response_data)
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "connection_details": response_data}
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")


@app.post("/receive_credential_offer")
async def receive_credential_offer(request: Request):
    """
    Receives an credential_offer and tries to accept it.
    """

    global credential_offer_thid

    try:
        payload = await request.json()
        credential_offer_thid = payload.get("thid")

        if not credential_offer_thid:
            raise HTTPException(status_code=400, detail="'thid' key is required in the payload.")

        # Would be better to just user an webhook handler for holder 
        # instead of the sleep. But for the purposes of a proof of concept thats okay.
        await asyncio.sleep(5)
        # Call holder_controller 'accept_offer()'
        print(f'CREDENTIAL THID: {credential_offer_thid}')
        response_data = await accept_credential_offer(credential_offer_thid)
        print(response_data)
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "connection_details": response_data}
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")


@app.post("/receive_presentation_request")
async def receive_presentation_request(request: Request):
    """
    ...
    """
    try:
        payload = await request.json()
        presentation_thid = payload.get("presentation_thid")

        if not presentation_thid:
            raise HTTPException(status_code=400, detail="'presentation_thid' key is required in the payload.")

        # Would be better to just user an webhook handler for holder 
        await asyncio.sleep(5)
        response_data = await accept_presentation_request(presentation_thid, credential_offer_thid)
        print(response_data)
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "connection_details": response_data}
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("holder_api:app", host="localhost", port=5001, reload=True)

