import gradio as gr
import sys
from pathlib import Path
import os

sys.path.append(str(Path(__file__).resolve().parent))

from main import run_agent_pipeline
from memory.session_buffer import SessionBuffer

# Try to import OpenAI for voice support
try:
    from openai import OpenAI
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# ─── Custom CSS ──────────────────────────────────────────────────────────────
custom_css = """
/* ── Global ─────────────────────────────────────────────────────── */
.gradio-container {
    max-width: 1600px !important;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* ── Left Sidebar ───────────────────────────────────────────────── */
.sidebar-container {
    background: linear-gradient(145deg, #0f0c29, #302b63, #24243e);
    border-radius: 16px;
    padding: 16px 12px;
    min-height: 80vh;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.sidebar-title {
    text-align: center;
    color: #fff !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px;
    margin-bottom: 4px !important;
    text-shadow: 0 0 20px rgba(138,100,255,0.5);
}

.sidebar-subtitle {
    text-align: center;
    color: rgba(255,255,255,0.5) !important;
    font-size: 11px !important;
    margin-bottom: 12px !important;
}

.sidebar-section-label {
    color: rgba(255,255,255,0.7) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 14px 0 6px 0 !important;
    padding-left: 4px;
}

.sidebar-divider {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 10px 0 !important;
}

/* ── Category Buttons ───────────────────────────────────────────── */
.category-btn button {
    width: 100% !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    padding: 10px 8px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #fff !important;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
    min-height: 42px !important;
    line-height: 1.2 !important;
}
.category-btn button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.35) !important;
    filter: brightness(1.15);
}

.cat-cakes button     { background: linear-gradient(135deg, #f093fb, #f5576c) !important; }
.cat-flowers button   { background: linear-gradient(135deg, #4facfe, #00f2fe) !important; }
.cat-choco button     { background: linear-gradient(135deg, #a18cd1, #fbc2eb) !important; }
.cat-toys button      { background: linear-gradient(135deg, #fccb90, #d57eeb) !important; }
.cat-hampers button   { background: linear-gradient(135deg, #a1c4fd, #c2e9fb) !important; color: #1a1a2e !important; }
.cat-icecream button  { background: linear-gradient(135deg, #ffecd2, #fcb69f) !important; color: #1a1a2e !important; }

/* ── Combo Buttons ──────────────────────────────────────────────── */
.combo-btn button {
    width: 100% !important;
    background: rgba(255,255,255,0.06) !important;
    border: 1px dashed rgba(255,255,255,0.2) !important;
    border-radius: 10px !important;
    color: #e0d4ff !important;
    padding: 9px 8px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
    min-height: 38px !important;
}
.combo-btn button:hover {
    background: rgba(138,100,255,0.2) !important;
    border-color: rgba(138,100,255,0.5) !important;
    transform: translateY(-1px) !important;
    color: #fff !important;
}

/* ── Sidebar Form Controls ──────────────────────────────────────── */
.sidebar-container .gr-dropdown,
.sidebar-container select,
.sidebar-container input[type="range"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
    color: #fff !important;
}

.sidebar-container label {
    color: rgba(255,255,255,0.65) !important;
    font-size: 12px !important;
}

.sidebar-container .gr-radio label span,
.sidebar-container .gr-check-radio label {
    color: rgba(255,255,255,0.8) !important;
}

/* ── Main Content ───────────────────────────────────────────────── */
.cart-item {
    padding: 8px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
}
.cart-total {
    font-size: 18px;
    font-weight: bold;
    padding: 15px 0;
    border-top: 2px solid #333;
    margin-top: 10px;
}
.product-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 15px;
    background: white;
    text-align: center;
    transition: box-shadow 0.2s;
}
.product-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.product-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
    border-radius: 6px;
    margin-bottom: 10px;
}
.product-name {
    font-size: 16px;
    font-weight: bold;
    margin: 10px 0 5px 0;
    color: #333;
}
.product-id {
    font-size: 12px;
    color: #666;
    margin: 5px 0;
}
.product-price {
    font-size: 18px;
    font-weight: bold;
    color: #0066cc;
    margin: 10px 0;
}

/* ── Active Filter Badges ───────────────────────────────────────── */
.filter-badge {
    display: inline-block;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    margin: 2px;
    letter-spacing: 0.3px;
}
"""

