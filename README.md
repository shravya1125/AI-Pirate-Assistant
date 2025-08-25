# 🏴‍☠️ Captain Blackbeard — AI Pirate Voice Agent

An AI voice agent with the soul of **Captain Blackbeard**! ⚓ Powered by **FastAPI**, **Gemini (LLM)**, and **Murf AI (TTS)**, this project brings short, salty pirate banter to life with both text 💬 and speech 🎤.  

---

## ⚡ Features

- 🏴 Pirate persona: replies in short, salty banter  
- 🎨 Pirate-themed UI (`captain2.html`)  
- 🎤 Voice input using browser **SpeechRecognition API**  
- 🔊 Speech output using **Murf AI TTS** (with fallback to browser TTS)  
- 📜 Session memory to keep conversations flowing  
- ⚡ FastAPI backend (`captain.py`) handling text + voice chat  

---

## 📂 Project Structure

.
│
├── captain.py # Backend — FastAPI server, LLM + Murf integration
├── captain3.html # Frontend — Pirate UI + PirateVoiceAgent JS
└── .env # (optional) Store API keys here  


---

## 🔑 Requirements

- Python **3.9+**  
- API Keys:  
  - `MURF_API_KEY` → [Murf AI](https://murf.ai/)  
  - `GEMINI_API_KEY` → [Google AI Studio](https://aistudio.google.com/)  

---

## ⚙️ Setup

1. **Clone the repo & install dependencies**
   ```bash
   git clone https://github.com/yourusername/captain-blackbeard.git
   cd captain-blackbeard
   pip install fastapi uvicorn httpx google-generativeai python-multipart python-dotenv  


2. **Set environment variables**
Create a .env file in the project root:
   ```bash
   MURF_API_KEY=your_murf_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Run backend server**
uvicorn captain:app --reload --host 0.0.0.0 --port 5000

4. **Open frontend**

Open captain3.html directly in your browser.

It connects to http://localhost:5000 by default.  

---

## 🚢 How It Works

- Frontend (captain3.html)

- User speaks or types → JS (PirateVoiceAgent) sends request to backend

- Displays conversation (user + Captain Blackbeard)

- Plays Murf AI audio response

- Backend (captain.py)

- /chat/text → Gemini generates pirate reply

- /chat/voice → Transcribes audio → Gemini reply → Murf TTS response  

---

## ⚓ Demo

🎥 Demo clip here → Captain Blackbeard in action: short, salty pirate banter with speech + text.

---

## 🏴‍☠️ Credits

Built with 🐍 FastAPI + ⚓ Murf AI + 🧭 Gemini

Created as part of #30DaysOfAIVoiceAgents Challenge  

---

⚓ “Arrr, may yer code sail smoothly and yer bugs walk the plank!” 🏴‍☠️

