import os
import re
from openai import OpenAI
from utils.config import get_config, get_api_key

config = get_config()
PROVIDER = config.get("provider.default", "groq")
MODEL = config.get_model(PROVIDER, "general")

try:
    api_key = "ollama-local" if PROVIDER == "ollama" else get_api_key(PROVIDER)
except ValueError as e:
    raise ValueError(f"Router agent error: {e}")

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

ROUTER_PROMPT = """
You are an expert intent router for Kapruka e-commerce.
The user may speak English, Singlish, or Tanglish.
CRITICAL RULE: If a user message contains a greeting AND a product/shopping request, you MUST classify it as [CATALOG].
Categorize into exactly one intent tag:
[CATALOG]    - Searching for or wanting to see products.
[LOGISTICS]  - Delivery areas, fees, shipping costs, or time frames.
[PREFERENCE] - Saving customer preferences, likes, or allergies.
[CHECKOUT]   - Ready to pay, finalize order, or proceed to payment links.
[CHITCHAT]   - Pure greetings or generic text with NO product mentions.

Output ONLY the intent tag.
"""

CATALOG_KEYWORDS    = {"cake", "cakes", "chocolate", "chocolates", "flower", "flowers", "bouquet", "gift", "gifts", "toy", "toys", "teddy", "hamper", "hampers"}
CHITCHAT_KEYWORDS   = {"hi", "hello", "hey", "thanks", "bye", "ayubowan", "vanakkam", "kohomada", "eppadi", "sthuthi", "nandri"}
LOGISTICS_KEYWORDS  = {"delivery", "shipping", "kandy", "colombo", "cost", "fee", "mila", "kiyada", "dawasa", "ewanna", "evvalavu", "anuppu"}
PREFERENCE_KEYWORDS = {"allergic", "allergy", "prefer", "likes", "dislikes", "favorite", "love", "loves", "hates", "kemathi", "akemathi"}
CHECKOUT_KEYWORDS   = {"checkout", "pay", "purchase", "order", "salli", "gewanna"}

def route_query(query: str) -> str:
    clean_query = re.sub(r'[^\w\s]', '', query.lower().strip())
    words = set(clean_query.split())

    if words & CATALOG_KEYWORDS:
        return "[CATALOG]"

    if words & CHITCHAT_KEYWORDS and len(words) <= 2:
        return "[CHITCHAT]"

    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.0,
        )
        intent = res.choices[0].message.content.strip()
        if intent in ["[CATALOG]", "[LOGISTICS]", "[PREFERENCE]", "[CHECKOUT]", "[CHITCHAT]"]:
            return intent
    except Exception:
        pass

    if words & CHECKOUT_KEYWORDS:   return "[CHECKOUT]"
    if words & LOGISTICS_KEYWORDS:  return "[LOGISTICS]"
    if words & PREFERENCE_KEYWORDS: return "[PREFERENCE]"
    if words & CHITCHAT_KEYWORDS:   return "[CHITCHAT]"
    
    return "[CATALOG]"