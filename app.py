"""
Paste the following in terminal to run the application:
uvicorn app:app --reload
"""
from fastapi import FastAPI, HTTPException
from schemas import InboundMessage
from datetime import datetime, timezone 
from pipeline import run_pipeline
from route import run_routing
import logging
import uuid
from zoneinfo import ZoneInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

beirut_tz = ZoneInfo("Asia/Beirut")


app = FastAPI(
    title = "ArcVault Assignment",
    description= "Ingestion layer"
)

LLM_PROVIDER = "openai"

#200 = ok
#202 = ill do it later
@app.post("/ingest",status_code = 200)
async def ingest_message(payload: InboundMessage):
    """
    Accepts an inbound customer message, runs it through the triage pipeline, 
    and routes it.

    The client waits for the LLM processing to finish, and receives the 
    final structured JSON output in the response.
    
    """

    intake_id   = str(uuid.uuid4())#message id
    received_at = datetime.now(beirut_tz).strftime("%Y-%m-%d %H:%M:%S")
    try:
        #the client waits here and fastapi is free to handle other requests
        pipeline_result = await run_pipeline(payload,provider=LLM_PROVIDER)

        pipeline_result["intake_id"]   = intake_id
        pipeline_result["received_at"] = received_at

        #we're also waiting for routing/sheets to finish
        final_result = await run_routing(pipeline_result, provider=LLM_PROVIDER)
    except Exception as e:
        logger.error("Pipeline/routing failed | intake_id=%s error=%s", intake_id, e)
        raise HTTPException(status_code=500, detail="Pipeline/Routing failed")
    
    # we successfully waited, now return the actual data to the user
    return {
        "status": "success",
        **final_result
    }

