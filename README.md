---
title: Kapi Smart Shopping Agent
emoji: 🛍️
colorFrom: blue
colorTo: purple
sdk: gradio
app_file: app_gradio_full.py
pinned: false
python_version: "3.11"
---

# 🛍️ Kapi - Kapruka Smart Agent

An intelligent shopping assistant powered by multi-agent AI system.

## Features
- 🤖 Multi-agent system (Catalog, Preferences, Checkout, Logistics)
- 🎤 Voice input support (සිංහල | தமிழ் | English)
- 💬 Natural language chat in English, Tamil, Sinhala, Singlish, Tanglish
- 🛒 Smart cart management
- 📦 Order tracking

## Configuration

Add these secrets in your Hugging Face Space settings:

### Required (at least one):
- `GROQ_API_KEY` - Recommended! Supports both chat + voice transcription
- `GEMINI_API_KEY` - For Google Gemini (chat only)

### Optional:
- `OPENAI_API_KEY` - Alternative for voice transcription

## Voice Support
The app now supports multilingual voice input using Whisper:
- 🎤 Click the microphone icon
- 🗣️ Speak in Sinhala, Tamil, English, or mixed languages
- ✨ Auto-transcribes and processes your request
