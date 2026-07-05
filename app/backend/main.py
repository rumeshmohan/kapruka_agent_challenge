import os
import sys
import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict

# Ensure internal modules can find root directory pathing
root_path = str(Path(__file__).resolve().parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

from main import run_agent_pipeline
from memory.session_buffer import SessionBuffer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Kapruka Smart Agent Core API")

# Allow cross-origin calls during local prototyping phase
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROFILES_FILE = Path("data/profiles.json")
session_memories: Dict[str, SessionBuffer] = {}

# Pydantic Schemas for validation
class QueryRequest(BaseModel):
    query: str
    session_id: str
    cart: List[dict]

# API Endpoints
@app.get("/api/profile")
def get_profile():
    if not PROFILES_FILE.exists():
        return {"customer_name": "Guest", "recipients": {}}
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("CUS_001", {"customer_name": "Guest", "recipients": {}})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profile/reset")
def reset_profile_json():
    """Physically resets profiles.json to the baseline initial stage."""
    try:
        baseline_snapshot = {
            "CUS_001": {
                "customer_name": "Guest",
                "recipients": {}
            }
        }
        PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(baseline_snapshot, f, indent=2)
        return baseline_snapshot["CUS_001"]
    except Exception as e:
        logger.error(f"Failed to clear user vault file: {e}")
        raise HTTPException(status_code=500, detail=f"Database wipe failure: {str(e)}")

@app.post("/api/chat")
async def chat_with_agent(payload: QueryRequest):
    session_id = payload.session_id
    if session_id not in session_memories:
        session_memories[session_id] = SessionBuffer(max_pairs=5)

    # NOTE: the "don't output raw markdown links" constraint used to be
    # appended here globally, to every query regardless of intent. That
    # broke the checkout agent, whose whole job is to hand the guest a
    # working payment link formatted in Markdown. The constraint now lives
    # in catalog_agent.py's own system prompt, scoped to where it's
    # actually needed, so checkout and logistics are unaffected.

    try:
        response = run_agent_pipeline(
            query=payload.query,
            session_memory=session_memories[session_id],
            cart_items=payload.cart
        )
        
        raw_text = response.get("text", "")
        
        # --- CLEANUP LAYER: Strip out raw trailing data strings from user text view ---
        clean_text = raw_text
        if "products:" in clean_text:
            clean_text = clean_text.split("products:")[0].strip()
        elif "Products:" in clean_text:
            clean_text = clean_text.split("Products:")[0].strip()

        return {
            "text": clean_text,
            "products": response.get("products", []),
            "order_status": response.get("order_status"),
            "checkout_data": response.get("checkout_data"),
        }
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Standalone tracking lookup, so the /track page can look up an order
# directly without going through the chat pipeline / LLM at all.
@app.get("/api/track/{order_number}")
def track_order_direct(order_number: str):
    from utils.mcp_client import execute_remote_tool
    from agents.logistics_agent import parse_tracking_markdown

    try:
        raw_result = execute_remote_tool("kapruka_track_order", {"order_number": order_number})
        if isinstance(raw_result, str):
            parsed = parse_tracking_markdown(raw_result)
            return parsed or {"raw": raw_result}
        return raw_result
    except Exception as e:
        logger.error(f"Direct tracking lookup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount compiled static frontend production builds securely
frontend_dist = Path("app/frontend/dist")
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="frontend-assets")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str, request: Request):
        """
        Serves the compiled React app for any non-API path, so client-side
        routes like /payment and /track resolve correctly on a hard refresh
        or a directly-typed URL, not just via in-app navigation.
        """
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")

        candidate = frontend_dist / full_path
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)

        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

        return JSONResponse({"status": "Backend running. Build your frontend code to see the full UI."}, status_code=200)
else:
    @app.get("/")
    def index_fallback():
        return {"status": "Backend running. Build your frontend code to see the full UI."}