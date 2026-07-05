import uuid
import json
import requests
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

_mcp_session_cache = {}

def get_mcp_session():
    if "mcp_session_id" in _mcp_session_cache and _mcp_session_cache["mcp_session_id"]:
        return _mcp_session_cache["mcp_session_id"]
        
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
        _mcp_session_cache["mcp_session_id"] = session_id

        headers = dict(IMAGE_HEADERS)
        headers["Mcp-Session-Id"] = session_id
        notify_payload = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        requests.post(MCP_URL, json=notify_payload, headers=headers, timeout=15)
    except Exception as e:
        print(f"🚨 MCP SESSION ERROR: {e}")
        session_id = str(uuid.uuid4())
        _mcp_session_cache["mcp_session_id"] = session_id

    return _mcp_session_cache["mcp_session_id"]


def _parse_mcp_body(raw_text: str):
    """
    MCP's Streamable HTTP transport can reply with either:
      1. A plain JSON body, e.g. {"jsonrpc": "2.0", "id": "...", "result": {...}}
      2. A Server-Sent Events (SSE) framed body, e.g.:
             event: message
             data: {"jsonrpc": "2.0", "id": "...", "result": {...}}

    This normalizes both cases into a parsed dict (or None if nothing usable
    was found), so callers don't need to care which transport shape came back.
    """
    if not raw_text:
        return None

    stripped = raw_text.strip()

    # Case 1: plain JSON body
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    # Case 2: SSE framing — pull out every "data: ..." line and try to
    # parse each as JSON. An SSE stream can contain multiple events, so we
    # walk from the last event backwards and return the first one that's
    # valid JSON (the final event is almost always the actual tool result).
    data_lines = [
        line[len("data:"):].strip()
        for line in stripped.splitlines()
        if line.strip().startswith("data:")
    ]

    for line in reversed(data_lines):
        if not line or line == "[DONE]":
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue

    return None


def execute_remote_tool(tool_name: str, arguments: dict) -> list:
    session_id = get_mcp_session()
    headers = dict(IMAGE_HEADERS)
    headers["Mcp-Session-Id"] = session_id

    # Strictly sanitize arguments to prevent Pydantic extra_forbidden rejections
    if tool_name == "kapruka_search_products" and "query" in arguments:
        arguments = {"q": arguments.get("query")}

    elif tool_name == "kapruka_track_order":
        order_val = str(arguments.get("order_number", "")).strip()
        arguments = {"order_number": order_val}

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

        data = _parse_mcp_body(raw_text)

        if data is None:
            print(f"🚨 MCP CLIENT ERROR: Could not parse MCP response body. Raw response was: {raw_text[:500]!r}")
            return []

        if data and "result" in data:
            result_data = data["result"]
            if "content" in result_data and isinstance(result_data["content"], list):
                for block in result_data["content"]:
                    if block.get("type") == "text":
                        text_val = block.get("text", "[]")
                        try:
                            return json.loads(text_val)
                        except json.JSONDecodeError:
                            return text_val
            return result_data

        if data and "error" in data:
            print(f"🚨 MCP TOOL ERROR: {data['error']}")
            return []

    except Exception as e:
        print(f"🚨 MCP CLIENT ERROR: {e}")
    return []