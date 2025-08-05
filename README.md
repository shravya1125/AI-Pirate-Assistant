# 🎙️ VoiceBot with TTS & Echo 🎧

An interactive voice bot web application that supports both:
- **Text-to-Speech (TTS)** generation via Murf API
- **Echo audio playback** via in-browser recording

---

## 🔥 Features

✅ Enter text and generate realistic audio using TTS  
✅ Record voice and playback instantly (Echo Bot)  
✅ FastAPI backend with REST API endpoint  
✅ Simple frontend using HTML, CSS & JavaScript  
✅ Spinner loading animation while TTS is generating  
✅ Modular & beginner-friendly

---

## 📸 Preview

![screenshot](preview.png) 

---

## ⚙️ Tech Stack

| Layer       | Tech Used                 |
|-------------|---------------------------|
| Backend     | FastAPI (Python)          |
| TTS API     | Murf REST API             |
| Frontend    | HTML, CSS, JavaScript     |
| Audio Input | MediaRecorder API         |

---

## 🚀 Run Locally

### 1. Clone the repo

```bash
python -m venv venv
venv\Scripts\activate
pip install flask
python app.py
```
🚀 More coming every day!

🎤 Day 2 Task: Connect to Murf.ai’s REST API for Text-to-Speech!

🚀 Built a FastAPI endpoint `/generate-audio` that accepts text and returns a URL to an audio file. API key secured with `.env`.

🧠 Tools:
- FastAPI
- Murf.ai
- REST API
- Swagger UI (localhost:8000/docs)

Day 3: Play TTS Audio on Web UI
Today’s task was all about creating a seamless voice experience on the frontend! 🗣️✨
 🔹 I built a simple HTML page with a text input and a button.
 🔹 When the user submits text, it makes a POST request to my FastAPI /generate-audio endpoint.
 🔹 The backend calls Murf’s REST TTS API to generate audio and sends back a playable URL.
 🔹 The frontend receives that URL and plays the audio in an <audio> player element – all dynamically handled using JavaScript!
🧠 Skills Applied:
RESTful API Integration (Murf TTS)
FastAPI backend
CORS handling
Fetch API in JS
Audio playback on frontend
🔐 API keys stored securely in .env, keeping best practices in mind!
Thanks to the hashtag#MurfAI team for this hands-on learning experience 🙌
Can’t wait to take this further with more advanced voice features!