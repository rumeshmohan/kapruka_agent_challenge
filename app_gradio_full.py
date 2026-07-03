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

def transcribe_audio(audio_path):
    """Transcribe audio using OpenAI Whisper API (supports multilingual)"""
    if not audio_path or not VOICE_AVAILABLE:
        return None

    try:
        # Get API key - prefer Groq for voice support
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "⚠️ Voice requires GROQ_API_KEY or OPENAI_API_KEY"

        # Initialize client (Groq also supports Whisper)
        if os.getenv("GROQ_API_KEY"):
            client = OpenAI(
                api_key=os.getenv("GROQ_API_KEY"),
                base_url="https://api.groq.com/openai/v1"
            )
            model = "whisper-large-v3"
        else:
            client = OpenAI(api_key=api_key)
            model = "whisper-1"

        # Transcribe audio
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="text"
            )

        return transcript if isinstance(transcript, str) else transcript.text

    except Exception as e:
        return f"⚠️ Transcription error: {str(e)}"

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
        error_msg += "3. For voice: Add `GROQ_API_KEY` or `OPENAI_API_KEY`\n"
        error_msg += "4. Check the Container logs for detailed errors"
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
        ### 🎤 Voice-Enabled! (සිංහල | தமிழ் | English)

        Your AI-powered shopping assistant for Kapruka! Ask me about:
        - 🎂 Cakes & Bakery
        - 🍫 Chocolates & Sweets
        - 💐 Flowers & Bouquets
        - 🎁 Gift Items
        - 🧸 Toys & More

        **💬 Type or 🎤 Speak** in: English, Tamil, Sinhala, Singlish, Tanglish
        """
    )

    chatbot = gr.Chatbot(
        height=500,
        show_label=False,
        avatar_images=(None, "🛍️")
    )

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Type your message or use the microphone... (e.g., 'Show me chocolates')",
            show_label=False,
            scale=7,
            lines=2
        )
        audio_input = gr.Audio(
            sources=["microphone"],
            type="filepath",
            label="🎤 Voice",
            show_label=False,
            scale=2
        )
        submit = gr.Button("Send", scale=1, variant="primary")

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

    gr.Markdown(
        """
        ---
        **🔑 Setup:** Add API keys in Space Settings → Repository secrets:
        - `GROQ_API_KEY` (recommended - supports both chat + voice)
        - `OPENAI_API_KEY` (alternative - for voice support)
        - `GEMINI_API_KEY` (alternative - for chat only)

        **🎤 Voice Support:** Speak naturally in Sinhala, Tamil, English, or mixed languages!
        """
    )

    # Handle message submission
    def respond(message, chat_history):
        if not message or not message.strip():
            return "", chat_history
        bot_message = process_message(message, chat_history)
        chat_history.append((message, bot_message))
        return "", chat_history

    # Handle voice input
    def handle_voice(audio, chat_history):
        if audio is None:
            return "", chat_history

        # Transcribe audio
        transcribed = transcribe_audio(audio)

        if transcribed and not transcribed.startswith("⚠️"):
            # Process the transcribed text
            bot_message = process_message(transcribed, chat_history)
            chat_history.append((f"🎤 {transcribed}", bot_message))
            return "", chat_history
        else:
            # Show error in chat
            error = transcribed or "No speech detected"
            chat_history.append(("🎤 Voice Input", error))
            return "", chat_history

    # Event handlers
    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    submit.click(respond, [msg, chatbot], [msg, chatbot])

    # Voice input triggers automatic transcription and submission
    audio_input.change(handle_voice, [audio_input, chatbot], [msg, chatbot])

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
