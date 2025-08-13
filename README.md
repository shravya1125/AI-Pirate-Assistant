# 🎙️ AI VoiceBot – 30 Days of AI Voice Agents Challenge 

An interactive voice-first AI assistant that supports speech input, natural AI conversation, and realistic text-to-speech output — built over 30 days, one feature at a time.

---

## ⚡ Overview

This VoiceBot is a full-stack conversational AI that lets you talk to an AI as naturally as speaking to a person — no typing, no reading.  

It combines:

- **Speech-to-Text (STT)** for transcribing user audio  
- **Large Language Model (LLM)** for intelligent responses  
- **Text-to-Speech (TTS)** for speaking back naturally  
- **Memory & error handling** for smooth, resilient experiences  

---

## 🛠 Tech Stack

| Layer             | Technology Used               |
|------------------|-------------------------------|
| Backend           | FastAPI (Python)              |
| Speech-to-Text    | AssemblyAI                    |
| LLM               | Google Gemini Pro API         |
| Text-to-Speech    | Murf REST API                 |
| Frontend          | HTML, CSS, JavaScript         |
| Audio Input       | MediaRecorder API             |
| Deployment Ready  | CORS + .env secured API keys  |

---

## 🚀 Run Locally

```bash
# Clone the repository
git clone <repo-url> && cd voicebot

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start backend
uvicorn main:app --reload

Visit http://localhost:8000/docs for API testing.

---

📅 Build Progress

Day 1 – Project Setup
✅ FastAPI backend skeleton
✅ Basic HTML/CSS/JS frontend

Day 2 – Text-to-Speech with Murf API
Built /generate-audio endpoint
Returns playable audio URL from given text

Day 3 – Play TTS Audio on Web UI
Integrated fetch API to call backend
Dynamically plays audio in <audio> element

Day 4 – Echo Bot v1
MediaRecorder API to capture microphone input
Instantly plays back recorded voice

Day 5 – Send Audio to Server
/upload-audio endpoint
Saves uploaded files to /uploads directory

Day 6 – Speech Transcription
Integrated AssemblyAI for transcription
Displays transcript in browser

Day 7 – Echo Bot v2
Record → Transcribe → Murf TTS → Playback
Added voice selection from Murf API

Day 8 – LLM Integration
/llm/query endpoint
Sends text to Gemini API and returns AI response

Day 9 – Full Non-Streaming Pipeline
Voice in → STT → LLM → TTS → AI voice out
Entire conversation handled with no typing

Day 10 – Memory & Hands-Free Mode
Per-session chat history
Auto-record after bot finishes speaking

Day 11 – Robust Error Handling
try/except blocks for STT, LLM, TTS APIs
Fallback audio: “I’m having trouble connecting right now.”

Day 12 – UI Revamp
Single-tap recording button with live status
Minimal, modern conversational layout
Auto-play AI responses for smooth flow

---

🎯 What’s Next
Summarized chat memory to keep prompts short
Streaming audio responses
Multi-voice personalities

---

💡 This project is part of my #30DaysOfAIVoiceAgents challenge — exploring voice-first AI interaction from the ground up.
