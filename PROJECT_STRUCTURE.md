# 📁 Project Structure

## Essential Files for Deployment

```
miniproject03_V2/
├── 📄 app_gradio_full.py      # Main Gradio app with voice support
├── 📄 main.py                 # Agent pipeline orchestrator
├── 📄 requirements.txt        # Python dependencies
├── 📄 README.md               # Project overview
├── 📄 VOICE_SETUP.md         # Voice feature setup guide
├── 📄 .env.example           # Environment variables template
├── 📄 .gitignore             # Git ignore rules
│
├── 📁 agents/                # Multi-agent system
│   ├── catalog_agent.py      # Product search & recommendations
│   ├── preference_agent.py   # User preferences & allergies
│   ├── checkout_agent.py     # Cart & checkout handling
│   ├── logistics_agent.py    # Shipping & delivery
│   ├── chitchat_agent.py     # Conversational responses
│   ├── router.py             # Intent routing
│   └── reflection_loop.py    # Response quality check
│
├── 📁 memory/                # Session management
│   └── session_buffer.py     # Conversation history buffer
│
├── 📁 utils/                 # Utility modules
│   ├── config.py             # Configuration loader
│   ├── llm_services.py       # LLM API clients
│   └── mcp_client.py         # MCP protocol client
│
├── 📁 config/                # Configuration files
│   └── settings.yaml         # App settings
│
└── 📁 data/                  # Data files
    └── user_profiles/        # User preference storage
```

## Key Components

### 🎯 Main Application
- **app_gradio_full.py**: Gradio interface with chat, voice input, and product display
- **main.py**: Agent pipeline that routes queries to appropriate agents

### 🤖 Agent System
- **Router**: Classifies user intent (catalog, preferences, checkout, logistics, chitchat)
- **Catalog Agent**: Searches products, parses structured data
- **Preference Agent**: Manages user preferences and dietary restrictions
- **Checkout Agent**: Handles cart operations and checkout flow
- **Logistics Agent**: Provides delivery information
- **Chitchat Agent**: Handles casual conversation
- **Reflection Loop**: Quality checks and filters responses

### 🎤 Voice Support
- Uses OpenAI Whisper API (via Groq or OpenAI)
- Supports: Sinhala, Tamil, English, Singlish, Tanglish
- Auto-transcription and processing

### 💾 Memory System
- Session buffer for conversation context
- User profile storage for preferences
- Short-term memory (5 conversation pairs)

### 🔧 Configuration
- Environment variables for API keys
- YAML configuration for app settings
- Multiple LLM provider support (Groq, Gemini, OpenAI)

## Removed Files (Cleanup)

The following files were removed as they're not needed for HF Spaces:

- ❌ `app.py` - Old app version
- ❌ `app_simple.py` - Simple test version
- ❌ `app_gradio.py` - Basic Gradio version
- ❌ `app_gradio_voice.py` - Alternative voice version
- ❌ `ui/app.py` - Streamlit version
- ❌ `uv.lock` - UV package lock
- ❌ `pyproject.toml` - Project config (using requirements.txt)
- ❌ `.dockerignore` - Docker config

## Deployment

### Hugging Face Spaces
The app is configured for Hugging Face Spaces deployment:
- SDK: Gradio
- Python: 3.11
- Entry point: `app_gradio_full.py`
- Dependencies: `requirements.txt`

### Required Secrets
Add in Space Settings → Repository secrets:
- `GROQ_API_KEY` or `OPENAI_API_KEY` (for voice + chat)
- `GEMINI_API_KEY` (alternative for chat)

## Dependencies

```txt
gradio>=4.0.0          # UI framework
openai>=1.0.0          # LLM API (Groq/OpenAI)
requests>=2.31.0       # HTTP client
python-dotenv>=1.0.0   # Environment variables
pyyaml>=6.0            # YAML parser
pillow>=10.0.0         # Image handling
pandas>=2.0.0          # Data handling
altair>=5.0.0          # Visualization
```

## File Sizes

- Total: ~50KB (excluding dependencies and data)
- Main app: ~8KB
- Agents: ~35KB combined
- Utils: ~7KB combined

## Git Repositories

- **GitHub**: https://github.com/rumeshmohan/kapruka_agent_challenge
- **HF Spaces**: https://huggingface.co/spaces/rumeshmohan/kapruka-agent-challenge

---

**Last Updated**: 2026-07-03
**Version**: 2.0 (Voice-enabled, cleaned up)
