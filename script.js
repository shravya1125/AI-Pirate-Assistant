class EchoBotV2 {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.startTime = null;
        this.timerInterval = null;
        
        // DOM elements
        this.recordBtn = document.getElementById('recordBtn');
        this.recordingIndicator = document.getElementById('recordingIndicator');
        this.statusText = document.getElementById('statusText');
        this.durationText = document.getElementById('durationText');
        this.transcriptionText = document.getElementById('transcriptionText');
        this.transcriptionSection = document.getElementById('transcriptionSection');
        this.audioSection = document.getElementById('audioSection');
        this.generatedAudio = document.getElementById('generatedAudio');
        this.progressSection = document.getElementById('progressSection');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.voiceSelect = document.getElementById('voiceSelect');
        
        // API base for FastAPI backend
        this.API_BASE_URL = (window.API_BASE_URL) || 'http://127.0.0.1:8000';
        
        this.init();
    }
    
    init() {
        this.recordBtn.addEventListener('click', () => this.toggleRecording());
        this.setupAudioContext();
        this.updateStatus('Ready to record');
    }
    
    async setupAudioContext() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                } 
            });
            this.stream = stream;
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.updateStatus('Microphone access denied');
        }
    }
    
    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }
    
    async startRecording() {
        try {
            if (!this.stream) {
                await this.setupAudioContext();
            }
            
            this.audioChunks = [];
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => this.handleRecordingStop();
            
            this.mediaRecorder.start(100);
            this.isRecording = true;
            this.startTime = Date.now();
            
            this.updateUI('recording');
            this.startTimer();
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.updateStatus('Error starting recording');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.stopTimer();
            this.updateUI('processing');
        }
    }
    
    async handleRecordingStop() {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        
        // Reset UI
        this.updateUI('idle');
        this.showProgress();
        
        try {
            // Build multipart form data for /llm/query
            this.updateProgress(25, 'Uploading audio...');
            const form = new FormData();
            form.append('file', audioBlob, 'recording.webm');
            form.append('voice_id', this.voiceSelect.value || 'en-US-natalie');

            // Send to backend which will transcribe -> LLM -> Murf
            this.updateProgress(55, 'Transcribing and generating response...');
            const response = await fetch(`${this.API_BASE_URL}/llm/query`, {
                method: 'POST',
                body: form,
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();
            const transcription = result.transcription || '';
            const audioUrl = result.audioFile || result.audioUrl || '';

            if (!audioUrl) {
                throw new Error('No audio generated');
            }

            this.updateProgress(100, 'Complete!');
            this.displayResults(transcription, audioUrl);
            try { this.generatedAudio.play(); } catch (_) {}

            setTimeout(() => this.hideProgress(), 800);

        } catch (error) {
            console.error('Error processing audio:', error);
            this.updateStatus(`Error: ${error.message}`);
            this.hideProgress();
        }
    }
    
    // Legacy method no longer used; kept for reference
    async transcribeAudio(_) { return this.getDemoTranscription(); }
    
    // Legacy method no longer used in consolidated pipeline
    async generateSpeech(_) { return this.getDemoAudioUrl(); }
    
    displayResults(transcription, audioUrl) {
        // Display transcription
        this.transcriptionText.textContent = transcription;
        this.transcriptionText.classList.add('has-content', 'fade-in');
        
        // Display audio
        this.generatedAudio.src = audioUrl;
        this.audioSection.classList.add('show', 'fade-in');
        
        this.updateStatus('Audio generated successfully!');
    }
    
    updateUI(state) {
        switch (state) {
            case 'recording':
                this.recordBtn.innerHTML = `
                    <span class="btn-icon">⏹️</span>
                    <span class="btn-text">Stop Recording</span>
                `;
                this.recordBtn.classList.add('recording');
                this.recordingIndicator.classList.add('active');
                this.updateStatus('Recording...');
                break;
                
            case 'processing':
                this.recordBtn.innerHTML = `
                    <span class="btn-icon">⏳</span>
                    <span class="btn-text">Processing...</span>
                `;
                this.recordBtn.classList.remove('recording');
                this.recordBtn.classList.add('processing');
                this.recordBtn.disabled = true;
                this.recordingIndicator.classList.remove('active');
                this.updateStatus('Processing audio...');
                break;
                
            case 'idle':
            default:
                this.recordBtn.innerHTML = `
                    <span class="btn-icon">🎤</span>
                    <span class="btn-text">Start Recording</span>
                `;
                this.recordBtn.classList.remove('recording', 'processing');
                this.recordBtn.disabled = false;
                this.recordingIndicator.classList.remove('active');
                break;
        }
    }
    
    updateStatus(status) {
        this.statusText.textContent = status;
    }
    
    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const seconds = Math.floor(elapsed / 1000);
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            
            this.durationText.textContent = 
                `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
        }, 1000);
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }
    
    showProgress() {
        this.progressSection.classList.add('show');
    }
    
    hideProgress() {
        this.progressSection.classList.remove('show');
        this.progressFill.style.width = '0%';
    }
    
    updateProgress(percentage, text) {
        this.progressFill.style.width = `${percentage}%`;
        this.progressText.textContent = text;
    }
    
    arrayBufferToBase64(buffer) {
        const bytes = new Uint8Array(buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }
    
    // Demo fallback methods
    getDemoTranscription() {
        const demoTexts = [
            "Hello, this is a demo transcription of your speech.",
            "This is Echo Bot version 2 with Murf voice generation.",
            "Your voice has been transcribed and will be converted to speech.",
            "Welcome to the future of voice technology!"
        ];
        return demoTexts[Math.floor(Math.random() * demoTexts.length)];
    }
    
    getDemoAudioUrl() {
        // Return a demo audio URL (you can replace with actual demo audio)
        return 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBjuU2u/neCgEYaTwvGkeADuN1e/LdCEJ';
    }
}

// Backend implementation example (Node.js/Express)
const backendExample = `
// server.js - Example backend implementation

const express = require('express');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json({limit: '50mb'}));

// Configure multer for file uploads
const upload = multer({ storage: multer.memoryStorage() });

// Environment variables
const ASSEMBLY_API_KEY = process.env.ASSEMBLY_API_KEY;
const MURF_API_KEY = process.env.MURF_API_KEY;

// Echo endpoint
app.post('/tts/echo', upload.single('audio'), async (req, res) => {
    try {
        const { audio, voice } = req.body;
        
        // Convert base64 to buffer
        const audioBuffer = Buffer.from(audio, 'base64');
        
        // Step 1: Transcribe with AssemblyAI
        const transcription = await transcribeAudio(audioBuffer);
        
        // Step 2: Generate speech with Murf
        const audioUrl = await generateMurfAudio(transcription, voice);
        
        res.json({
            transcription,
            audioUrl,
            voice
        });
        
    } catch (error) {
        console.error('Error in echo endpoint:', error);
        res.status(500).json({ error: error.message });
    }
});

async function transcribeAudio(audioBuffer) {
    try {
        // Upload to AssemblyAI
        const uploadResponse = await axios.post(
            'https://api.assemblyai.com/v2/upload',
            audioBuffer,
            {
                headers: {
                    'authorization': ASSEMBLY_API_KEY,
                    'content-type': 'application/octet-stream'
                }
            }
        );
        
        const uploadUrl = uploadResponse.data.upload_url;
        
        // Start transcription
        const transcriptResponse = await axios.post(
            'https://api.assemblyai.com/v2/transcript',
            {
                audio_url: uploadUrl,
                language_detection: true
            },
            {
                headers: {
                    'authorization': ASSEMBLY_API_KEY,
                    'content-type': 'application/json'
                }
            }
        );
        
        const transcriptId = transcriptResponse.data.id;
        
        // Poll for completion
        let transcript;
        do {
            await new Promise(resolve => setTimeout(resolve, 1000));
            const statusResponse = await axios.get(
                \`https://api.assemblyai.com/v2/transcript/\${transcriptId}\`,
                {
                    headers: {
                        'authorization': ASSEMBLY_API_KEY
                    }
                }
            );
            transcript = statusResponse.data;
        } while (transcript.status === 'processing' || transcript.status === 'queued');
        
        if (transcript.status === 'error') {
            throw new Error('Transcription failed');
        }
        
        return transcript.text;
        
    } catch (error) {
        throw new Error(\`Transcription error: \${error.message}\`);
    }
}

async function generateMurfAudio(text, voiceId) {
    try {
        const response = await axios.post(
            'https://api.murf.ai/v1/speech/generate',
            {
                text: text,
                voice: voiceId,
                format: 'mp3',
                speed: 1.0,
                pitch: 1.0
            },
            {
                headers: {
                    'Authorization': \`Bearer \${MURF_API_KEY}\`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        return response.data.audioUrl;
        
    } catch (error) {
        throw new Error(\`Murf API error: \${error.message}\`);
    }
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(\`Server running on port \${PORT}\`);
});
`;

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EchoBotV2();
});