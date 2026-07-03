import gradio as gr
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from main import run_agent_pipeline
from memory.session_buffer import SessionBuffer

# Global state (will be per-session in Gradio)
session_memory = SessionBuffer(max_pairs=5)
cart = []

def process_query(message, history):
    """Process user query and return response"""
    try:
        # Run agent pipeline
        response = run_agent_pipeline(
            query=message,
            session_memory=session_memory,
            cart_items=cart
        )

        # Format response
        text = response.get("text", "No response")
        products = response.get("products", [])

        # Add product cards if any
        if products:
            text += "\n\n**Products:**\n"
            for prod in products[:5]:  # Limit to 5
                name = prod.get("name", "Unknown")
                price = prod.get("price", 0)
                url = prod.get("url", "")
                text += f"\n- **{name}** - LKR {price:,.0f}"
                if url:
                    text += f" [View]({url})"

        return text

    except Exception as e:
        return f"❌ Error: {str(e)}\n\nPlease make sure API keys are set in Settings."

# Create Gradio interface
demo = gr.ChatInterface(
    fn=process_query,
    title="🛍️ Kapi - Smart Shopping Agent",
    description="Ask me anything about products on Kapruka! I can help you find gifts, cakes, flowers, and more.",
    examples=[
        "Show me chocolates",
        "I need a birthday gift for my mom",
        "Find flowers for delivery in Colombo"
    ],
    theme="soft",
    retry_btn=None,
    undo_btn=None,
    clear_btn="Clear Chat"
)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
