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

SYSTEM_PROMPT = """
You are the Kapruka Checkout Concierge.
Your goal is to finalize the customer's order.

RULES:
1. Before calling the checkout tool, ensure you know the delivery city, recipient phone number, and if they want a gift message.
2. MULTILINGUAL SUPPORT: Mirror the user's language. 
   - If they converse in Tanglish or pure Tamil, reply warmly in Tanglish.
   - If they converse in Singlish or pure Sinhala, reply warmly in Singlish/Sinhala.
   - Otherwise, default to English.
3. Once you have the details, ALWAYS use the 'kapruka_create_order' tool to generate the payment link.
4. Format the payment link beautifully using Markdown so it stands out.
5. Be incredibly warm and express excitement about their purchase.
"""

CHECKOUT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "kapruka_create_order",
            "description": "Create a live guest checkout order on Kapruka and return a secure payment link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Kapruka product IDs in the cart."
                    },
                    "delivery_city": {
                        "type": "string",
                        "description": "The destination city in Sri Lanka."
                    },
                    "recipient_phone": {
                        "type": "string",
                        "description": "Phone number for the delivery driver."
                    },
                    "gift_message": {
                        "type": "string",
                        "description": "Optional message to print on the physical gift card."
                    }
                },
                "required": ["item_ids", "delivery_city", "recipient_phone"]
            }
        }
    }
]

def handle_checkout_query(query: str, cart_items: list, history: str = "") -> str:
    if not cart_items:
        return "Your cart is currently empty! Let me know if you need help finding the perfect gift."

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
                function_args["item_ids"] = [item.get("id", item.get("name")) for item in cart_items]
                
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
                temperature=0.4,
            )
            return second_response.choices[0].message.content.strip()
        else:
            return response_message.content.strip()

    except Exception:
        return "I'm sorry, I encountered an error while setting up your secure checkout. Please try again in a moment."