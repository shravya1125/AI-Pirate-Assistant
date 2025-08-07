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

🧠 Skills Applied: RESTful API Integration (Murf TTS), FastAPI backend, CORS handling, Fetch API in JS,Audio playback on frontend
🔐 API keys stored securely in .env, keeping best practices in mind!
Can’t wait to take this further with more advanced voice features!

Day 4 of the hashtag#30DaysOfAIVoiceAgents challenge is complete!
Today’s task: Build an Echo Bot using the MediaRecorder API!
Now my bot can record my voice and instantly play it back!🎙️
I created a full-stack application that:
🔹 Accepts voice or text input 
🔹 Uses Murf API to generate realistic TTS audio 
🔹 Echoes back recorded audio via MediaRecorder 
🔹 Built with FastAPI, JavaScript, and HTML/CSS 
🔹 Fully interactive and plays audio directly in the browser!

Day 5: Send Audio to the Server 
Today’s task was about building a complete voice upload pipeline. After recording my voice using the Echo Bot I built earlier, I now upload that audio to my FastAPI backend using a new /upload-audio endpoint! 
hashtag#MurfAI hashtag#BuildWithMurf
📌 Features:
 ✅ Uses MediaRecorder to capture audio
 ✅ Uploads audio to backend after recording
 ✅ Stores audio in an /uploads directory
 ✅ Displays upload status and file details in the UI

Day 6: Transcribe Audio with AssemblyAI
Today, I integrated audio transcription into my voice agent! 🔊➡️✍️
 ✅ Recorded audio using the browser
 ✅ Sent it to my FastAPI server
 ✅ Used AssemblyAI to transcribe audio in real time
 ✅ Displayed the transcription in the UI
🔧Tools Used: FastAPI, AssemblyAI Python SDK, JavaScript (MediaRecorder API), HTML/CSS