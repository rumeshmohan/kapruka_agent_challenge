import sys
import json
import io
import logging
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import streamlit.components.v1 as components
from main import run_agent_pipeline
from memory.session_buffer import SessionBuffer
from utils.config import get_config

# ==============================================================================
# --- 🛡️ SAFE PRICE HELPER (fixes uncaught float() crashes) ---
# ==============================================================================
def safe_price(p: dict) -> float:
    """
    Safely coerce a product's price field to a float.
    Handles strings like '1,500', 'LKR 1500', 'Rs. 1500', None, or empty values
    without raising ValueError/TypeError — which previously crashed the app
    on any search or cart interaction if the MCP server returned a
    non-numeric price.
    """
    try:
        raw = str(p.get("price", 0)).replace(",", "").replace("LKR", "").replace("Rs.", "").strip()
        return float(raw) if raw else 0.0
    except (ValueError, TypeError):
        return 0.0

# ==============================================================================
# --- 🛠️ REAL-TIME SYSTEM TRACE TERMINAL CAPTURE ENGINE ---
# ==============================================================================
if "log_stream" not in st.session_state:
    st.session_state.log_stream = io.StringIO()

# Configure the root logging layout to pipe data into our session stream
logging.basicConfig(level=logging.INFO, force=True)
root_logger = logging.getLogger()

# Prevent duplicate handlers from stacking on redraws
for h in root_logger.handlers[:]:
    root_logger.removeHandler(h)

# FIXED: Added style='{' to cleanly format time brackets without ValueError crashes
string_handler = logging.StreamHandler(st.session_state.log_stream)
string_handler.setFormatter(logging.Formatter("⏰ {asctime} | [{levelname}] ➔ {message}", style='{'))
root_logger.addHandler(string_handler)

# Inject an initial boot trace log line 
if not st.session_state.log_stream.getvalue():
    root_logger.info("⚡ Kapi Smart Agent Multi-Agent Kernel Initialized successfully.")

