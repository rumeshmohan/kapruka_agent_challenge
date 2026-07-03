import streamlit as st
import os

# Force correct port for HF
os.environ['STREAMLIT_SERVER_PORT'] = '7860'
os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

st.set_page_config(
    page_title="Kapi Test",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Kapi - Test")
st.write("If you see this, the app is working!")
st.write(f"Port: {os.environ.get('PORT', 'not set')}")
st.write(f"Streamlit port: {os.environ.get('STREAMLIT_SERVER_PORT', 'not set')}")

if st.button("Click me"):
    st.success("Button clicked successfully!")
