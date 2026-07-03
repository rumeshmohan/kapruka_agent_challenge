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

# Custom CSS for better layout
custom_css = """
.gradio-container {
    max-width: 1400px !important;
}
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
"""

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

def format_cart_display(cart):
    """Format cart items for display in sidebar"""
    if not cart:
        return "🛒 *Your cart is empty*"

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

# Create Gradio Interface
with gr.Blocks(css=custom_css, title="Kapi Shopping Agent") as demo:
    # Hidden state to track cart and products
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
        # Main content area (2/3 width)
        with gr.Column(scale=2):
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
                        img_1 = gr.Image(label="", show_label=False, height=200, visible=False)
                        name_1 = gr.Markdown("", visible=False)
                        id_1 = gr.Markdown("", visible=False)
                        price_1 = gr.Markdown("", visible=False)
                        btn_1 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

                    prod_col_2 = gr.Column(scale=1)
                    with prod_col_2:
                        img_2 = gr.Image(label="", show_label=False, height=200, visible=False)
                        name_2 = gr.Markdown("", visible=False)
                        id_2 = gr.Markdown("", visible=False)
                        price_2 = gr.Markdown("", visible=False)
                        btn_2 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

                    prod_col_3 = gr.Column(scale=1)
                    with prod_col_3:
                        img_3 = gr.Image(label="", show_label=False, height=200, visible=False)
                        name_3 = gr.Markdown("", visible=False)
                        id_3 = gr.Markdown("", visible=False)
                        price_3 = gr.Markdown("", visible=False)
                        btn_3 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

                # Row 2
                with gr.Row():
                    prod_col_4 = gr.Column(scale=1)
                    with prod_col_4:
                        img_4 = gr.Image(label="", show_label=False, height=200, visible=False)
                        name_4 = gr.Markdown("", visible=False)
                        id_4 = gr.Markdown("", visible=False)
                        price_4 = gr.Markdown("", visible=False)
                        btn_4 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

                    prod_col_5 = gr.Column(scale=1)
                    with prod_col_5:
                        img_5 = gr.Image(label="", show_label=False, height=200, visible=False)
                        name_5 = gr.Markdown("", visible=False)
                        id_5 = gr.Markdown("", visible=False)
                        price_5 = gr.Markdown("", visible=False)
                        btn_5 = gr.Button("Add to Cart 🛒", variant="primary", visible=False)

                    prod_col_6 = gr.Column(scale=1)
                    with prod_col_6:
                        img_6 = gr.Image(label="", show_label=False, height=200, visible=False)
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

        # Sidebar (1/3 width)
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

    # Group all product components for easier updates
    product_imgs = [img_1, img_2, img_3, img_4, img_5, img_6]
    product_names = [name_1, name_2, name_3, name_4, name_5, name_6]
    product_ids = [id_1, id_2, id_3, id_4, id_5, id_6]
    product_prices = [price_1, price_2, price_3, price_4, price_5, price_6]
    product_btns = [btn_1, btn_2, btn_3, btn_4, btn_5, btn_6]

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

                # Image, Name, ID, Price, Button
                updates.extend([
                    gr.update(value=image_url, visible=True),
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

            chat_history.append((message, text))

            # Update product display
            product_updates = update_product_display(products)
            section_update = gr.update(visible=len(products) > 0)

            return ["", chat_history, session_mem, products, section_update] + product_updates

        except Exception as e:
            error_msg = f"❌ **Error:** {str(e)}"
            chat_history.append((message, error_msg))

            # Hide products on error
            product_updates = update_product_display([])
            section_update = gr.update(visible=False)

            return ["", chat_history, session_mem, [], section_update] + product_updates

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

    def handle_voice(audio, chat_history, session_mem, cart):
        """Handle voice input"""
        if audio is None:
            product_updates = update_product_display([])
            return ["", chat_history, session_mem, [], gr.update(visible=False)] + product_updates

        transcribed = transcribe_audio(audio)

        if transcribed and not transcribed.startswith("⚠️"):
            return process_query(f"🎤 {transcribed}", chat_history, session_mem, cart)
        else:
            error = transcribed or "No speech detected"
            chat_history.append(("🎤 Voice Input", error))
            product_updates = update_product_display([])
            return ["", chat_history, session_mem, [], gr.update(visible=False)] + product_updates

    # Event handlers
    submit_outputs = [msg, chatbot, session_memory_state, products_state, products_section] + \
                     product_imgs + product_names + product_ids + product_prices + product_btns

    msg.submit(
        process_query,
        [msg, chatbot, session_memory_state, cart_state],
        submit_outputs
    )

    submit.click(
        process_query,
        [msg, chatbot, session_memory_state, cart_state],
        submit_outputs
    )

    audio_input.change(
        handle_voice,
        [audio_input, chatbot, session_memory_state, cart_state],
        submit_outputs
    )

    # Add to cart handlers
    for idx, btn in enumerate(product_btns):
        btn.click(
            lambda p=products_state, c=cart_state, i=idx: add_to_cart(i, p, c),
            [products_state, cart_state],
            [cart_state, cart_display, checkout_btn]
        )

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
