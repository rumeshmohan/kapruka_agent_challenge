import json
import re
import ast
from openai import OpenAI
from utils.config import get_config, get_api_key
from utils.mcp_client import execute_remote_tool

BASE_URL_MAP = {
    "ollama":      "http://localhost:11434/v1",
    "openrouter":  "https://openrouter.ai/api/v1",
    "groq":        "https://api.groq.com/openai/v1",
    "gemini":      "https://generativelanguage.googleapis.com/v1beta/openai/",
    "openai":      "https://api.openai.com/v1",
    "cohere":      "https://api.cohere.ai/compatibility/v1",
    "deepseek":    "https://api.deepseek.com/v1",
    "anthropic":   "https://api.anthropic.com/v1",
}

_client = None
_model = None

def _get_client():
    global _client, _model
    if _client is None:
        config = get_config()
        provider = config.get("provider.default", "groq")
        _model = config.get_model(provider, "general")
        try:
            api_key = "ollama-local" if provider == "ollama" else get_api_key(provider)
        except ValueError as e:
            raise ValueError(f"Logistics agent error: {e}")
        _client = OpenAI(api_key=api_key, base_url=BASE_URL_MAP.get(provider))
    return _client, _model

SYSTEM_PROMPT = """
You are the Kapruka Customer Service Agent handling Logistics and Delivery.
RULES:
1. Be polite, clear, and concise (under 3 sentences).
2. ALWAYS use the 'kapruka_check_delivery' tool to check live delivery fees and times.
3. MULTILINGUAL SUPPORT: Mirror the user's language. 
   - If they ask in Tanglish or pure Tamil, reply warmly in Tanglish.
   - If they ask in Singlish or pure Sinhala, reply warmly in Singlish/Sinhala.
   - Otherwise, default to English.
"""

LOGISTICS_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "kapruka_check_delivery",
            "description": "Check live Kapruka delivery availability, times, and fees for a specific location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string", 
                        "description": "The city or district for delivery (e.g., 'Kandy', 'Colombo 4')"
                    }
                },
                "required": ["city"]
            }
        }
    }
]


# ------------------------------------------------------------------
# Kapruka's order-tracking MCP tool returns a pre-formatted Markdown
# report (table + delivery address + progress timeline), NOT JSON.
# It's also mis-encoded on Kapruka's end: every em dash ("—") comes
# through as a mangled "â" character (or similar junk bytes). This
# parser is defensive about that: instead of matching the mangled
# separator character literally, it locates the meaningful token
# (a timestamp, a table key, etc.) and strips whatever non-alphanumeric
# junk surrounds it, so it keeps working even if the mangling changes.
# ------------------------------------------------------------------

_HEADER_RE = re.compile(r'^##\s*Order\s*`([^`]+)`\s*(.+)$')
_TABLE_ROW_RE = re.compile(r'^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|$')
_EVENT_RE = re.compile(
    r'^-?\s*([A-Za-z]{3}\s+\d{1,2},\s*\d{4}\s+\d{1,2}:\d{2}\s*[AaPp][Mm])\s*(.*)$'
)


def _strip_junk_prefix(text: str) -> str:
    """Strip leading separator junk (mangled dashes/encoding artifacts)."""
    return re.sub(r'^[^A-Za-z0-9(]+', '', text or "").strip()


