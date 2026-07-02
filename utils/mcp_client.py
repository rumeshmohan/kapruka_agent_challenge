import uuid
import json
import re
import requests
import streamlit as st
from utils.config import get_config

config = get_config()
MCP_URL = config.get("mcp.url", "https://mcp.kapruka.com/mcp")

IMAGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.kapruka.com/",
    "Accept": "application/json, text/event-stream",
}

def get_mcp_session():
    if "mcp_session_id" in st.session_state and st.session_state.mcp_session_id:
        return st.session_state.mcp_session_id
        
    init_payload = {
        "jsonrpc": "2.0",
        "id": "init-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "KaprukaConcierge", "version": "1.0.0"}
        }
    }
    
    try:
        resp = requests.post(MCP_URL, json=init_payload, headers=IMAGE_HEADERS, timeout=15)
        resp.raise_for_status()
        session_id = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id") or str(uuid.uuid4())
        st.session_state.mcp_session_id = session_id
        
        headers = dict(IMAGE_HEADERS)
        headers["Mcp-Session-Id"] = session_id
        notify_payload = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        requests.post(MCP_URL, json=notify_payload, headers=headers, timeout=15)
    except Exception as e:
        print(f"🚨 MCP SESSION ERROR: {e}")
        session_id = str(uuid.uuid4())
        st.session_state.mcp_session_id = session_id
        
    return st.session_state.mcp_session_id

def execute_remote_tool(tool_name: str, arguments: dict) -> list:
    session_id = get_mcp_session()
    headers = dict(IMAGE_HEADERS)
    headers["Mcp-Session-Id"] = session_id

    if tool_name == "kapruka_search_products" and "query" in arguments:
        arguments["q"] = arguments.pop("query")

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": {"params": arguments}
        }
    }

    try:
        response = requests.post(MCP_URL, json=payload, headers=headers, timeout=15)
        raw_text = response.text.strip()
        response.raise_for_status()
        
        if not raw_text:
            return []
            
        data = None
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            if "data:" in raw_text:
                for line in raw_text.splitlines():
                    if line.startswith("data:"):
                        try:
                            data = json.loads(line.replace("data:", "", 1).strip())
                            break
                        except json.JSONDecodeError:
                            pass
        
        if data and "result" in data:
            result_data = data["result"]
            if "content" in result_data and isinstance(result_data["content"], list):
                for block in result_data["content"]:
                    if block.get("type") == "text":
                        text_val = block.get("text", "[]")
                        try:
                            parsed = json.loads(text_val)
                            if isinstance(parsed, list): return parsed
                            if isinstance(parsed, dict) and "products" in parsed: return parsed["products"]
                        except json.JSONDecodeError:
                            parsed_products = []
                            pattern = re.compile(
                                r'\*\*\d+\.\s+(.*?)\*\*.*?ID:\s+`([A-Z0-9]+)`.*?LKR\s+([\d,]+).*?\[View product\]\((https?://[^\)]+)\)', 
                                re.IGNORECASE | re.DOTALL
                            )
                            for match in pattern.finditer(text_val):
                                if len(parsed_products) >= 5:
                                    break
                                name = match.group(1).strip()
                                item_id = match.group(2).strip()
                                price_str = match.group(3).replace(',', '')
                                product_url = match.group(4).strip()
                                
                                try:
                                    price = float(price_str)
                                    image_url = "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500&q=80"
                                    try:
                                        page_resp = requests.get(product_url, headers=headers, timeout=2)
                                        img_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', page_resp.text)
                                        if img_match:
                                            image_url = img_match.group(1)
                                    except Exception:
                                        pass
                                    parsed_products.append({
                                        "id": item_id,
                                        "name": name,
                                        "price": price,
                                        "image_url": image_url,
                                        "url": product_url
                                    })
                                except ValueError:
                                    continue
                            if parsed_products:
                                return parsed_products
            if isinstance(result_data, list): return result_data
            if isinstance(result_data, dict) and "products" in result_data: return result_data["products"]
    except Exception as e:
        print(f"🚨 MCP CLIENT ERROR: {e}")
    return []