# 🎤 Voice Support Setup Guide

## Overview
Your Kapi Shopping Agent now supports multilingual voice input using OpenAI's Whisper model through either Groq or OpenAI APIs.

## Supported Languages
- **Sinhala** (සිංහල)
- **Tamil** (தமிழ்)
- **English**
- **Singlish** (සිංගලිෂ්) - Sinhala-English mixed
- **Tanglish** (தமிழிஷ்) - Tamil-English mixed

## How It Works

### 1. Audio Input
Users can click the microphone icon and speak their query naturally in any supported language.

### 2. Transcription
The audio is transcribed using Whisper (via Groq or OpenAI):
- **Groq**: Uses `whisper-large-v3` - Fast and accurate
- **OpenAI**: Uses `whisper-1` - Original Whisper model

### 3. Processing
The transcribed text is automatically sent to the agent pipeline for processing, just like typed input.

## Setup Instructions

### For Hugging Face Spaces

1. Go to your Space settings:
   ```
   https://huggingface.co/spaces/rumeshmohan/kapruka-agent-challenge/settings
   ```

2. Navigate to **"Repository secrets"** section

3. Add API keys (choose one or both):

   **Option A - Groq (Recommended)**
   ```
   Name: GROQ_API_KEY
   Value: gsk_xxxxxxxxxxxxxxxxxxxxx
   ```
   - Get free API key from: https://console.groq.com/
   - Supports both chat + voice
   - Very fast processing

   **Option B - OpenAI**
   ```
   Name: OPENAI_API_KEY
   Value: sk-xxxxxxxxxxxxxxxxxxxxx
   ```
   - Get API key from: https://platform.openai.com/
   - Supports voice transcription
   - Requires paid account for Whisper API

4. Restart your Space (if needed)

### For Local Testing

1. Create a `.env` file in your project root:
   ```bash
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
   # OR
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
   ```

2. Install dependencies:
   ```bash
   pip install gradio openai python-dotenv
   ```

3. Run the app:
   ```bash
   python app_gradio_full.py
   ```

4. Open browser to: http://localhost:7860

## Usage Examples

### English
🎤 *"Show me chocolate cakes for delivery in Colombo"*

### Sinhala
🎤 *"මට චොකලට් කේක් එකක් අවශ්‍යයි"*
Translation: "I need a chocolate cake"

### Tamil
🎤 *"எனக்கு பூக்கள் வேண்டும்"*
Translation: "I need flowers"

### Singlish (Mixed)
🎤 *"මට flowers එකක් gift කරන්න ඕනෑ"*
Translation: "I want to gift some flowers"

### Tanglish (Mixed)
🎤 *"எனக்கு birthday cake ஒன்று வேண்டும்"*
Translation: "I need a birthday cake"

## Troubleshooting

### "Voice requires GROQ_API_KEY or OPENAI_API_KEY"
- You need to add at least one API key in Space settings
- Groq is recommended for best performance

### "Transcription error"
- Check that your API key is valid
- Ensure you have credits/quota remaining
- Try speaking more clearly or in a quieter environment

### "No speech detected"
- Check your microphone permissions in browser
- Speak louder or closer to the microphone
- Ensure audio is actually recording (look for waveform)

### Voice button not appearing
- Check that `openai` package is installed
- Verify API keys are set correctly
- Check browser console for errors

## Technical Details

### Audio Format
- Gradio captures audio from microphone
- Converts to file format compatible with Whisper API
- Supports various audio codecs automatically

### API Endpoints
- **Groq**: `https://api.groq.com/openai/v1/audio/transcriptions`
- **OpenAI**: `https://api.openai.com/v1/audio/transcriptions`

### Privacy
- Audio is sent to Groq/OpenAI for transcription
- Not stored permanently on their servers
- Processed in real-time and returned as text

## Cost Considerations

### Groq
- **Free tier**: Very generous limits
- **Speed**: 10-30x faster than OpenAI
- **Cost**: $0.05 per 1000 audio seconds (if exceeded free tier)

### OpenAI
- **Cost**: $0.006 per minute of audio
- **Speed**: Standard processing time
- **Accuracy**: Excellent for all languages

## Files Modified

1. **app_gradio_full.py** - Main app with integrated voice support
2. **app_gradio_voice.py** - Alternative version with enhanced voice UI
3. **README.md** - Updated documentation
4. **requirements.txt** - Already includes `openai` package

## Next Steps

1. ✅ Add your API key(s) to Space settings
2. ✅ Test voice input in different languages
3. ✅ Share with users
4. 🎯 Monitor usage and adjust as needed

## Support

- **Groq Documentation**: https://console.groq.com/docs/speech-text
- **OpenAI Whisper API**: https://platform.openai.com/docs/guides/speech-to-text
- **Gradio Audio**: https://www.gradio.app/docs/audio

---

**Built with ❤️ for multilingual voice shopping experience**