# ─── Audio Transcription ─────────────────────────────────────────────────────
def transcribe_audio(audio_path):
    """Transcribe audio using OpenAI Whisper API (supports multilingual)"""
    if not audio_path or not VOICE_AVAILABLE:
        return None

    try:
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "⚠️ Voice requires GROQ_API_KEY or OPENAI_API_KEY"

        if os.getenv("GROQ_API_KEY"):
            client = OpenAI(
                api_key=os.getenv("GROQ_API_KEY"),
                base_url="https://api.groq.com/openai/v1"
            )
            model = "whisper-large-v3"
        else:
            client = OpenAI(api_key=api_key)
            model = "whisper-1"

        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="text"
            )

        return transcript if isinstance(transcript, str) else transcript.text

    except Exception as e:
        return f"⚠️ Transcription error: {str(e)}"

# ─── Cart Display ─────────────────────────────────────────────────────────────
def format_cart_display(cart):
    """Format cart items for display in sidebar"""
    if not cart:
        return "<p style='color: #666;'>Your cart is empty</p>"

    cart_html = ""
    total = 0

    for idx, item in enumerate(cart):
        name = item.get("name", "Unknown")
        price = float(item.get("price", 0))
        total += price

        cart_html += f"""
        <div class="cart-item">
            <div>
                <strong>{name}</strong><br/>
                <span style="color: #0066cc; font-weight: bold;">LKR {price:,.2f}</span>
            </div>
        </div>
        """

    cart_html += f"""
    <div class="cart-total">
        Total: LKR {total:,.2f}
    </div>
    """

    return cart_html

# ─── Product Rendering ───────────────────────────────────────────────────────
def render_product_cards(products, current_products_state):
    """Render products as interactive Gradio components"""
    if not products:
        return [], gr.update(visible=False), current_products_state

    # Store products in state for "Add to Cart" callbacks
    product_components = []

    # Create rows of 3 products each
    num_products = min(len(products), 9)  # Limit to 9 products
    rows_needed = (num_products + 2) // 3

    for row_idx in range(rows_needed):
        row_products = products[row_idx * 3 : (row_idx + 1) * 3]
        product_components.append(row_products)

    return product_components, gr.update(visible=True), products


# ─── Enriched Query Builder ──────────────────────────────────────────────────
LANG_MAP = {
    "English": "",
    "සිංහල (Sinhala)": "Please respond in Sinhala script. ",
    "தமிழ் (Tamil)": "Please respond in Tamil script. ",
}

def build_enriched_query(base_query, price_min, price_max, city, language, occasion):
    """Compose a smarter prompt by injecting active filter context."""
    parts = []

    # Language hint
    lang_hint = LANG_MAP.get(language, "")
    if lang_hint:
        parts.append(lang_hint)

    # Core query
    parts.append(base_query)

    # Price context
    if price_min and price_max and (price_min > 500 or price_max < 25000):
        parts.append(f"(budget: LKR {int(price_min)} – {int(price_max)})")

    # City context
    if city and city != "Any City":
        parts.append(f"for delivery in {city}")

    # Occasion context
    if occasion and occasion != "Any Occasion":
        parts.append(f"for a {occasion.lower()}")

    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# GRADIO APP
