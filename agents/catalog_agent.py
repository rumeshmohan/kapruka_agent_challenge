import json
import re
from openai import OpenAI
from utils.config import get_config, get_api_key
from utils.mcp_client import execute_remote_tool

# ------------------------------------------------------------------
# kapruka_search_products supports response_format="json", confirmed via
# inspect_search_schema.py, which returns real structured data including
# image_url — unlike the default Markdown report, which has no images at
# all. We request JSON explicitly and normalize its {"results": [...]}
# shape into the flat product dicts (name, id, price, currency,
# stock_status, url, image_url) the rest of catalog_agent.py /
# reflection_loop.py already expect.
#
# IMPORTANT: mcp_client.py's execute_remote_tool auto-rewrites any
# "query" key into {"q": ...} and drops every other key in the process
# (to satisfy the tool's actual param name, "q"). That would silently
# strip response_format if we let it happen. So we build the real
# argument dict ourselves here — using "q" directly — and never pass a
# "query" key into execute_remote_tool, sidestepping that rewrite entirely.
#
# A Markdown parser is kept as a defensive fallback only, in case the
# server ever ignores response_format and returns text anyway.
# ------------------------------------------------------------------

_NAME_RE = re.compile(r'^\*\*\d+\.\s*(.+?)\*\*\s*$')
_ID_RE = re.compile(r'ID:\s*`([^`]+)`')
_PRICE_RE = re.compile(r'LKR\s*([\d,]+(?:\.\d+)?)')
_STOCK_RE = re.compile(r'(In stock[^\u00b7|\n]*|Out of stock[^\u00b7|\n]*)', re.IGNORECASE)
_LINK_RE = re.compile(r'\[View product\]\(([^)]+)\)')


def parse_search_results_markdown(md: str) -> list:
    if not md or not isinstance(md, str):
        return []

    products = []
    current = {}

    for raw_line in md.strip().splitlines():
        line = raw_line.strip()

        name_match = _NAME_RE.match(line)
        if name_match:
            if current.get("name"):
                products.append(current)
            current = {"name": name_match.group(1).strip(), "image_url": None}
            continue

        if not current:
            continue

        id_match = _ID_RE.search(line)
        if id_match:
            current["id"] = id_match.group(1).strip()

        price_match = _PRICE_RE.search(line)
        if price_match:
            current["price"] = price_match.group(1).replace(",", "")
            current["currency"] = "LKR"

        stock_match = _STOCK_RE.search(line)
        if stock_match:
            current["stock_status"] = stock_match.group(1).strip(" .").strip()

        link_match = _LINK_RE.search(line)
        if link_match:
            current["url"] = link_match.group(1).strip()

    if current.get("name"):
        products.append(current)

    return products


def _normalize_search_results(raw_results):
    """Accepts the real JSON shape ({"results": [...]}), a bare list, or a
    Markdown string (defensive fallback), and always returns a flat list
    of product dicts with a consistent shape."""
    if isinstance(raw_results, dict) and isinstance(raw_results.get("results"), list):
        normalized = []
        for item in raw_results["results"]:
            price_obj = item.get("price") or {}
            normalized.append({
                "id": item.get("id"),
                "name": item.get("name"),
                "price": price_obj.get("amount"),
                "currency": price_obj.get("currency", "LKR"),
                "stock_status": "In stock" if item.get("in_stock") else "Out of stock",
                "url": item.get("url"),
                "image_url": item.get("image_url"),
            })
        return normalized
    if isinstance(raw_results, list):
        return raw_results
    if isinstance(raw_results, str):
        return parse_search_results_markdown(raw_results)
    return []


def _search_products(query: str) -> list:
    """Calls kapruka_search_products with the real param name ('q') and
    response_format='json' directly — bypassing execute_remote_tool's
    'query' -> {'q': ...} auto-rewrite so response_format isn't dropped."""
    raw = execute_remote_tool("kapruka_search_products", {"q": query, "response_format": "json"})
    return _normalize_search_results(raw)

BASE_URL_MAP = {
    "ollama":      "http://localhost:11434/v1",
    "openrouter":  "https://openrouter.ai/api/v1",
    "groq":        "https://api.groq.com/openai/v1",
    "gemini":      "https://generativelanguage.googleapis.com/v1beta/openai/",
    "openai":      "https://api.openai.com/v1",
}

_client = None
_model = None

