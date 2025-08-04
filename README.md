# 🎤 30 Days of Voice Agents

Day 1: ✅ Project setup using Flask and a simple HTML+JS frontend

## Features
- Python Flask backend
- HTML/JS frontend served from Flask
- Basic page styled with CSS
- Ready for voice integrations in upcoming days

## How to Run

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