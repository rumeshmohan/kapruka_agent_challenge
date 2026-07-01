import json
from utils.llm_services import get_llm

CRITIC_PROMPT = """
You are the Kapruka Guardrail Critic Agent. 
Your single responsibility is to cross-examine a proposed catalog response against a customer's known profile to ensure maximum safety.

CRITICAL RULES:
1. If the user profile states a recipient has an allergy (e.g., "dairy", "nuts"), check if the proposed response contains ANY items matching that allergy.
2. If the response contains an allergen, you MUST trigger a failure by responding with exactly: [REJECT]
3. If the response is completely safe, respond with exactly: [APPROVE]

Output ONLY [APPROVE] or [REJECT]. Absolutely no commentary.
"""

REWRITE_PROMPT = """
You are the Kapruka Self-Correction Agent.
An internal guardrail rejected a proposed response because it contained items that violate a customer's allergy restrictions.

USER PROFILE CONTEXT:
{profile_context}

ORIGINAL QUERY:
{query}

Your job is to rewrite the catalog response to be completely safe. Remove any products that violate the allergies mentioned in the profile. Pivot beautifully and suggest safe alternatives instead.
CRITICAL: Do not mention that a guardrail was triggered, do not say "corrected", and do not output any warning labels. Simply provide a natural, warm response to the customer.
Maintain the exact same language (English, Singlish, or Tanglish) as the query.
"""

def evaluate_and_reflect(query: str, proposed_response: dict, profile_context: str) -> dict:
    text_content = proposed_response.get("text", "")
    products = proposed_response.get("products", [])
    
    if not profile_context or not products:
        return proposed_response

    try:
        critic_input = f"USER PROFILE:\n{profile_context}\n\nPROPOSED CATALOG RESPONSE:\n{text_content}\n\nITEMS:\n{json.dumps(products)}"
        critic_verdict = get_llm(tier="strong").generate(prompt=critic_input, system_prompt=CRITIC_PROMPT).strip()

        if "[REJECT]" in critic_verdict:
            rewrite_sys = REWRITE_PROMPT.format(profile_context=profile_context, query=query)
            rewrite_input = f"Rejected Response:\n{text_content}\n\nItems List:\n{json.dumps(products)}"
            
            corrected_text = get_llm(tier="strong").generate(prompt=rewrite_input, system_prompt=rewrite_sys).strip()
            
            try:
                profile_data = json.loads(profile_context)
                recipients = profile_data.get("recipients", {})
            except Exception:
                recipients = {}

            allergies = []
            for r_data in recipients.values():
                if isinstance(r_data, dict) and "allergies" in r_data:
                    allergies.extend([str(a).lower() for a in r_data["allergies"]])

            if "nuts" in allergies or "nut" in allergies or "cashew" in allergies:
                allergies.extend(["ferrero", "rocher", "nutella", "peanut", "cashew", "almond", "walnut", "skyline"])

            filtered_products = []
            filtered_images = []
            for p in products:
                p_name = p.get("name", "").lower()
                p_desc = p.get("description", "").lower()
                
                is_allergen = False
                for allergy in allergies:
                    if allergy in p_name or allergy in p_desc:
                        is_allergen = True
                        break
                
                if not is_allergen:
                    filtered_products.append(p)
                    if p.get("image_url"):
                        filtered_images.append(p["image_url"])

            return {
                "text":        corrected_text,
                "image_urls":  filtered_images,
                "products":    filtered_products
            }
    except Exception:
        pass

    return proposed_response