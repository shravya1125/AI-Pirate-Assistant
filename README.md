# 🏴‍☠️ Captain Blackbeard – AI Voice Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&amp;logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-teal.svg?logo=fastapi&amp;logoColor=white" />
  <img src="https://img.shields.io/badge/JavaScript-ES6-yellow.svg?logo=javascript&amp;logoColor=black" />
  <img src="https://img.shields.io/badge/HTML5-orange.svg?logo=html5&amp;logoColor=white" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?;logoColor=white)" /> 
  <img src="https://img.shields.io/badge/Murf%20AI-TTS-purple.svg" />
  <img src="https://img.shields.io/badge/AssemblyAI-FF6F61" />
  <img src="https://img.shields.io/badge/Gemini%20LLM-green.svg" />
  <img src="https://img.shields.io/badge/WebSockets-4A90E2?;logoColor=white)" />
  <img src="https://img.shields.io/badge/Deployed%20on-Render-46E3B7?;logoColor=black)" />

</p>  



##  📖 Overview  

**Captain Blackbeard** (a.k.a. **AI-Pirate-Assistant**) is a voice-powered AI assistant with a pirate's swagger. It:
- **Listens** to your voice commands via browser.
- Uses **Gemini LLM** to craft intelligent, pirate-flavored responses.
- Speaks back using **Murf AI** for natural TTS.
- Keeps your API keys purely session-based—nothing is persistently stored.

It comprises:
- FastAPI backend.
- Pirate-themed frontend.  


## ⚡ Features

- **Voice Input** – Record and send audio directly from your browser  
- **AI-Powered Responses** – Integrates Gemini & other APIs for smart replies  
- **Voice Output** – Listen to AI’s response with Murf TTS  
- **Weather & News APIs** – Ask real-world updates instantly  
- **User Privacy First** – API keys live only in your session (not stored after reload)  
- **Deployed on Render** – Accessible from anywhere  


## 🚀 Demo  

Try it live here:  
👉 [AI Pirate Assistant on Render](https://ai-pirate-assistant.onrender.com/)  

⚠️ **Note:** You must enter your own API keys in the **Config modal** before using. Keys are **not saved** and will be cleared once the session ends.  



## 🛠️ Tech Stack  

- **Backend**: FastAPI (Python)  
- **Frontend**: HTML, CSS, JavaScript  
- **Audio Handling**: pydub, Web Audio API  
- **APIs Integrated**:  
  - Gemini API  
  - AssemblyAI (Speech-to-Text)  
  - Murf AI (Text-to-Speech)  
  - Weather API  
  - News API  
- **Deployment**: Render   


## 📂 Project Structure  

AI-Pirate-Assistant/  
├── captain.py      # FastAPI backend logic  
├── captain.html    # Frontend pirate-themed UI  
└── README.md       # Project documentation    


## ⚓ Getting Started 

### 1. Clone the Repo

```bash
git clone https://github.com/shravya1125/AI-Pirate-Assistant.git
cd AI-Pirate-Assistant
```

### 2. Backend Setup  

Create a virtual environment & install dependencies:  
```bash
pip install -r requirements.txt
```

Run FastAPI server
```bash
uvicorn captain:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Usage   

- Open captain.html in your browser.  
- Enter your Gemini LLM and Murf AI API keys in the config modal.  
- Click Speak to Captain, speak into your mic, and get responses with authentic pirate flair.     


## 🎮 How to Use  

1. Open the app (local or Render link).  
2. Enter your API keys in the Config modal.  
3. Speak into the mic 🎤 – your voice is transcribed.  
4. Captain Blackbeard (AI) responds with text + voice 🔊.  
5. Keys disappear after session ends – no storage.  

---

## 📸 Screenshots  

Voice Interaction                                                
 <img width="1366" height="768" alt="Screenshot (134)" src="https://github.com/user-attachments/assets/e91b0b36-76c2-4002-8ead-9e7133d4f87e" />

Config Modal                                                         
<img width="1366" height="768" alt="Screenshot (129)" src="https://github.com/user-attachments/assets/3cffdb5f-9d74-4663-a7c4-76ac4d5c46d0" />


## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to open a PR or start a discussion.  

## 🌟 Acknowledgements    

Captain Blackbeard was crafted as part of my learning & exploration journey. 🚀  
Special appreciation to the 30 Days of AI Voice Agents Challenge, which inspired and pushed me to bring this project to life. 🏴‍☠️  

---


⚓ “Arrr, may yer code sail smoothly and yer bugs walk the plank!” 🏴‍☠️

