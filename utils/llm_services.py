import logging
from openai import OpenAI
from utils.config import get_api_key, get_config

logger = logging.getLogger(__name__)

_BASE_URLS = {
    "ollama":     "http://localhost:11434/v1",
    "google":     "https://generativelanguage.googleapis.com/v1beta/openai/",
    "gemini":     "https://generativelanguage.googleapis.com/v1beta/openai/",
    "groq":       "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}

class LLMProvider:
    def __init__(self, tier: str = "general"):
        self.config = get_config()
        provider = self.config.get("provider.default", "google")

        if provider == "ollama":
            base_url = _BASE_URLS["ollama"]
            api_key = "ollama"
        elif provider in ("google", "gemini"):
            base_url = _BASE_URLS["google"]
            api_key = get_api_key(provider)
        elif provider in _BASE_URLS:
            base_url = _BASE_URLS[provider]
            api_key = get_api_key(provider)
        else:
            base_url = None
            api_key = get_api_key("openai")

        # Lowered timeout to 45s to beat Railway's 100s proxy timeout
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=45)
        
        raw_model = self.config.get_model(provider, tier)
        self.model = raw_model.split("/")[-1] if "/" in raw_model else raw_model

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.config.get("llm.temperature", 0.2),
                max_tokens=self.config.get("llm.max_tokens", 1024),
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ API Error on model {self.model}: {e}")
            raise

def get_llm(tier: str = "general") -> LLMProvider:
    return LLMProvider(tier=tier)