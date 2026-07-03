import json
from openai import OpenAI
from utils.config import get_config, get_api_key
from utils.mcp_client import execute_remote_tool

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

            primary_results = execute_remote_tool("kapruka_search_products", {"query": primary_query})
            if isinstance(primary_results, list):
                combined_products.extend(primary_results[:3])

            upsell_query = "flowers" if "cake" in primary_query.lower() else "chocolate"
            if primary_query.lower() not in ["flowers", "flower", "chocolate", "chocolates"]:
                upsell_results = execute_remote_tool("kapruka_search_products", {"query": upsell_query})
                if isinstance(upsell_results, list):
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
            text = second_response.choices[0].message.content.strip()
        else:
            text = response_message.content.strip()

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