def _get_client():
    global _client, _model
    if _client is None:
        config = get_config()
        provider = config.get("provider.default", "gemini")
        _model = config.get_model(provider, "general")
        _client = OpenAI(
            api_key=get_api_key(provider),
            base_url=BASE_URL_MAP.get(provider, "https://generativelanguage.googleapis.com/v1beta/openai/")
        )
    return _client, _model

SYSTEM_PROMPT = """
You are an elite, proactive Kapruka Concierge Sales Specialist.
Your goal is to guide customers to the perfect purchase by offering thoughtful curation.

🌟 INNOVATIVE RULES - CULTURAL PAIRING & UPSELLING:
1. Always suggest premium combinations unique to Sri Lankan gifting customs.
- If the user is looking for a CAKE, you MUST proactively call the tool for 'flowers' as well, or blend them into your recommendations.
- If looking for ICE CREAM, FRUITS, or CHOCOLATES, suggest pairing it with premium toppings, a physical greeting card, or a soft toy.
2. MULTILINGUAL SUPPORT: Mirror the user's exact current query language immediately (English, Singlish, Tanglish, Sinhala Script, or Tamil Script).
- If the user types in TAMIL, your text response copy MUST be natively in pure, warm Tamil script.
- If the user types in SINHALA, your text response copy MUST be natively in pure, warm Sinhala script.
3. CRITICAL TOOL RULE: Pass ONLY clean, singular English keywords to 'kapruka_search_products' (e.g., convert 'ஐஸ்கிரீம்' or 'කේක්' to 'cake' or 'ice cream').
4. Keep the written copy under 4 sentences. Introduce the main item and smoothly highlight why the companion pairing makes it the perfect gift gesture.
5. LINK FORMATTING RULE: Do NOT output raw markdown or text links (e.g. [Name](URL)) in your
   conversational reply, and do NOT print raw JSON or text lists of products at the end of
   your message. The UI already renders dedicated interactive catalog cards for every item in
   the products payload - refer to products by name only and let the cards do the rest.
"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "kapruka_search_products",
            "description": "Search the live Kapruka product catalog by keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search keyword in pure English (e.g. 'cake', 'flowers', 'ice cream')."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def handle_catalog_query(query: str, history: str = "") -> dict:
    text = ""
    combined_products = []

    try:
        client, model = _get_client()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Conversation History:\n{history}\n\nCurrent User Query: {query}"}
        ]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.3
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            primary_query = json.loads(tool_calls[0].function.arguments).get("query", "").strip()

            if not primary_query or any(ord(char) > 127 for char in primary_query):
                primary_query = "cake" if "කේක්" in query or "cake" in query.lower() else "ice cream"

            primary_results = _search_products(primary_query)
            combined_products.extend(primary_results[:3])

            upsell_query = "flowers" if "cake" in primary_query.lower() else "chocolate"
            if primary_query.lower() not in ["flowers", "flower", "chocolate", "chocolates"]:
                upsell_results = _search_products(upsell_query)
                for item in upsell_results[:1]:
                    item["name"] = f"🎁 [Recommended Pairing] {item.get('name')}"
                    combined_products.append(item)

            messages.append(response_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_calls[0].id,
                "name": "kapruka_search_products",
                "content": json.dumps(combined_products)
            })

            second_response = client.chat.completions.create(model=model, messages=messages, temperature=0.3)
            # Gemini's OpenAI-compat endpoint can return content=None (e.g. after
            # tool results, if it declines to add extra commentary). Guard against
            # that instead of crashing on .strip().
            text = (second_response.choices[0].message.content or "").strip()
            if not text:
                text = "Here are a few options I found for you — take a look below! 🎁"
        else:
            text = (response_message.content or "").strip()
            if not text:
                text = "Could you tell me a bit more about what you're looking for?"

    except Exception as e:
        print(f"🚨 CATALOG AGENT ERROR: {e}")
        # Dynamic fallback response generator based on language tracking indices
        if any(ord(c) >= 0x0D80 and ord(c) <= 0x0DFF for c in query):
            text = "කණගාටුයි, සජීවී නාමාවලිය පරීක්ෂා කිරීමේදී ගැටලුවක් ඇති විය. කරුණාකර නැවත උත්සාහ කරන්න!"
        elif any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in query):
            text = "மன்னிக்கவும், நேரடி அட்டவணையைச் சரிபார்ப்பதில் சிக்கல் ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்!"
        else:
            text = "Mata live catalog eka check karanna podi prashnayak awa. Please try again shortly!"

    image_urls = [item.get("image_url") for item in combined_products if item.get("image_url")]

    return {
        "text":       text,
        "image_urls": image_urls,
        "products":   combined_products
    }