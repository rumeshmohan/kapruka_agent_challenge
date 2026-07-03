import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from main import run_agent_pipeline
from memory.session_buffer import SessionBuffer
from utils.config import get_config

# ==============================================================================
# --- PAGE CONFIGURATION (MUST BE FIRST) ---
# ==============================================================================
st.set_page_config(
    page_title="Kapi - Kapruka Smart Agent",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger = logging.getLogger(__name__)

# ==============================================================================
# --- 🛡️ SAFE PRICE HELPER ---
# ==============================================================================
def safe_price(p: dict) -> float:
    try:
        raw = str(p.get("price", 0)).replace(",", "").replace("LKR", "").replace("Rs.", "").strip()
        return float(raw) if raw else 0.0
    except (ValueError, TypeError):
        return 0.0

# ==============================================================================
# --- SESSION STATE INITS ---
# ==============================================================================
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

keyword_override = st.sidebar.text_input(label="Keyword", value="", placeholder="e.g. chocolate, lilies, fruits")
occasion = st.sidebar.selectbox(
    label="Occasion",
    options=["None", "Anniversary Gift", "Birthday Celebration", "Christmas Hamper", "Ramadan/Eid Sweets", "Mother's Day", "Valentine Surprise"],
    index=0
)
price_range = st.sidebar.slider(label="Budget (LKR)", min_value=0, max_value=50000, value=(0, 25000), step=500)
sort_order = st.sidebar.selectbox(label="Sort By", options=["Best Match", "Price: Low to High", "Price: High to Low"], index=0)
delivery_date = st.sidebar.date_input(
    label="Delivery Date",
    value=datetime.now() + timedelta(days=1),
    min_value=datetime.now() + timedelta(days=1),
    max_value=datetime.now() + timedelta(days=30)
)

sidebar_search_clicked = st.sidebar.button("🔎 Search", type="primary", use_container_width=True)

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
                st.session_state.cart = [c for c in st.session_state.cart if c.get("id", idx) != item_id]
                st.rerun(scope="app")

    total_price = sum(safe_price(item) for item in st.session_state.cart)
    st.sidebar.metric(label="Total Summary Value", value=f"LKR {total_price:,.2f}")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🗑️ Clear Cart", key="clear_cart_btn"):
            st.session_state.cart = []
            st.rerun(scope="app")
    with col2:
        if st.button("🚀 Buy Now", key="buy_now_btn"):
            st.session_state.order_history.extend(st.session_state.cart)
            st.session_state.cart = []
            st.sidebar.success("Order Placed!")
            st.rerun(scope="app")

st.sidebar.markdown("---")
st.sidebar.title("📜 Order History Vault")
if not st.session_state.order_history:
    st.sidebar.caption("No historical invoices processed in this session.")
else:
    for idx, historical_item in enumerate(st.session_state.order_history):
        st.sidebar.caption(f"✓ Paid: **{historical_item.get('name')}** (LKR {safe_price(historical_item):,.2f})")
    if st.sidebar.button("❌ Clear Order Logs"):
        st.session_state.order_history = []
        st.rerun(scope="app")

# ==============================================================================
# --- MAIN HEADER INTERFACE ---
# ==============================================================================
# Replaced volatile HTML/JS injections with native Streamlit components
st.title("🛍️ Kapi - Smart Agent")
st.caption("⚡ Live MCP Smart Assistant | English • Tamil • Sinhala • Singlish • Tanglish")

if not st.session_state.chat_history:
    st.info(
        "👋 **Just type below to ask for anything**\n\n"
        "Want more control? The **sidebar on the left** lets you filter by budget, occasion, and delivery date, or search by keyword."
    )

def render_product_card(prod, idx, key_prefix):
    st.image(prod.get("image_url", "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500&q=80"), width=None)
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
            st.rerun(scope="app")

# Render chat messages from history
for chat_idx, chat in enumerate(st.session_state.chat_history):
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])
        if "products" in chat and chat["products"]:
            cols = st.columns(min(len(chat["products"]), 4))
            for idx, prod in enumerate(chat["products"]):
                with cols[idx % 4]:
                    render_product_card(prod, idx, key_prefix=f"hist_{chat_idx}")

# Chat execution bar
user_query = st.chat_input("Ask Kapi...")

active_query = user_query
if not active_query and sidebar_search_clicked and (keyword_override or occasion != "None"):
    built_str = ""
    if keyword_override: built_str += f"{keyword_override} "
    if occasion != "None": built_str += f"suitable for {occasion}"
    active_query = f"Show me {built_str.strip()}"

if active_query:
    try:
        if active_query == user_query:
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)
        else:
            st.session_state.chat_history.append({"role": "user", "content": f"[Filter Search]: {active_query}"})
            with st.chat_message("user"):
                st.markdown(f"🔍 *Executing Sidebar Override Query:* **{active_query}**")

        logger.info("🚀 Main UI Thread packaging state payload context for user action.")

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
                    logger.error(f"❌ Core Pipeline Exception caught: {e}", exc_info=True)
                    response = {"text": f"An execution error occurred: {str(e)}", "products": []}

                raw_products = response.get("products", [])
                filtered_products = [p for p in raw_products if price_range[0] <= safe_price(p) <= price_range[1]]

                if sort_order == "Price: Low to High":
                    filtered_products.sort(key=safe_price)
                elif sort_order == "Price: High to Low":
                    filtered_products.sort(key=safe_price, reverse=True)

                st.markdown(response["text"])

                if raw_products and not filtered_products:
                    st.info(f"Found {len(raw_products)} matching product(s), but none fall within your LKR {price_range[0]:,}–{price_range[1]:,} budget filter.")

                chat_entry = {"role": "assistant", "content": response["text"], "products": []}
                if filtered_products:
                    chat_entry["products"] = filtered_products
                    cols = st.columns(min(len(filtered_products), 4))
                    for idx, prod in enumerate(filtered_products):
                        with cols[idx % 4]:
                            render_product_card(prod, idx, key_prefix=f"live_{len(st.session_state.chat_history)}")

                st.session_state.chat_history.append(chat_entry)
    except Exception as e:
        logger.error(f"❌ Critical error in query processing: {e}", exc_info=True)
        st.error(f"An unexpected error occurred: {str(e)}. Please try again.")