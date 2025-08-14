# Robust AI Voice Agent

Conversational AI voice assistant with session memory, robust error handling, graceful fallbacks, and a modern web UI. Speak to the agent, get real-time transcription, AI responses, and natural-sounding TTS – even when upstream APIs are down.

## ✨ Features
- Voice conversation with session-based memory
- Robust error handling across STT, LLM, and TTS
- Graceful fallbacks with helpful responses and gTTS audio
- Diagnostics, health checks, and error statistics
- Modern UI with pipeline status and retry flows
- Auto-mode for continuous back-and-forth conversation

## 🧱 Architecture
- Frontend: `templates/index.html` (vanilla JS, modern UI)
- Backend: `FastAPI` (`main.py`)
  - STT: AssemblyAI
  - LLM: Google Gemini
  - TTS: Murf AI → gTTS fallback → text-only fallback
- Audio handling: `pydub`, browser `MediaRecorder`
- Config: `.env` via `python-dotenv`

```
Browser (MediaRecorder) → /agent/chat/{session_id}
  ├─ Speech-to-Text (AssemblyAI)
  ├─ Prompt building with session history
  ├─ LLM response (Gemini)
  ├─ Text-to-Speech (Murf → gTTS → text)
  └─ JSON response with transcription, text, and audio URL
```

## ⚙️ Technologies
- FastAPI, Uvicorn, httpx
- AssemblyAI SDK, Google Generative AI SDK
- gTTS (fallback), pydub
- Vanilla JS/HTML/CSS UI

## 📦 Project Structure
```
.
├─ main.py                   # FastAPI server with robust pipeline
├─ templates/
│  └─ index.html             # Frontend UI
├─ static/
│  └─ index.html             # (legacy / optional)
├─ uploads/                  # Example recordings
├─ venv/                     # Virtual environment (local)
├─ requirements.txt
├─ README.md                 # This file
├─ ROBUST_ERROR_HANDLING.md  # Deep-dive guide
├─ ERROR_HANDLING_SUMMARY.md # Summary of features
├─ test_errors.py            # Test suite for error paths
├─ simulate_failures.py      # API failure simulation
└─ demo_robust_features.py   # Demo runner
```

## 🔐 Environment Variables (.env)
Create a `.env` file in the project root:
```
# Required (use "your_api_key_here" or leave empty to test fallbacks)
ASSEMBLYAI_API_KEY=your_assemblyai_key
GEMINI_API_KEY=your_gemini_key
MURF_API_KEY=your_murf_key

# Optional
FFMPEG_PATH=C:\\path\\to\\ffmpeg\\bin   # Windows example
# FFMPEG_PATH=/usr/local/bin                   # macOS/Linux example
```
Notes:
- If keys are missing/placeholder, the app remains functional with fallbacks
- On Windows, ensure `ffmpeg.exe` and `ffprobe.exe` are at `FFMPEG_PATH`

## 🛠️ Setup & Run
### 1) Create env and install deps
```bash
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate
pip install -r requirements.txt

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Run the server
```bash
python main.py
# Server: http://127.0.0.1:8000
# UI:     http://127.0.0.1:8000
```

### 3) Open the UI
- Visit `http://127.0.0.1:8000`
- Click “Start Conversation” then “Record Message” (or press SPACE)

## 🧪 Testing & Diagnostics
### Health & Diagnostics
```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/agent/diagnostics
```

### Simulate errors
```bash
# Temporarily comment out API keys in main.py (backup first)
python simulate_failures.py backup
python simulate_failures.py fail assemblyai
python simulate_failures.py fail gemini
python simulate_failures.py fail murf
python simulate_failures.py fail all

# Restore
python simulate_failures.py restore
```

### Test suite / demo
```bash
python test_errors.py
python demo_robust_features.py
```

### Full pipeline test (with a sample file)
```bash
curl -X POST http://127.0.0.1:8000/agent/chat/test-session \
  -F "file=@uploads/recording_20250806_212815.webm" \
  -F "voice_id=en-US-natalie"
```

## 🔁 Robust Error Handling
- Standardized error schema from server with `error_type`, `fallback_used`
- Client timeout, retry button, user-friendly messages
- Fallback layers: Murf → gTTS → text-only
- Health checks every 30s with API status warnings

For details, see `ROBUST_ERROR_HANDLING.md`.

## 🖼️ Screenshots
Add screenshots to `static/` and reference them here.

![UI Screenshot](static/screenshot-ui.png)
![Diagnostics Screenshot](static/screenshot-diagnostics.png)

## 💡 Tips
- Press SPACE to record while conversation is active
- Use Auto-Mode to continue the conversation hands-free
- Check `pipeline_status` block in responses for step-level success

## 📣 Share on LinkedIn
1. Open `README.md` in your editor
2. Take a screenshot of the top section (title + features + architecture)
3. Post on LinkedIn with a short write-up:
   - What you built and why
   - Challenges and how you handled failures
   - A short clip/GIF of it working

Example caption:
> Built a robust AI Voice Agent with graceful fallbacks. Even when STT/LLM/TTS APIs go down, users still get helpful responses. Full write-up in the repo – would love feedback!

---

Made with ❤️. Contributions and suggestions welcome!
