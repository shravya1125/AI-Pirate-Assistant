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
git clone https://github.com/yourusername/voicebot-tts-echo.git
cd voicebot-tts-echo
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Add your Murf API key

Create a .env file:
```bash
MURF_API_KEY=your_murf_api_key_here
```

4. Run the server
```bash
uvicorn main:app --reload
```
Backend will run on: http://127.0.0.1:8000

🌐 Project Structure

voicebot-tts-echo/
├── static/
│   ├── script.js
│   └── styles.css
├── templates/
│   └── index.html
├── main.py
├── requirements.txt
└── README.md

📡 API Endpoint
POST /generate-audio

Request Body:
```bash
{
  "text": "Hello, this is a test.",
  "voice_id": "en-AU-kylie"
}
```

Response:
```bash
{
  "audioFile": "/static/audio/output.mp3"
}
```

🎯 Future Improvements

Add voice-to-text (STT) support

Support multiple languages or voices

Deploy to Render / Vercel / Replit

🙋‍♀️ Author
Shreya S
LinkedIn | GitHub

📄 License
MIT License – Free to use & share!

🏷️ Tags
#VoiceBot #FastAPI #MurfAPI #TTS #Echo #WebApp #AI


---

Let me know if you'd like:
- The `.env` setup guide
- A deployment-ready version (Render or Replit)
- Video demo script or editing help  
- GIF creation for the LinkedIn preview

Ready to push this live!
