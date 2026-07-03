import gradio as gr
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from main import run_agent_pipeline
from memory.session_buffer import SessionBuffer

# Initialize session state
session_memory = SessionBuffer(max_pairs=5)
cart_items = []
chat_history_storage = []

def format_products_html(products):
    """Format products as HTML cards"""
    if not products:
        return ""

    html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-top: 20px;">'

    for prod in products[:8]:  # Limit to 8 products
        name = prod.get("name", "Unknown Product")
        price = prod.get("price", 0)
        image_url = prod.get("image_url", "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=300&q=80")
        product_url = prod.get("url", prod.get("product_url", "#"))
        prod_id = prod.get("id", name)

        html += f'''
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: white;">
            <img src="{image_url}" style="width: 100%; height: 150px; object-fit: cover; border-radius: 4px;" />
            <h4 style="margin: 10px 0 5px 0; font-size: 14px;">{name}</h4>
            <p style="color: #0066cc; font-weight: bold; margin: 5px 0;">LKR {price:,.0f}</p>
            <a href="{product_url}" target="_blank" style="display: inline-block; margin-top: 5px; padding: 5px 10px; background: #0066cc; color: white; text-decoration: none; border-radius: 4px; font-size: 12px;">View Product</a>
        </div>
        '''

    html += '</div>'
    return html

def process_message(message, history):
    """Process user message and return response"""
    try:
        # Run agent pipeline
        response = run_agent_pipeline(
            query=message,
            session_memory=session_memory,
            cart_items=cart_items
        )

        # Get response text
        text = response.get("text", "No response")
        products = response.get("products", [])

        # Format response with products
        if products:
            products_html = format_products_html(products)
            full_response = f"{text}\n\n{products_html}"
        else:
            full_response = text

        return full_response

    except Exception as e:
        error_msg = f"❌ **Error:** {str(e)}\n\n"
        error_msg += "**Troubleshooting:**\n"
        error_msg += "1. Make sure API keys are set in Settings → Repository secrets\n"
        error_msg += "2. Required: `GROQ_API_KEY` or `GEMINI_API_KEY`\n"
        error_msg += "3. Check the Container logs for detailed errors"
        return error_msg

# Custom CSS for better product display
custom_css = """
.gradio-container {
    max-width: 1200px !important;
}
"""

# Create Gradio Chat Interface
with gr.Blocks(css=custom_css, title="Kapi Shopping Agent") as demo:
    gr.Markdown(
        """
        # 🛍️ Kapi - Smart Shopping Agent

        Your AI-powered shopping assistant for Kapruka! Ask me about:
        - 🎂 Cakes & Bakery
        - 🍫 Chocolates & Sweets
        - 💐 Flowers & Bouquets
        - 🎁 Gift Items
        - 🧸 Toys & More

        **Languages supported:** English, Tamil, Sinhala, Singlish, Tanglish
        """
    )

    chatbot = gr.Chatbot(
        height=500,
        show_label=False,
        avatar_images=(None, "🛍️")
    )

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Ask me anything... (e.g., 'Show me chocolates')",
            show_label=False,
            scale=9
        )
        submit = gr.Button("Send", scale=1, variant="primary")

    gr.Examples(
        examples=[
            "Show me chocolate cakes",
            "I need a birthday gift for my mom",
            "Find flowers for delivery in Colombo",
            "What's available for under 5000 LKR?",
            "I'm allergic to nuts, show me safe options"
        ],
        inputs=msg
    )

    gr.Markdown(
        """
        ---
        **Note:** Add your API keys in Space Settings → Repository secrets:
        - `GROQ_API_KEY` (recommended)
        - `GEMINI_API_KEY` (alternative)
        """
    )

    # Handle message submission
    def respond(message, chat_history):
        bot_message = process_message(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    submit.click(respond, [msg, chatbot], [msg, chatbot])

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