def parse_tracking_markdown(md: str) -> dict:
    """
    Parses the Kapruka 'kapruka_track_order' Markdown report into the
    structured shape the frontend's OrderTrackingCard expects.

    Returns a dict with keys:
        order_number, status, eta, total, payment_ref, ordered_date,
        shipped_date, recipient_name, recipient_address, recipient_phone,
        greeting, notes, events (list of {timestamp, description})

    Falls back gracefully: any section that can't be found is left as
    None / [] rather than raising, since Kapruka's report format may
    vary slightly between orders (e.g. no "Shipped" row yet).
    """
    if not md or not isinstance(md, str):
        return None

    lines = [l.rstrip() for l in md.strip().splitlines()]
    result = {
        "order_number": None,
        "status": None,
        "eta": None,
        "total": None,
        "payment_ref": None,
        "ordered_date": None,
        "shipped_date": None,
        "recipient_name": None,
        "recipient_address": None,
        "recipient_phone": None,
        "greeting": None,
        "notes": None,
        "events": [],
    }

    section = None  # None | "delivering" | "progress"
    delivering_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        header_match = _HEADER_RE.match(stripped)
        if header_match:
            result["order_number"] = header_match.group(1).strip()
            result["status"] = _strip_junk_prefix(header_match.group(2))
            continue

        if stripped.startswith("**Delivering to**"):
            section = "delivering"
            continue
        if stripped.startswith("**Greeting:**"):
            section = None
            result["greeting"] = stripped.split("**Greeting:**", 1)[1].strip()
            continue
        if stripped.startswith("**Notes:**"):
            section = None
            result["notes"] = stripped.split("**Notes:**", 1)[1].strip()
            continue
        if stripped.startswith("**Progress**"):
            section = "progress"
            continue
        if stripped.startswith("_"):
            # Trailing italic footer note, e.g. "_live tracking available..._"
            section = None
            continue

        table_match = _TABLE_ROW_RE.match(stripped)
        if table_match and section is None:
            key_raw = table_match.group(1).strip()
            if set(key_raw) <= {"-"}:
                # Markdown table separator row, e.g. "|---|---|"
                continue
            key = key_raw.lower()
            val = table_match.group(2).strip()

            if key == "total":
                try:
                    parsed_val = ast.literal_eval(val)
                    if isinstance(parsed_val, dict):
                        currency = parsed_val.get("currency", "").strip()
                        amount = parsed_val.get("value", "")
                        result["total"] = f"{currency} {amount}".strip()
                    else:
                        result["total"] = val
                except Exception:
                    result["total"] = val
            elif key == "payment":
                result["payment_ref"] = val
            elif key == "ordered":
                result["ordered_date"] = val
            elif key == "shipped":
                result["shipped_date"] = val
            elif key == "delivery date":
                result["eta"] = val
            continue

        if section == "delivering" and stripped.startswith("-"):
            item = stripped.lstrip("-").strip()
            # Drop stray HTML artifacts like a trailing "<BR"
            item = re.split(r'<\s*BR', item, flags=re.IGNORECASE)[0].strip()
            if item:
                delivering_lines.append(item)
            continue

        if section == "progress" and stripped.startswith("-"):
            event_match = _EVENT_RE.match(stripped)
            if event_match:
                timestamp, rest = event_match.group(1), event_match.group(2)
                description = _strip_junk_prefix(rest)
                if description:
                    result["events"].append({
                        "timestamp": timestamp,
                        "description": description,
                    })
            continue

    if delivering_lines:
        result["recipient_name"] = delivering_lines[0]
        phone_idx = None
        for i, item in enumerate(delivering_lines[1:], start=1):
            if re.search(r'\d{3}[\s-]?\d{6,7}', item):
                phone_idx = i
                break
        if phone_idx is not None:
            result["recipient_phone"] = delivering_lines[phone_idx]
            address_parts = delivering_lines[1:phone_idx]
        else:
            address_parts = delivering_lines[1:]
        if address_parts:
            result["recipient_address"] = ", ".join(address_parts)

    return result


def handle_logistics_query(query: str, history: str = "") -> dict:
    """
    Returns a dict of the shape:
    {
        "text": "<conversational reply>",
        "order_status": <structured tracking payload or None>
    }
    """
    # 🌟 CASE-INSENSITIVE PRIORITY BYPASS: Extract the tracking reference
    match = re.search(r'(vpay\d+[a-zA-Z0-9]*)', query, re.IGNORECASE)

    if match:
        order_number = match.group(1).upper()
        try:
            tool_result = execute_remote_tool("kapruka_track_order", {"order_number": order_number})

            if tool_result:
                # The MCP tool returns a Markdown report string (not JSON)
                # for this endpoint. Parse it into structured data for the
                # frontend's OrderTrackingCard. If it ever does come back
                # as a dict/list already, pass it straight through.
                if isinstance(tool_result, str):
                    order_status = parse_tracking_markdown(tool_result) or {"raw": tool_result}
                else:
                    order_status = tool_result

                return {
                    "text": f"Ayubowan! 🌺 Here's the latest on order **{order_number}**:",
                    "order_status": order_status
                }
            else:
                return {
                    "text": f"Ayubowan! 📦 I connected to the live tracking server, but order **{order_number}** has no delivery events logged yet. Please check back shortly.",
                    "order_status": None
                }
        except Exception as e:
            return {
                "text": f"Ayubowan! ⚠️ Couldn't fetch tracking logs for order {order_number}. Error: {e}",
                "order_status": None
            }

    user_msg = f"History:\n{history}\n\nQuery: {query}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    ]

    try:
        client, model = _get_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=LOGISTICS_TOOLS,
            tool_choice="auto",
            temperature=0.1, 
        )
        
        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_result = execute_remote_tool(function_name, function_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_result)
                })

            second_response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
            )
            return {"text": second_response.choices[0].message.content.strip(), "order_status": None}
        else:
            return {"text": response_message.content.strip(), "order_status": None}

    except Exception as e:
        return {
            "text": f"I'm sorry, our live logistics system is currently unavailable. Error: {e}",
            "order_status": None
        }