# ═══════════════════════════════════════════════════════════════════════════════
with gr.Blocks(title="Kapi Shopping Agent") as demo:
    # ── Hidden state ──────────────────────────────────────────────────────────
    cart_state = gr.State([])
    products_state = gr.State([])
    session_memory_state = gr.State(SessionBuffer(max_pairs=5))

    gr.Markdown(
        """
        # 🛍️ Kapi - Smart Shopping Agent
        ### 🎤 Voice-Enabled! (සිංහල | தமிழ் | English)

        Your AI-powered shopping assistant for Kapruka!
        """
    )

    with gr.Row():
        # ═══════════════════════════════════════════════════════════════════════
        # LEFT SIDEBAR — Innovative Searches & Filters
        # ═══════════════════════════════════════════════════════════════════════
        with gr.Column(scale=1, elem_classes=["sidebar-container"]):
            gr.Markdown("### ✨ Smart Search", elem_classes=["sidebar-title"])
            gr.Markdown("Find the perfect gift instantly", elem_classes=["sidebar-subtitle"])

            # ── Quick Category Buttons ────────────────────────────────────────
            gr.Markdown("CATEGORIES", elem_classes=["sidebar-section-label"])

            with gr.Row():
                cat_cakes = gr.Button("🎂 Cakes", elem_classes=["category-btn", "cat-cakes"], size="sm")
                cat_flowers = gr.Button("💐 Flowers", elem_classes=["category-btn", "cat-flowers"], size="sm")
            with gr.Row():
                cat_choco = gr.Button("🍫 Chocolates", elem_classes=["category-btn", "cat-choco"], size="sm")
                cat_toys = gr.Button("🧸 Soft Toys", elem_classes=["category-btn", "cat-toys"], size="sm")
            with gr.Row():
                cat_hampers = gr.Button("🎁 Hampers", elem_classes=["category-btn", "cat-hampers"], size="sm")
                cat_icecream = gr.Button("🍨 Ice Cream", elem_classes=["category-btn", "cat-icecream"], size="sm")

            gr.Markdown("---", elem_classes=["sidebar-divider"])

            # ── Occasion / Gift Finder ────────────────────────────────────────
            gr.Markdown("OCCASION", elem_classes=["sidebar-section-label"])
            occasion_dropdown = gr.Dropdown(
                choices=["Any Occasion", "Birthday", "Anniversary", "Valentine's Day",
                         "New Year", "Get Well Soon", "Wedding", "Baby Shower", "Sympathy"],
                value="Any Occasion",
                label="",
                show_label=False,
                interactive=True,
            )

            gr.Markdown("---", elem_classes=["sidebar-divider"])

            # ── Price Range ───────────────────────────────────────────────────
            gr.Markdown("BUDGET (LKR)", elem_classes=["sidebar-section-label"])
            price_min_slider = gr.Slider(
                minimum=500, maximum=25000, value=500, step=500,
                label="Min Price", interactive=True,
            )
            price_max_slider = gr.Slider(
                minimum=500, maximum=25000, value=25000, step=500,
                label="Max Price", interactive=True,
            )

            gr.Markdown("---", elem_classes=["sidebar-divider"])

            # ── Delivery City ─────────────────────────────────────────────────
            gr.Markdown("DELIVERY CITY", elem_classes=["sidebar-section-label"])
            city_radio = gr.Radio(
                choices=["Any City", "Colombo", "Kandy", "Galle", "Matara", "Jaffna", "Kurunegala"],
                value="Any City",
                label="",
                show_label=False,
                interactive=True,
            )

            gr.Markdown("---", elem_classes=["sidebar-divider"])

            # ── Smart Combo Suggestions ───────────────────────────────────────
            gr.Markdown("COMBO IDEAS", elem_classes=["sidebar-section-label"])
            combo_cake_flower = gr.Button("🎂 + 💐  Cake & Flowers", elem_classes=["combo-btn"], size="sm")
            combo_choco_teddy = gr.Button("🍫 + 🧸  Chocolate & Teddy", elem_classes=["combo-btn"], size="sm")
            combo_hamper_card = gr.Button("🎁 + 💌  Hamper & Card", elem_classes=["combo-btn"], size="sm")

            gr.Markdown("---", elem_classes=["sidebar-divider"])

            # ── Language Toggle ───────────────────────────────────────────────
            gr.Markdown("LANGUAGE", elem_classes=["sidebar-section-label"])
            lang_radio = gr.Radio(
                choices=["English", "සිංහල (Sinhala)", "தமிழ் (Tamil)"],
                value="English",
                label="",
                show_label=False,
                interactive=True,
            )

        # ═══════════════════════════════════════════════════════════════════════
        # MAIN CONTENT (unchanged)
        # ═══════════════════════════════════════════════════════════════════════
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                height=450,
                show_label=False,
                avatar_images=(None, "🛍️")
            )

            # Product display area
            products_section = gr.Column(visible=False)
            with products_section:
                gr.Markdown("### ✨ Recommended Products")

                # Row 1
                with gr.Row():
                    prod_col_1 = gr.Column(scale=1)
                    with prod_col_1:
                        img_1 = gr.HTML("", visible=False)
                        name_1 = gr.Markdown("", visible=False)
                        id_1 = gr.Markdown("", visible=False)
                        price_1 = gr.Markdown("", visible=False)
                        btn_1 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

                    prod_col_2 = gr.Column(scale=1)
                    with prod_col_2:
                        img_2 = gr.HTML("", visible=False)
                        name_2 = gr.Markdown("", visible=False)
                        id_2 = gr.Markdown("", visible=False)
                        price_2 = gr.Markdown("", visible=False)
                        btn_2 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

                    prod_col_3 = gr.Column(scale=1)
                    with prod_col_3:
                        img_3 = gr.HTML("", visible=False)
                        name_3 = gr.Markdown("", visible=False)
                        id_3 = gr.Markdown("", visible=False)
                        price_3 = gr.Markdown("", visible=False)
                        btn_3 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

                # Row 2
                with gr.Row():
                    prod_col_4 = gr.Column(scale=1)
                    with prod_col_4:
                        img_4 = gr.HTML("", visible=False)
                        name_4 = gr.Markdown("", visible=False)
                        id_4 = gr.Markdown("", visible=False)
                        price_4 = gr.Markdown("", visible=False)
                        btn_4 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

                    prod_col_5 = gr.Column(scale=1)
                    with prod_col_5:
                        img_5 = gr.HTML("", visible=False)
                        name_5 = gr.Markdown("", visible=False)
                        id_5 = gr.Markdown("", visible=False)
                        price_5 = gr.Markdown("", visible=False)
                        btn_5 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

                    prod_col_6 = gr.Column(scale=1)
                    with prod_col_6:
                        img_6 = gr.HTML("", visible=False)
                        name_6 = gr.Markdown("", visible=False)
                        id_6 = gr.Markdown("", visible=False)
                        price_6 = gr.Markdown("", visible=False)
                        btn_6 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

            # Input area
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Type your message... (e.g., 'Show me chocolates')",
                    show_label=False,
                    scale=7,
                    lines=2
                )
                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="🎤",
                    show_label=False,
                    scale=2
                )
                submit = gr.Button("Send", scale=1, variant="primary")

            gr.Examples(
                examples=[
                    "Show me chocolate cakes",
                    "I need a birthday gift for my mom",
                    "Find flowers for delivery in Colombo",
                    "මම චොකලට් කේක් එකක් අවශ්‍යයි",
                    "எனக்கு பூக்கள் வேண்டும்"
                ],
                inputs=msg
            )

        # ═══════════════════════════════════════════════════════════════════════
        # RIGHT SIDEBAR — Cart (unchanged)
        # ═══════════════════════════════════════════════════════════════════════
        with gr.Column(scale=1):
            gr.Markdown("## 🛒 Shopping Cart")
            cart_display = gr.HTML("<p style='color: #666;'>Your cart is empty</p>")

            checkout_btn = gr.Button(
                "Proceed to Checkout",
                variant="primary",
                size="lg",
                interactive=False
            )

            gr.Markdown("---")

            clear_btn = gr.Button(
                "Clear Chat History 🗑️",
                variant="secondary"
            )

            gr.Markdown(
                """
                ---
                ### 🎤 Voice Support
                Speak in:
                - සිංහල (Sinhala)
                - தமிழ் (Tamil)
                - English
                - Mixed languages
                """
            )

    # ── Product component lists ───────────────────────────────────────────────
    product_imgs = [img_1, img_2, img_3, img_4, img_5, img_6]
    product_names = [name_1, name_2, name_3, name_4, name_5, name_6]
    product_ids = [id_1, id_2, id_3, id_4, id_5, id_6]
    product_prices = [price_1, price_2, price_3, price_4, price_5, price_6]
    product_btns = [btn_1, btn_2, btn_3, btn_4, btn_5, btn_6]

    # ═══════════════════════════════════════════════════════════════════════════
    # CORE FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def update_product_display(products):
        """Update all product card components"""
        updates = []

        for i in range(6):
            if i < len(products):
                prod = products[i]
                name = prod.get("name", "Unknown Product")
                price = prod.get("price", 0)
                image_url = prod.get("image_url", "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=400&q=80")
                prod_id = prod.get("id", name)

                # Create HTML img tag instead of passing URL
                img_html = f'<img src="{image_url}" style="width: 100%; height: 200px; object-fit: cover; border-radius: 8px;" alt="{name}" />'

                # Image (HTML), Name, ID, Price, Button
                updates.extend([
                    gr.update(value=img_html, visible=True),
                    gr.update(value=f"**{name}**", visible=True),
                    gr.update(value=f"ID: `{prod_id}`", visible=True),
                    gr.update(value=f"**LKR {float(price):,.2f}**", visible=True),
                    gr.update(visible=True, interactive=True)
                ])
            else:
                # Hide unused slots
                updates.extend([
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False)
                ])

        return updates

    def process_query(message, chat_history, session_mem, cart):
        """Process user message and return response with products"""
        try:
            response = run_agent_pipeline(
                query=message,
                session_memory=session_mem,
                cart_items=cart
            )

            text = response.get("text", "No response")
            products = response.get("products", [])

            # Gradio 6.0 format: list of dicts with role and content
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": text})

            # Update product display
            product_updates = update_product_display(products)
            section_update = gr.update(visible=len(products) > 0)

            return ["", chat_history, session_mem, products, section_update] + product_updates

        except Exception as e:
            error_msg = f"❌ **Error:** {str(e)}"
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": error_msg})

            # Hide products on error
            product_updates = update_product_display([])
            section_update = gr.update(visible=False)

            return ["", chat_history, session_mem, [], section_update] + product_updates

    def process_enriched_query(message, chat_history, session_mem, cart,
                               price_min, price_max, city, language, occasion):
        """Wrap user input with active filters before sending to agent."""
        enriched = build_enriched_query(message, price_min, price_max, city, language, occasion)
        return process_query(enriched, chat_history, session_mem, cart)

    def sidebar_search(query_text, chat_history, session_mem, cart,
                       price_min, price_max, city, language, occasion):
        """Triggered by sidebar category / combo buttons."""
        enriched = build_enriched_query(query_text, price_min, price_max, city, language, occasion)
        return process_query(enriched, chat_history, session_mem, cart)

    def occasion_search(occasion, chat_history, session_mem, cart,
                        price_min, price_max, city, language):
        """Triggered when an occasion is selected from the dropdown."""
        if not occasion or occasion == "Any Occasion":
            # No action if deselected
            product_updates = update_product_display([])
            return ["", chat_history, session_mem, [], gr.update(visible=False)] + product_updates
        query = f"Show me the best {occasion.lower()} gifts"
        enriched = build_enriched_query(query, price_min, price_max, city, language, occasion)
        return process_query(enriched, chat_history, session_mem, cart)

    def add_to_cart(product_idx, products, cart):
        """Add product to cart"""
        if product_idx < len(products):
            product = products[product_idx]
            cart.append(product)

            cart_html = format_cart_display(cart)
            checkout_enabled = len(cart) > 0

            return cart, cart_html, gr.update(interactive=checkout_enabled)

        return cart, format_cart_display(cart), gr.update(interactive=len(cart) > 0)

    def clear_all(session_mem):
        """Clear chat history and cart"""
        new_session = SessionBuffer(max_pairs=5)
        empty_cart_html = "<p style='color: #666;'>Your cart is empty</p>"

        # Hide all products
        product_updates = update_product_display([])
        section_update = gr.update(visible=False)

        return [
            [],  # Clear chat
            new_session,  # New session
            [],  # Clear cart
            [],  # Clear products
            empty_cart_html,  # Empty cart display
            gr.update(interactive=False),  # Disable checkout
            section_update  # Hide products section
        ] + product_updates

    def handle_voice(audio, chat_history, session_mem, cart,
                     price_min, price_max, city, language, occasion):
        """Handle voice input — also injects active sidebar filters."""
        if audio is None:
            product_updates = update_product_display([])
            return ["", chat_history, session_mem, [], gr.update(visible=False)] + product_updates

        transcribed = transcribe_audio(audio)

        if transcribed and not transcribed.startswith("⚠️"):
            enriched = build_enriched_query(f"🎤 {transcribed}", price_min, price_max,
                                            city, language, occasion)
            return process_query(enriched, chat_history, session_mem, cart)
        else:
            error = transcribed or "No speech detected"
            chat_history.append({"role": "user", "content": "🎤 Voice Input"})
            chat_history.append({"role": "assistant", "content": error})
            product_updates = update_product_display([])
            return ["", chat_history, session_mem, [], gr.update(visible=False)] + product_updates

    # ═══════════════════════════════════════════════════════════════════════════
    # EVENT WIRING
    # ═══════════════════════════════════════════════════════════════════════════

    submit_outputs = [msg, chatbot, session_memory_state, products_state, products_section] + \
                     product_imgs + product_names + product_ids + product_prices + product_btns

    # Filter inputs that get injected into every query
    filter_inputs = [price_min_slider, price_max_slider, city_radio, lang_radio, occasion_dropdown]

    # ── Text / Send ───────────────────────────────────────────────────────────
    msg.submit(
        process_enriched_query,
        [msg, chatbot, session_memory_state, cart_state] + filter_inputs,
        submit_outputs
    )

    submit.click(
        process_enriched_query,
        [msg, chatbot, session_memory_state, cart_state] + filter_inputs,
        submit_outputs
    )

    # ── Voice ─────────────────────────────────────────────────────────────────
    audio_input.change(
        handle_voice,
        [audio_input, chatbot, session_memory_state, cart_state] + filter_inputs,
        submit_outputs
    )

    # ── Category Buttons ──────────────────────────────────────────────────────
    category_queries = {
        cat_cakes:    "Show me the best cakes",
        cat_flowers:  "Show me beautiful flower arrangements",
        cat_choco:    "Show me premium chocolates",
        cat_toys:     "Show me soft toys and teddy bears",
        cat_hampers:  "Show me gift hampers",
        cat_icecream: "Show me ice cream options",
    }

    for btn, query_text in category_queries.items():
        btn.click(
            lambda q=query_text, *args: sidebar_search(q, *args),
            [chatbot, session_memory_state, cart_state] + filter_inputs,
            submit_outputs
        )

    # ── Combo Buttons ─────────────────────────────────────────────────────────
    combo_queries = {
        combo_cake_flower:  "I want a cake and flowers combo gift",
        combo_choco_teddy:  "Show me a chocolate and teddy bear combo",
        combo_hamper_card:  "Show me a gift hamper with a greeting card",
    }

    for btn, query_text in combo_queries.items():
        btn.click(
            lambda q=query_text, *args: sidebar_search(q, *args),
            [chatbot, session_memory_state, cart_state] + filter_inputs,
            submit_outputs
        )

    # ── Occasion Dropdown ─────────────────────────────────────────────────────
    occasion_dropdown.change(
        occasion_search,
        [occasion_dropdown, chatbot, session_memory_state, cart_state,
         price_min_slider, price_max_slider, city_radio, lang_radio],
        submit_outputs
    )

    # ── Add to Cart ───────────────────────────────────────────────────────────
    for idx, btn in enumerate(product_btns):
        btn.click(
            lambda p=products_state, c=cart_state, i=idx: add_to_cart(i, p, c),
            [products_state, cart_state],
            [cart_state, cart_display, checkout_btn]
        )

    # ── Clear ─────────────────────────────────────────────────────────────────
    clear_btn.click(
        clear_all,
        [session_memory_state],
        [chatbot, session_memory_state, cart_state, products_state,
         cart_display, checkout_btn, products_section] +
        product_imgs + product_names + product_ids + product_prices + product_btns
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
