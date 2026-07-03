import streamlit as st

st.set_page_config(
    page_title="Kapi Test",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Kapi - Test")
st.write("If you see this, the app is working!")

if st.button("Click me"):
    st.success("Button clicked successfully!")
