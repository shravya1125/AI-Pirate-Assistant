
# 🏴‍☠️ AI Pirate Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&amp;logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-teal.svg?logo=fastapi&amp;logoColor=white" />
  <img src="https://img.shields.io/badge/JavaScript-ES6-yellow.svg?logo=javascript&amp;logoColor=black" />
  <img src="https://img.shields.io/badge/HTML5-orange.svg?logo=html5&amp;logoColor=white" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?;logoColor=white)" /> 
  <img src="https://img.shields.io/badge/Murf%20AI-TTS-purple.svg" />
  <img src="https://img.shields.io/badge/AssemblyAI-FF6F61" />
  <img src="https://img.shields.io/badge/Gemini%20LLM-green.svg" />
  <img src="https://img.shields.io/badge/Deployed%20on-Render-46E3B7?;logoColor=black)" />

</p>  

A voice-enabled AI assistant that combines speech recognition,
LLM-powered conversation, and text-to-speech to provide an
interactive browser-based assistant.


## ⚡ Features

- **Voice Input** – Record and send audio directly from your browser  
- **AI-Powered Responses** – Integrates Gemini & other APIs for smart replies  
- **Voice Output** – Listen to AI’s response with Murf TTS  
- **Weather & News APIs** – Ask real-world updates instantly  
- **User Privacy First** – API keys live only in your session (not stored after reload)  
- **Deployed on Render** – Accessible from anywhere  


## 🚀 Demo  

Try it live here:  👉 [AI Pirate Assistant on Render](https://ai-pirate-assistant.onrender.com/)  

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



## 📂 Project Structure  

AI-Pirate-Assistant/  
├── captain.py      # FastAPI backend logic  
├── captain3.html    # Frontend pirate-themed UI  
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

## 🚀 Deployment

The application is deployed using Render.  


## 🏆 Murf AI 30-Day Challenge

Built as part of the Murf AI 30-Day AI Voice Agents Challenge.

The development process and daily challenge submissions were documented on LinkedIn.

## 📸 Screenshots  

Voice Interaction                                                
 <img width="1366" height="768" alt="Screenshot (134)" src="https://github.com/user-attachments/assets/e91b0b36-76c2-4002-8ead-9e7133d4f87e" />

Config Modal                                                         
<img width="1366" height="768" alt="Screenshot (129)" src="https://github.com/user-attachments/assets/3cffdb5f-9d74-4663-a7c4-76ac4d5c46d0" />


## 👩‍💻 Author

Shreya Sati
