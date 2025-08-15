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
├─ schemas/
│  └─ models.py  
├─ services/
│  └─ llm.py  
|  └─ memory.py 
|  └─ stt.py 
|  └─ tts.py
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
# FFMPEG_PATH=/usr/local/bin            # macOS/Linux example
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
<img width="1366" height="768" alt="Screenshot (84)" src="https://github.com/user-attachments/assets/e748461b-d02e-41fe-96d3-4ab25f91f7de" />

## 💡 Tips
- Press SPACE to record while conversation is active
- Use Auto-Mode to continue the conversation hands-free
- Check `pipeline_status` block in responses for step-level success


---

## 🛠 Build Progress

<details>
<summary>📅 Click to expand — Day 1 to Day 14 progress</summary>

### [Day 1](https://www.linkedin.com/posts/shreya-s-5685232ab_30daysofvoiceagents-buildwithmurf-30daysofvoiceagents-activity-7357343462360322048-xwKe?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – Project Setup  
- FastAPI backend skeleton  
- Basic HTML/CSS/JS frontend

### [Day 2](https://www.linkedin.com/posts/shreya-s-5685232ab_30daysofvoiceagents-ai-tts-activity-7357795416802807810-M70-?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – Text-to-Speech with Murf API  
- Built /generate-audio endpoint  
- Returns playable audio URL from given text  

### [Day 3](https://www.linkedin.com/posts/shreya-s-5685232ab_30daysofvoiceagents-murfai-buildwithmurf-activity-7358173427288952832-I7_a?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – Play TTS Audio on Web UI  
- Integrated fetch API to call backend  
- Dynamically plays audio in <audio> element  

### [Day 4](https://www.linkedin.com/posts/shreya-s-5685232ab_30daysofaivoiceagents-mediarecorder-30dayschallenge-activity-7358506915213033472-EW6g?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – Echo Bot v1  
- MediaRecorder API to capture microphone input  
- Instantly plays back recorded voice  

### [Day 5](https://www.linkedin.com/posts/shreya-s-5685232ab_30daysofaivoiceagents-murfai-buildwithmurf-activity-7358898454552612864-vJFM?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – Send Audio to Server  
- /upload-audio endpoint  
- Saves uploaded files to /uploads directory  

### [Day 6](https://www.linkedin.com/posts/shreya-s-5685232ab_30daysofaivoiceagents-30daysofvoiceagents-activity-7359271368774873089-fcaN?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – Speech Transcription  
- Integrated AssemblyAI for transcription  
- Displays transcript in browser  

### [Day 7](https://www.linkedin.com/posts/shreya-s-5685232ab_30daysofvoiceagents-ai-voiceai-activity-7359637529605623808-GoV_?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – Echo Bot v2  
- Record → Transcribe → Murf TTS → Playback  
- Added voice selection from Murf API  

### [Day 8](https://www.linkedin.com/posts/shreya-s-5685232ab_ai-voiceagents-gemini-activity-7360009252981149697-elkc?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – LLM Integration  
- /llm/query endpoint  
- Sends text to Gemini API and returns AI response  

### [Day 9](https://www.linkedin.com/posts/shreya-s-5685232ab_ai-voiceai-llm-activity-7360434838731960321-d0Fj?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – Full Non-Streaming Pipeline  
- Voice in → STT → LLM → TTS → AI voice out  
- Entire conversation handled with no typing  

### [Day 10](https://www.linkedin.com/posts/shreya-s-5685232ab_ai-voiceai-fastapi-activity-7360783451186221056-LhIq?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – Memory & Hands-Free Mode  
- Per-session chat history  
- Auto-record after bot finishes speaking  

### [Day 11](https://www.linkedin.com/posts/shreya-s-5685232ab_ai-softwaredevelopment-errorhandling-activity-7361175095244939264-Lr_j?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – Robust Error Handling  
- try/except blocks for STT, LLM, TTS APIs  
- Fallback audio: “I’m having trouble connecting right now.”  

### [Day 12](https://www.linkedin.com/posts/shreya-s-5685232ab_30daysofaivoiceagents-voiceai-conversationalai-activity-7361429562418704389-zco3?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) – UI Revamp  
- Single-tap recording button with live status  
- Minimal, modern conversational layout  
- Auto-play AI responses for smooth flow 

### [Day 13](https://www.linkedin.com/posts/shreya-s-5685232ab_documentation-readme-softwaredevelopment-activity-7361820918190428160-lgr2?utm_source=share&utm_medium=member_desktop&rcm=ACoAAEqmZWABQoQd7GPvz8EDIg31Jt4Su3UUv8k) - Documentatiom
- Wrote comprehensive README.md

### [Day 14]() - Refactoring
- Refactored code, added schemas, logging, and robust error handling — published public repo

</details>

---
💡 This project is part of my #30DaysOfAIVoiceAgents challenge — exploring voice-first AI interaction from the ground up. Special Thanks to #MurfAI.  

---

Made with ❤️. Contributions and suggestions welcome!
