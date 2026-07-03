import gradio as gr
import sys
from pathlib import Path
import os
import tempfile

sys.path.append(str(Path(__file__).resolve().parent))

from main import run_agent_pipeline
from memory.session_buffer import SessionBuffer

# Try to import speech recognition libraries
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Initialize session state
session_memory = SessionBuffer(max_pairs=5)
cart_items = []

def transcribe_audio(audio_path):
    """Transcribe audio using OpenAI Whisper API (supports multilingual)"""
    if not audio_path:
        return None

    if not OPENAI_AVAILABLE:
        return "⚠️ Voice input not available. Please install OpenAI library."

    try:
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY")
        if not api_key:
            return "⚠️ No API key found. Please add OPENAI_API_KEY or GROQ_API_KEY to secrets."

        # Initialize client (Groq also supports Whisper API)
        if os.getenv("GROQ_API_KEY"):
            client = OpenAI(
                api_key=os.getenv("GROQ_API_KEY"),
                base_url="https://api.groq.com/openai/v1"
            )
        else:
            client = OpenAI(api_key=api_key)

        # Open and transcribe audio file
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",  # Groq uses "whisper-large-v3"
                file=audio_file,
                language=None,  # Auto-detect: supports Sinhala, Tamil, English
                response_format="text"
            )

        return transcript if isinstance(transcript, str) else transcript.text

    except Exception as e:
        return f"⚠️ Transcription error: {str(e)}"

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
        error_msg += "3. For voice: Add `OPENAI_API_KEY` or use `GROQ_API_KEY`\n"
        error_msg += "4. Check the Container logs for detailed errors"
        return error_msg

def process_audio_input(audio, history):
    """Process voice input and convert to text"""
    if audio is None:
        return history, ""

    # Transcribe audio
    transcribed_text = transcribe_audio(audio)

    if not transcribed_text or transcribed_text.startswith("⚠️"):
        return history, transcribed_text or "No audio detected"

    return history, transcribed_text

# Custom CSS for better product display
custom_css = """
.gradio-container {
    max-width: 1400px !important;
}
.input-group {
    display: flex;
    gap: 10px;
    align-items: flex-end;
}
"""

# Create Gradio Chat Interface with Voice Support
with gr.Blocks(css=custom_css, title="Kapi Shopping Agent") as demo:
    gr.Markdown(
        """
        # 🛍️ Kapi - Smart Shopping Agent
        ### 🎤 Now with Voice Support! (සිංහල | தமிழ் | English)

        Your AI-powered shopping assistant for Kapruka! Ask me about:
        - 🎂 Cakes & Bakery
        - 🍫 Chocolates & Sweets
        - 💐 Flowers & Bouquets
        - 🎁 Gift Items
        - 🧸 Toys & More

        **💬 Type or 🎤 Speak** in: English, Tamil, Sinhala, Singlish, Tanglish
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                height=500,
                show_label=False,
                avatar_images=(None, "🛍️")
            )

            with gr.Row():
                with gr.Column(scale=8):
                    msg = gr.Textbox(
                        placeholder="Type your message or use voice... (e.g., 'Show me chocolates')",
                        show_label=False,
                        lines=2
                    )
                with gr.Column(scale=2):
                    audio_input = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="🎤 Voice Input",
                        show_label=False
                    )

            with gr.Row():
                send_btn = gr.Button("Send 📤", variant="primary", scale=1)
                clear_btn = gr.Button("Clear 🗑️", scale=1)

            gr.Examples(
                examples=[
                    "Show me chocolate cakes",
                    "I need a birthday gift for my mom",
                    "Find flowers for delivery in Colombo",
                    "What's available for under 5000 LKR?",
                    "මම චොකලට් කේක් එකක් අවශ්‍යයි",  # Sinhala: I need a chocolate cake
                    "எனக்கு பூக்கள் வேண்டும்"  # Tamil: I need flowers
                ],
                inputs=msg
            )

        with gr.Column(scale=1):
            gr.Markdown("### 🛒 Shopping Cart")
            cart_display = gr.Markdown("*Cart is empty*")

            gr.Markdown("---")
            gr.Markdown(
                """
                ### 🎤 Voice Support
                - **Sinhala** (සිංහල)
                - **Tamil** (தமிழ்)
                - **English**
                - **Singlish** (සිංගලිෂ්)
                - **Tanglish** (தமிழிஷ்)

                Click the microphone and speak naturally!
                """
            )

    gr.Markdown(
        """
        ---
        **Setup for Voice:** Add these API keys in Space Settings → Repository secrets:
        - `GROQ_API_KEY` (recommended - supports Whisper + chat)
        - `OPENAI_API_KEY` (alternative - for Whisper transcription)
        - `GEMINI_API_KEY` (alternative - for chat only)
        """
    )

    # Handle text message submission
    def respond(message, chat_history):
        if not message.strip():
            return chat_history, ""

        bot_message = process_message(message, chat_history)
        chat_history.append((message, bot_message))
        return chat_history, ""

    # Handle voice input
    def handle_voice(audio, chat_history, current_text):
        if audio is None:
            return chat_history, current_text

        # Transcribe audio
        transcribed = transcribe_audio(audio)

        if transcribed and not transcribed.startswith("⚠️"):
            # Auto-submit the transcribed text
            bot_message = process_message(transcribed, chat_history)
            chat_history.append((f"🎤 {transcribed}", bot_message))
            return chat_history, ""
        else:
            # Show error but don't add to chat
            return chat_history, transcribed or "No speech detected"

    # Event handlers
    msg.submit(respond, [msg, chatbot], [chatbot, msg])
    send_btn.click(respond, [msg, chatbot], [chatbot, msg])

    # Voice input triggers automatic transcription and submission
    audio_input.change(
        handle_voice,
        [audio_input, chatbot, msg],
        [chatbot, msg]
    )

    clear_btn.click(lambda: ([], ""), None, [chatbot, msg])

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
