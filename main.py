import logging
import threading
from agents.router import route_query
from agents.chitchat_agent import handle_chitchat_query
from agents.logistics_agent import handle_logistics_query
from agents.preference_agent import handle_preference_query, load_profile_context
from agents.catalog_agent import handle_catalog_query
from agents.checkout_agent import handle_checkout_query
from agents.reflection_loop import evaluate_and_reflect
from memory.session_buffer import SessionBuffer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_agent_pipeline(query: str, session_memory: SessionBuffer, cart_items: list) -> dict:
    # 🌟 INNOVATIVE UPGRADE: Background Dual-Processing (Listen & Learn)
    # Even if it's a catalog search, inspect if they slipped a preference/allergy in
    try:
        # We process this quickly to update the profile JSON file before catalog rendering
        handle_preference_query(query, history=session_memory.get_history_string())
    except Exception:
        pass

    profile_context = load_profile_context()
    session_memory.set_persistent_context(profile_context)
    
    intent = route_query(query)
    logger.info(f"🎯 Routed Intent: {intent}")
    
    history_str = session_memory.get_history_string()
    session_memory.add_message("user", query)
    
    output = {
        "text": "",
        "image_urls": [],
        "products": [],
        "intent": intent
    }

    if intent == "[CHITCHAT]":
        output["text"] = handle_chitchat_query(query)
        session_memory.add_message("assistant", output["text"])
        
    elif intent == "[LOGISTICS]":
        output["text"] = handle_logistics_query(query, history=history_str)
        session_memory.add_message("assistant", output["text"])
        
    elif intent == "[PREFERENCE]":
        # Handled gracefully above via background parsing, but return text if explicit
        output["text"] = handle_preference_query(query, history=history_str)
        session_memory.add_message("assistant", output["text"])
        
    elif intent == "[CHECKOUT]":
        output["text"] = handle_checkout_query(query, cart_items=cart_items, history=history_str)
        session_memory.add_message("assistant", output["text"])
        
    else:  # [CATALOG]
        raw_catalog_response = handle_catalog_query(query, history=history_str)
        
        reflected_response = evaluate_and_reflect(
            query=query,
            proposed_response=raw_catalog_response,
            profile_context=profile_context
        )
        
        output["text"] = reflected_response.get("text", "")
        output["image_urls"] = reflected_response.get("image_urls", [])
        output["products"] = reflected_response.get("products", [])
        session_memory.add_message("assistant", output["text"])

    return output