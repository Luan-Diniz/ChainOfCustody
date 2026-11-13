import sys
from pathlib import Path

# Add parent directory to sys.path so i18n can be imported regardless of execution directory
sys.path.append(str(Path(__file__).resolve().parent.parent))

import aiohttp
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from local_database import get_connection
from verifier_controller import accept_presentation
import json
from i18n import t

app = FastAPI()

API_VERIFIER_URL = "http://localhost:5017"

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json() 

    print(t("webhook_received"))
    print(json.dumps(payload, indent=2))
    
    connectionId = None
    if (payload['type'] == 'ConnectionUpdated') and payload["data"]["state"] == 'ConnectionResponseSent':
        connectionId = payload["data"]["connectionId"]
        name, did = await get_connection(connectionId)
        # Could refactor in a way the user needs only one terminal (issuer_interface app)
        # But for meanings of this PoC, that's alright
        print(t("connection_accepted", name=name, did=did))

    elif (payload['type'] == "PresentationUpdated") and payload["data"]["status"] == "PresentationVerified":
        #await accept_presentation(payload["data"]["presentationId"])
        presentation_id = payload["data"]["presentationId"]
        url = f"{API_VERIFIER_URL}/accept_presentation"
        data = {"presentation_id": presentation_id}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    print(t("verifier_accepted_data"))
                else:
                    print(t("error_calling_verifier", status=response.status, text=await response.text()))

    return JSONResponse({"status": "success"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webhook_handler:app", host="0.0.0.0", port=5000, reload=True)
