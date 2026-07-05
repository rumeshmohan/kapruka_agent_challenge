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
            raise ValueError(f"Checkout agent error: {e}")
        _client = OpenAI(api_key=api_key, base_url=BASE_URL_MAP.get(provider, "https://api.openai.com/v1"))
    return _client, _model

# ------------------------------------------------------------------
# Real kapruka_create_order schema (from inspect_checkout_schema.py):
#   params.cart         -> list[{product_id, quantity, icing_text?}]
#   params.recipient    -> {name, phone}
#   params.delivery     -> {address, city, location_type?, date, instructions?}
#   params.sender       -> {name, anonymous?}
#   params.gift_message -> optional str
#   params.currency     -> optional str (default LKR)
# We build `cart` ourselves from cart_items, so the LLM only needs to
# collect recipient / delivery / sender / gift_message from the user.
# ------------------------------------------------------------------

SYSTEM_PROMPT = """
You are the Kapruka Checkout Concierge.
Your goal is to finalize the customer's order.

Before calling the checkout tool, you MUST collect ALL of the following from the conversation:
- recipient name and phone number
- delivery address (street/house), delivery city, and delivery date (YYYY-MM-DD, today or later)
- sender's name (the person paying/sending the gift), and whether they want to stay anonymous
- (optional) a gift message to print on the card
- (optional) location type: house, apartment, office, or other (default house if not mentioned)

RULES:
1. If any REQUIRED field above is missing, ask the customer for it conversationally instead of guessing or calling the tool.
2. MULTILINGUAL SUPPORT: Mirror the user's language.
   - If they converse in Tanglish or pure Tamil, reply warmly in Tanglish.
   - If they converse in Singlish or pure Sinhala, reply warmly in Singlish/Sinhala.
   - Otherwise, default to English.
3. Once you have every required field, ALWAYS use the 'kapruka_create_order' tool to generate the payment link. Do not invent placeholder values.
4. Format the payment link beautifully using Markdown so it stands out.
5. Be incredibly warm and express excitement about their purchase.
"""

CHECKOUT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "kapruka_create_order",
            "description": "Create a live guest checkout order on Kapruka and return a secure payment link. The cart is filled in automatically from the customer's current cart — only provide recipient, delivery, sender, and optional gift_message/currency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "object",
                        "description": "Who the order is delivered to.",
                        "properties": {
                            "name": {"type": "string", "description": "Recipient name shown on the order."},
                            "phone": {"type": "string", "description": "Recipient phone, E.164 (+9477...) or local SL (077...) format."}
                        },
                        "required": ["name", "phone"]
                    },
                    "delivery": {
                        "type": "object",
                        "description": "Delivery details.",
                        "properties": {
                            "address": {"type": "string", "description": "Street address."},
                            "city": {"type": "string", "description": "Delivery city in Sri Lanka."},
                            "location_type": {
                                "type": "string",
                                "description": "One of: house, apartment, office, other. Default house.",
                            },
                            "date": {"type": "string", "description": "Delivery date, YYYY-MM-DD, today or future (Asia/Colombo)."},
                            "instructions": {"type": "string", "description": "Optional free-form delivery instructions."}
                        },
                        "required": ["address", "city", "date"]
                    },
                    "sender": {
                        "type": "object",
                        "description": "Who is sending/paying for the gift.",
                        "properties": {
                            "name": {"type": "string", "description": "Sender name shown on the gift card."},
                            "anonymous": {"type": "boolean", "description": "If true, gift card shows 'Anonymous' instead of the sender name. Default false."}
                        },
                        "required": ["name"]
                    },
                    "gift_message": {
                        "type": "string",
                        "description": "Optional message to print on the physical gift card (max 300 chars)."
                    },
                    "currency": {
                        "type": "string",
                        "description": "Pricing currency: LKR (default), USD, GBP, AUD, CAD, EUR."
                    }
                },
                "required": ["recipient", "delivery", "sender"]
            }
        }
    }
]


def _build_cart(cart_items: list) -> list:
    """Builds the params.cart list the MCP tool actually expects."""
    cart = []
    for item in cart_items:
        product_id = item.get("id") or item.get("product_id") or item.get("name")
        if not product_id:
            continue
        entry = {
            "product_id": product_id,
            "quantity": item.get("quantity", 1),
        }
        if item.get("icing_text"):
            entry["icing_text"] = item["icing_text"]
        cart.append(entry)
    return cart


def handle_checkout_query(query: str, cart_items: list, history: str = "") -> dict:
    if not cart_items:
        return {"text": "Your cart is currently empty! Let me know if you need help finding the perfect gift.", "checkout_data": None}

    cart_context = f"CURRENT CART STATUS: {json.dumps(cart_items)}\n"
    user_msg = f"{cart_context}History:\n{history}\n\nQuery: {query}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    ]

    try:
        client, model = _get_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=CHECKOUT_TOOLS,
            tool_choice="auto",
            temperature=0.2,
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # Always build cart ourselves from the real cart state —
                # never trust/accept a cart the LLM might invent.
                function_args["cart"] = _build_cart(cart_items)

                # Force structured JSON instead of the tool's default Markdown
                # report, so the frontend gets a reliable checkout_url /
                # order_ref / summary to drive the payment page — no Markdown
                # parsing needed for this one, unlike search/tracking.
                function_args["response_format"] = "json"

                tool_result = execute_remote_tool(function_name, function_args)

                checkout_data = None
                if isinstance(tool_result, dict) and tool_result.get("checkout_url"):
                    checkout_data = tool_result

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(tool_result)
                })

            second_response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.4,
            )
            text = (second_response.choices[0].message.content or "").strip()
            if not text:
                text = "Your order is ready! Tap below to complete payment. 🎁" if checkout_data else \
                       "I'm sorry, I couldn't finalize the order. Please try again."
            return {"text": text, "checkout_data": checkout_data}
        else:
            return {"text": (response_message.content or "").strip(), "checkout_data": None}

    except Exception:
        return {
            "text": "I'm sorry, I encountered an error while setting up your secure checkout. Please try again in a moment.",
            "checkout_data": None,
        }