# ==============================================================================
# --- PAGE CONFIGURATION ---
# ==============================================================================
st.set_page_config(
    page_title="Kapi - Kapruka Smart Agent",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "memory" not in st.session_state:
    st.session_state.memory = SessionBuffer(max_pairs=5)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "cart" not in st.session_state:
    st.session_state.cart = []
if "order_history" not in st.session_state:
    st.session_state.order_history = []

# ==============================================================================
# --- SIDEBAR INTERFACE ---
# ==============================================================================
st.sidebar.title("👤 Family Profile Dashboard")
config = get_config()
PROFILES_FILE = Path(config.get("paths.profiles_file", "data/profiles.json"))

if PROFILES_FILE.exists():
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            profile_data = json.load(f)
        customer_info = profile_data.get("CUS_001", {})
        customer_name = customer_info.get("customer_name", "Kamal")
        recipients = customer_info.get("recipients", {})
        
        st.sidebar.caption(f"Account: **{customer_name}** | Connected Vault")
        
        for recipient, data in recipients.items():
            with st.sidebar.expander(f"💝 {recipient.capitalize()}'s Preferences", expanded=False):
                if data.get("allergies"):
                    st.markdown("**🚨 Allergies / Restrictions:**")
                    for allergy in data["allergies"]:
                        st.caption(f"• ⚠️ {allergy.upper()}")
                if data.get("preferences"):
                    st.markdown("**✨ Likes / Tags:**")
                    for pref in data["preferences"]:
                        st.caption(f"• ❤️ {pref}")
    except Exception as e:
        st.sidebar.error(f"Error loading profile data: {e}")
else:
    st.sidebar.info("No active profile data found.")

st.sidebar.markdown("---")

st.sidebar.title("🔍 Search & Filters")
st.sidebar.caption("Optional — just type in the chat box if you'd rather skip this.")

keyword_override = st.sidebar.text_input(
    label="Keyword",
    value="",
    placeholder="e.g. chocolate, lilies, fruits",
    help="What are you looking for?"
)
occasion = st.sidebar.selectbox(
    label="Occasion",
    options=["None", "Anniversary Gift", "Birthday Celebration", "Christmas Hamper", "Ramadan/Eid Sweets", "Mother's Day", "Valentine Surprise"],
    index=0,
    help="Get gift ideas suited to a specific occasion."
)
price_range = st.sidebar.slider(
    label="Budget (LKR)",
    min_value=0,
    max_value=50000,
    value=(0, 25000),
    step=500
)
sort_order = st.sidebar.selectbox(
    label="Sort By",
    options=["Best Match", "Price: Low to High", "Price: High to Low"],
    index=0
)
delivery_date = st.sidebar.date_input(
    label="Delivery Date",
    value=datetime.now() + timedelta(days=1),
    min_value=datetime.now() + timedelta(days=1),
    max_value=datetime.now() + timedelta(days=30)
)

sidebar_search_clicked = st.sidebar.button(
    "🔎 Search", type="primary", use_container_width=True
)

st.sidebar.markdown("---")

st.sidebar.title("🛒 Active Shopping Cart")
if not st.session_state.cart:
    st.sidebar.info("Your shopping cart is empty.")
else:
    for idx, item in enumerate(st.session_state.cart):
        item_id = item.get("id", idx)
        with st.sidebar.container(border=True):
            st.markdown(f"**{item.get('name', 'Product')}**")
            st.caption(f"Price: LKR {safe_price(item):,.2f}")
            if st.button("Remove", key=f"remove_cart_{item_id}"):
                st.session_state.cart = [
                    c for c in st.session_state.cart if c.get("id", idx) != item_id
                ]
                st.rerun()

    total_price = sum(safe_price(item) for item in st.session_state.cart)
    st.sidebar.metric(label="Total Summary Value", value=f"LKR {total_price:,.2f}")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🗑️ Clear Cart", key="clear_cart_btn"):
            st.session_state.cart = []
            st.rerun()
    with col2:
        if st.button("🚀 Buy Now", key="buy_now_btn"):
            st.session_state.order_history.extend(st.session_state.cart)
            st.session_state.cart = []
            st.sidebar.success("Order Placed!")
            st.rerun()

st.sidebar.markdown("---")

st.sidebar.title("📜 Order History Vault")
if not st.session_state.order_history:
    st.sidebar.caption("No historical invoices processed in this session.")
else:
    for idx, historical_item in enumerate(st.session_state.order_history):
        st.sidebar.caption(f"✓ Paid: **{historical_item.get('name')}** (LKR {safe_price(historical_item):,.2f})")
    if st.sidebar.button("❌ Clear Order Logs"):
        st.session_state.order_history = []
        st.rerun()

# ==============================================================================
# --- MAIN HEADER INTERFACE ---
# ==============================================================================
components.html(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@700&family=Noto+Sans+Tamil:wght@700&family=Noto+Sans+Sinhala:wght@700&display=swap" rel="stylesheet">
    <style>
        html, body {
            background: transparent;
            margin: 0;
            padding: 0;
        }
        .kapi-title-wrap {
            font-family: "Source Sans Pro", "Noto Sans", "Iskoola Pota", "Sinhala Sangam MN", "Noto Sans Sinhala", "Latha", "Tamil Sangam MN", "Noto Sans Tamil", sans-serif;
            display: flex;
            align-items: center;
            gap: 4px;
            height: 3.2rem;
            padding-top: 4px;
            margin-bottom: 2px;
        }
        .kapi-title-wrap .fixed-part {
            font-size: 2.1rem;
            font-weight: 700;
            color: #4A90E2;
            line-height: 3.2rem;
        }
        .kapi-rotator {
            position: relative;
            display: inline-block;
            height: 3.2rem;
            overflow: hidden;
            vertical-align: middle;
            min-width: 160px;
        }
        .kapi-rotator .tick-word {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: 3.2rem;
            line-height: 3.2rem;
            display: flex;
            align-items: center;
            font-family: "Source Sans Pro", "Noto Sans", "Iskoola Pota", "Sinhala Sangam MN", "Noto Sans Sinhala", "Latha", "Tamil Sangam MN", "Noto Sans Tamil", sans-serif;
            font-size: 2.1rem;
            font-weight: 700;
            color: #FFC72C;
            white-space: nowrap;
            transform: translateY(120%);
            opacity: 0;
        }
        .kapi-rotator .tick-word.tick-active {
            animation: kapi-tick-in 2s infinite;
        }
        @keyframes kapi-tick-in {
            0%   { transform: translateY(120%); opacity: 0; }
            12%  { transform: translateY(0%); opacity: 1; }
            70%  { transform: translateY(0%); opacity: 1; }
            85%  { transform: translateY(-120%); opacity: 0; }
            100% { transform: translateY(-120%); opacity: 0; }
        }
    </style>
    <div class="kapi-title-wrap">
        <span class="fixed-part">🛍️ Kapi -</span>
        <span class="kapi-rotator" id="kapi-rotator"></span>
        <span class="fixed-part">Smart Agent</span>
    </div>
    <script>
        (function() {
            const words = [
                { text: "Kapruka", lang: "en" },
                { text: "கப்ருகா", lang: "ta" },
                { text: "කප්රුක", lang: "si" }
            ];
            const container = document.getElementById("kapi-rotator");
            let current = 0;

            function showWord(idx) {
                container.innerHTML = "";
                const span = document.createElement("span");
                span.className = "tick-word tick-active";
                span.lang = words[idx].lang;
                span.textContent = words[idx].text;
                container.appendChild(span);
            }

            showWord(current);
            setInterval(() => {
                current = (current + 1) % words.length;
                showWord(current);
            }, 2000);
        })();
    </script>
    """,
    height=75,
)
st.caption("⚡ Live MCP Smart Assistant | English • Tamil • Sinhala • Singlish • Tanglish")

if not st.session_state.chat_history:
    st.info(
        "👋 **Just type or tap the mic below to ask for anything** — e.g. "
        "*\"chocolate hamper under 5000\"*.\n\n"
        "Want more control? The **sidebar on the left** lets you filter by "
        "budget, occasion, and delivery date, or search by keyword — "
        "optional, use it only if you need it."
    )

def render_product_card(prod, idx, key_prefix):
    st.image(
        prod.get("image_url", "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500&q=80"),
        width=None
    )
    st.markdown(f"**{prod.get('name')}**")
    st.caption(f"LKR {safe_price(prod):,.2f}")

    product_url = prod.get("product_url") or prod.get("url")
    if product_url:
        st.link_button("View Product ↗", product_url, use_container_width=True)

    already_in_cart = any(c.get("id") == prod.get("id") for c in st.session_state.cart)
    if already_in_cart:
        st.button("Added ✓", key=f"{key_prefix}_added_{prod.get('id')}_{idx}", disabled=True, use_container_width=True)
    else:
        if st.button("🛒 Add to Cart", key=f"{key_prefix}_add_{prod.get('id')}_{idx}", use_container_width=True):
            st.session_state.cart.append(prod)
            st.success("Added!")
            st.rerun()

# Render chat messages from history
for chat_idx, chat in enumerate(st.session_state.chat_history):
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])
        if "products" in chat and chat["products"]:
            cols = st.columns(min(len(chat["products"]), 4))
            for idx, prod in enumerate(chat["products"]):
                col_idx = idx % 4
                with cols[col_idx]:
                    render_product_card(prod, idx, key_prefix=f"hist_{chat_idx}")

# Chat execution bar
user_query = st.chat_input("Ask Kapi...")

# --- TRILINGUAL AND DIALECT MIX AUDIO ENGINE ---
voice_html = """
<script>
(function() {
    const doc = window.parent.document;
    const MIC_SVG = `
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Z"
                  stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M19 11a7 7 0 0 1-14 0M12 18v3"
                  stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    `;
    function mount() {
        const submitBtn = doc.querySelector('button[data-testid="stChatInputSubmitButton"]');
        if (!submitBtn || !submitBtn.parentElement) return false;
        const existing = doc.getElementById('bar-mic-btn');
        if (existing && existing.nextElementSibling === submitBtn) return true;
        if (existing) existing.remove();

        const oldStyle = doc.getElementById('bar-mic-style');
        if (oldStyle) oldStyle.remove();

        const style = doc.createElement('style');
        style.id = 'bar-mic-style';
        style.innerHTML = `
            #bar-mic-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 36px;
                height: 36px;
                margin: 0 6px;
                border-radius: 50%;
                border: none;
                background: rgba(136, 136, 136, 0.12);
                color: #6b6b6b;
                cursor: pointer;
                flex-shrink: 0;
                transition: background 0.15s ease, color 0.15s ease, transform 0.1s ease;
            }
            #bar-mic-btn svg { width: 18px; height: 18px; }
            #bar-mic-btn:hover { background: rgba(136, 136, 136, 0.22); }
            #bar-mic-btn:active { transform: scale(0.92); }
            #bar-mic-btn.recording {
                background: rgba(255, 75, 75, 0.14);
                color: #ff4b4b;
                animation: bar-mic-pulse 1.1s ease-in-out infinite;
            }
            @keyframes bar-mic-pulse {
                0%, 100% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.35); }
                50% { box-shadow: 0 0 0 6px rgba(255, 75, 75, 0); }
            }
            #voice-indicator-label {
                font-size: 11px;
                color: #888;
                margin-right: 4px;
                font-weight: 600;
                letter-spacing: 0.2px;
            }
        `;
        doc.head.appendChild(style);
        const micBtn = doc.createElement('button');
        micBtn.id = 'bar-mic-btn';
        micBtn.type = 'button';
        micBtn.title = 'Tap to speak. Use language tag to switch between variations';
        micBtn.innerHTML = MIC_SVG;
        
        const LANG_MODES = [
            { key: 'en',       label: 'English',  tag: 'en-US' },
            { key: 'si',       label: 'Sinhala',  tag: 'si-LK' },
            { key: 'ta',       label: 'Tamil',    tag: 'ta-LK' },
            { key: 'singlish', label: 'Singlish', tag: 'en-US' },
            { key: 'tanglish', label: 'Tanglish', tag: 'en-US' },
        ];
        let modeIdx = 0;

        const langTag = doc.createElement('button');
        langTag.id = 'bar-lang-tag';
        langTag.type = 'button';
        langTag.title = 'Click to change recognition language';
        langTag.innerText = LANG_MODES[modeIdx].label;
        langTag.style.cssText = `
            font-size: 11px; color: #888; margin-right: 4px; font-weight: 600;
            letter-spacing: 0.2px; border: none; background: rgba(136,136,136,0.12);
            border-radius: 10px; padding: 3px 9px; cursor: pointer;
        `;
        langTag.addEventListener('click', () => {
            modeIdx = (modeIdx + 1) % LANG_MODES.length;
            langTag.innerText = LANG_MODES[modeIdx].label;
        });
        const indicatorLabel = doc.createElement('span');
        indicatorLabel.id = 'voice-indicator-label';
        indicatorLabel.innerText = '🎙️';

        submitBtn.parentElement.insertBefore(langTag, submitBtn);
        submitBtn.parentElement.insertBefore(indicatorLabel, submitBtn);
        submitBtn.parentElement.insertBefore(micBtn, submitBtn);
        wireUp(micBtn, indicatorLabel, langTag, LANG_MODES, () => modeIdx);
        return true;
    }

    function wireUp(micBtn, indicatorLabel, langTag, LANG_MODES, getModeIdx) {
        const SpeechRecognition = window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            micBtn.style.display = 'none';
            indicatorLabel.style.display = 'none';
            langTag.style.display = 'none';
            return;
        }

        let isRecording = false;
        micBtn.addEventListener('click', () => {
            if (isRecording) return;
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;

            const mode = LANG_MODES[getModeIdx()];
            recognition.lang = mode.tag;

            recognition.onstart = () => {
                isRecording = true;
                micBtn.classList.add('recording');
                indicatorLabel.innerText = `Listening (${mode.label})...`;
                indicatorLabel.style.color = '#ff4b4b';
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                const textarea = doc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (textarea) {
                    const setter = Object.getOwnPropertyDescriptor(window.parent.HTMLTextAreaElement.prototype, 'value').set;
                    setter.call(textarea, transcript);
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.focus();
                }
            };
            recognition.onerror = () => {
                isRecording = false;
                micBtn.classList.remove('recording');
                indicatorLabel.innerText = '🎙️';
                indicatorLabel.style.color = '#888';
            };
            recognition.onend = () => {
                isRecording = false;
                micBtn.classList.remove('recording');
                indicatorLabel.innerText = '🎙️';
                indicatorLabel.style.color = '#888';
            };
            recognition.start();
        });
    }

    if (!mount()) {
        const interval = setInterval(() => { if (mount()) clearInterval(interval); }, 250);
        setTimeout(() => clearInterval(interval), 10000);
    }
    const observer = new MutationObserver(() => mount());
    observer.observe(doc.body, { childList: true, subtree: true });
})();
</script>
"""
#components.html(voice_html, height=0)

active_query = user_query
if not active_query and sidebar_search_clicked and (keyword_override or occasion != "None"):
    built_str = ""
    if keyword_override: built_str += f"{keyword_override} "
    if occasion != "None": built_str += f"suitable for {occasion}"
    active_query = f"Show me {built_str.strip()}"

if active_query:
    if active_query == user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)
    else:
        st.session_state.chat_history.append({"role": "user", "content": f"[Filter Search]: {active_query}"})
        with st.chat_message("user"):
            st.markdown(f"🔍 *Executing Sidebar Override Query:* **{active_query}**")

    # Trace active session context packaging
    root_logger.info(f"🚀 Main UI Thread packaging state payload context for user action.")

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            pipeline_kwargs = dict(
                query=active_query,
                session_memory=st.session_state.memory,
                cart_items=st.session_state.cart,
            )
            try:
                response = run_agent_pipeline(**pipeline_kwargs)
            except Exception as e:
                root_logger.error(f"❌ Core Pipeline Exception caught: {e}")
                response = {"text": "An execution error occurred.", "products": []}

            raw_products = response.get("products", [])

            # FIXED: use safe_price() instead of float() to avoid crashing
            # when the MCP server returns a non-numeric price (e.g. "1,500", "Rs. 1500", None)
            filtered_products = [
                p for p in raw_products
                if price_range[0] <= safe_price(p) <= price_range[1]
            ]

            if sort_order == "Price: Low to High":
                filtered_products.sort(key=safe_price)
            elif sort_order == "Price: High to Low":
                filtered_products.sort(key=safe_price, reverse=True)

            st.markdown(response["text"])

            if raw_products and not filtered_products:
                st.info(
                    f"Found {len(raw_products)} matching product(s), but none fall within "
                    f"your LKR {price_range[0]:,}–{price_range[1]:,} budget filter."
                )

            chat_entry = {"role": "assistant", "content": response["text"], "products": []}
            if filtered_products:
                chat_entry["products"] = filtered_products
                cols = st.columns(min(len(filtered_products), 4))
                for idx, prod in enumerate(filtered_products):
                    col_idx = idx % 4
                    with cols[col_idx]:
                        render_product_card(prod, idx, key_prefix=f"live_{len(st.session_state.chat_history)}")
            
            st.session_state.chat_history.append(chat_entry)
            st.rerun()

# ==============================================================================
# --- 🛠️ DYNAMIC STREAMING AGENT TRACE LOGGER PANEL ---
# ==============================================================================
st.markdown("---")
with st.expander("🛠️ System Multi-Agent Terminal Trace Logs", expanded=True):
    current_logs = st.session_state.log_stream.getvalue()
    if current_logs:
        st.code(current_logs, language="bash")
    else:
        st.info("Waiting for agent activity triggers...")