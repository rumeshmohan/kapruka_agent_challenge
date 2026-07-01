import json
from openai import OpenAI
from utils.config import get_config, get_api_key
from utils.mcp_client import execute_remote_tool

config   = get_config()
PROVIDER = config.get("provider.default", "groq")
MODEL    = config.get_model(PROVIDER, "general")

try:
    api_key = "ollama-local" if PROVIDER == "ollama" else get_api_key(PROVIDER)
except ValueError as e:
    raise ValueError(f"Logistics agent error: {e}")

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

client = OpenAI(api_key=api_key, base_url=BASE_URL_MAP.get(PROVIDER))

SYSTEM_PROMPT = """
You are the Kapruka Customer Service Agent handling Logistics and Delivery.
RULES:
1. Be polite, clear, and concise (under 3 sentences).
2. ALWAYS use the 'kapruka_check_delivery' tool to check live delivery fees and times.
3. MULTILINGUAL SUPPORT: Mirror the user's language. 
   - If they ask in Tanglish or pure Tamil, reply warmly in Tanglish.
   - If they ask in Singlish or pure Sinhala, reply warmly in Singlish/Sinhala.
   - Otherwise, default to English.
4. If the user does not provide a city or address, politely ask them where they want the item delivered before calling the tool.
5. Format prices nicely (e.g., Rs. 400).
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

def handle_logistics_query(query: str, history: str = "") -> str:
    user_msg = f"History:\n{history}\n\nQuery: {query}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
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
                model=MODEL,
                messages=messages,
                temperature=0.3,
            )
            return second_response.choices[0].message.content.strip()
        else:
            return response_message.content.strip()

    except Exception as e:
        return f"I'm sorry, our live logistics system is currently unavailable. Error: {e}"