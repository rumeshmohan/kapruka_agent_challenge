import os
import sys
import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

@app.post("/api/chat")
async def chat_with_agent(payload: QueryRequest):
    session_id = payload.session_id
    if session_id not in session_memories:
        session_memories[session_id] = SessionBuffer(max_pairs=5)
        
    # --- PROMPT INJECTION CONSTRAINT FOR PRECISE LINK HANDLING ---
    structured_instruction_wrapper = (
        f"{payload.query}\n\n"
        "[SYSTEM CONSTRAINT: Do NOT under any circumstances output raw markdown or text links "
        "e.g., [Name](URL) inside your conversational response. Refer to products by name only. "
        "Do NOT print out raw JSON or text lists of products at the end of your message text. "
        "The React UI automatically displays dedicated interactive catalog cards with functioning links "
        "for items populated in the products array payload. Direct the user to look at the cards instead.]"
    )

    try:
        response = run_agent_pipeline(
            query=structured_instruction_wrapper,
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
            "products": response.get("products", [])
        }
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount compiled static frontend production builds securely
frontend_dist = Path("app/frontend/dist")
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
else:
    @app.get("/")
    def index_fallback():
        return {"status": "Backend running. Build your frontend code to see the full UI."}