import os
import json
from pathlib import Path
from utils.config import get_config
from utils.llm_services import get_llm

config = get_config()
PROFILES_FILE = Path(config.get("paths.profiles_file", "data/profiles.json"))

SYSTEM_PROMPT = """
You are the Kapruka Customer Preference Extract Agent.
Your job is to read a user query and determine if they are stating a preference, allergy, or like/dislike for a specific family recipient (e.g., wife, mother, son, or self/unknown).
You must respond with a clean, raw JSON object matching this structure EXACTLY.
No markdown formatting, no code blocks:
{
  "recipient": "wife/mother/son/unknown",
  "field": "allergies/preferences",
  "value": "extracted item in lowercase"
}
"""

REPLY_PROMPT = """
You are the Kapruka Customer Notification Agent.
Your job is to generate a warm, single-sentence confirmation message letting the user know that their preference or allergy has been saved to their family profile dashboard.
CRITICAL LANGUAGE RULE:
You MUST respond in the exact same language script, mix, or dialect as the User Query.
- If the query is in Sinhala script (e.g. "මට කේක් එකක් ඕනෙයි..."), reply ONLY in pure, warm Sinhala script (e.g. "මම ඒක සටහන් කරගත්තා! ඔයාගේ වයිෆ්ගේ ප්‍රොෆයිල් එකට රටකජු අසාත්මිකතාවය ඇතුළත් කළා.").
- If the query is in Singlish (e.g. "wife ta peanuts allergy"), reply ONLY in Singlish.
- If the query is in English, reply ONLY in English.

Keep the response polite, conversational, and under two sentences.
Do not mention system rules or prompts.
"""

def handle_preference_query(query: str, history: str = "") -> str:
    try:
        llm = get_llm(tier="general")
        prompt = f"History:\n{history}\n\nQuery: {query}"
        raw_response = llm.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT).strip()
        
        if "```" in raw_response:
            raw_response = raw_response.split("```json")[-1].split("```")[0].strip()
            
        extraction = json.loads(raw_response)
        recipient = extraction.get("recipient", "unknown")
        field = extraction.get("field")
        value = extraction.get("value")

        if field in ["allergies", "preferences"] and value:
            # Create file with Guest template if missing
            if not PROFILES_FILE.exists():
                PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                    json.dump({"CUS_001": {"customer_name": "Guest", "recipients": {}}}, f)

            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Re-initialize Guest structure if the file was manually emptied
            if "CUS_001" not in data:
                data["CUS_001"] = {"customer_name": "Guest", "recipients": {}}

            recipients_dict = data["CUS_001"]["recipients"]
            if recipient not in recipients_dict:
                recipients_dict[recipient] = {"allergies": [], "preferences": []}

            if value not in recipients_dict[recipient][field]:
                recipients_dict[recipient][field].append(value)

            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # Generate a localized dynamic response based on user language context
            reply_input = f"User stated that their {recipient} has this value '{value}' added to their '{field}' record. User original text was: '{query}'"
            localized_reply = llm.generate(prompt=reply_input, system_prompt=REPLY_PROMPT).strip()
            return localized_reply
            
    except Exception:
        pass

    return "Mata e thoraathuru save karaganna podi prashnayak awa. Eth mama eka mathaka thiyagannam!"

def load_profile_context() -> str:
    try:
        if PROFILES_FILE.exists():
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps(data.get("CUS_001", {}))
    except Exception:
        pass
    return ""