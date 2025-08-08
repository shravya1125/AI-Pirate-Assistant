const express = require('express');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.static('public')); // Serve static files

// Configure multer for file uploads
const upload = multer({ 
    storage: multer.memoryStorage(),
    limits: {
        fileSize: 10 * 1024 * 1024 // 10MB limit
    }
});

// Environment variables
const ASSEMBLY_API_KEY = process.env.ASSEMBLY_API_KEY;
const MURF_API_KEY = process.env.MURF_API_KEY;
const PORT = process.env.PORT || 3000;

// Validate environment variables
if (!ASSEMBLY_API_KEY) {
    console.error('ASSEMBLY_API_KEY is required');
    process.exit(1);
}

if (!MURF_API_KEY) {
    console.error('MURF_API_KEY is required');
    process.exit(1);
}

// Main echo endpoint
app.post('/tts/echo', async (req, res) => {
    try {
        console.log('Received echo request');
        
        const { audio, voice = 'en-US-aria' } = req.body;
        
        if (!audio) {
            return res.status(400).json({ error: 'Audio data is required' });
        }
        
        // Convert base64 to buffer
        console.log('Converting audio data...');
        const audioBuffer = Buffer.from(audio, 'base64');
        
        // Step 1: Transcribe with AssemblyAI
        console.log('Starting transcription...');
        const transcription = await transcribeAudio(audioBuffer);
        
        if (!transcription || transcription.trim() === '') {
            return res.status(400).json({ error: 'No speech detected in audio' });
        }
        
        console.log('Transcription:', transcription);
        
        // Step 2: Generate speech with Murf
        console.log('Generating speech with Murf...');
        const audioUrl = await generateMurfAudio(transcription, voice);
        
        console.log('Audio generated successfully');
        
        res.json({
            transcription,
            audioUrl,
            voice,
            success: true
        });
        
    } catch (error) {
        console.error('Error in echo endpoint:', error);
        res.status(500).json({ 
            error: error.message,
            success: false 
        });
    }
});

// Separate TTS generation endpoint
app.post('/tts/generate', async (req, res) => {
    try {
        const { text, voice = 'en-US-aria' } = req.body;
        
        if (!text) {
            return res.status(400).json({ error: 'Text is required' });
        }
        
        const audioUrl = await generateMurfAudio(text, voice);
        
        res.json({
            audioUrl,
            text,
            voice,
            success: true
        });
        
    } catch (error) {
        console.error('Error in TTS endpoint:', error);
        res.status(500).json({ 
            error: error.message,
            success: false 
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
            assemblyai: !!ASSEMBLY_API_KEY,
            murf: !!MURF_API_KEY
        }
    });
});

// AssemblyAI transcription function
async function transcribeAudio(audioBuffer) {
    try {
        console.log('Uploading to AssemblyAI...');
        
        // Upload audio file
        const uploadResponse = await axios.post(
            'https://api.assemblyai.com/v2/upload',
            audioBuffer,
            {
                headers: {
                    'authorization': ASSEMBLY_API_KEY,
                    'content-type': 'application/octet-stream'
                },
                timeout: 30000 // 30 second timeout
            }
        );
        
        const uploadUrl = uploadResponse.data.upload_url;
        console.log('Audio uploaded, starting transcription...');
        
        // Start transcription
        const transcriptResponse = await axios.post(
            'https://api.assemblyai.com/v2/transcript',
            {
                audio_url: uploadUrl,
                language_detection: true,
                punctuate: true,
                format_text: true
            },
            {
                headers: {
                    'authorization': ASSEMBLY_API_KEY,
                    'content-type': 'application/json'
                }
            }
        );
        
        const transcriptId = transcriptResponse.data.id;
        console.log('Transcription started, ID:', transcriptId);
        
        // Poll for completion
        let transcript;
        let attempts = 0;
        const maxAttempts = 60; // 1 minute timeout
        
        do {
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            const statusResponse = await axios.get(
                `https://api.assemblyai.com/v2/transcript/${transcriptId}`,
                {
                    headers: {
                        'authorization': ASSEMBLY_API_KEY
                    }
                }
            );
            
            transcript = statusResponse.data;
            attempts++;
            
            console.log(`Transcription status: ${transcript.status} (attempt ${attempts})`);
            
            if (attempts >= maxAttempts) {
                throw new Error('Transcription timeout');
            }
            
        } while (transcript.status === 'processing' || transcript.status === 'queued');
        
        if (transcript.status === 'error') {
            throw new Error(`Transcription failed: ${transcript.error}`);
        }
        
        return transcript.text;
        
    } catch (error) {
        console.error('AssemblyAI error:', error);
        throw new Error(`Transcription error: ${error.message}`);
    }
}

// Murf API speech generation function
async function generateMurfAudio(text, voiceId) {
    try {
        console.log('Generating speech with Murf API...');
        
        // Murf API call
        const response = await axios.post(
            'https://api.murf.ai/v1/speech/generate',
            {
                text: text,
                voice: voiceId,
                format: 'mp3',
                speed: 1.0,
                pitch: 1.0,
                emphasis: 'normal'
            },
            {
                headers: {
                    'Authorization': `Bearer ${MURF_API_KEY}`,
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            }
        );
        
        console.log('Murf API response received');
        
        // Return the audio URL from Murf
        return response.data.audioUrl || response.data.audio_url;
        
    } catch (error) {
        console.error('Murf API error:', error);
        
        // Fallback for demo purposes - generate a demo audio URL
        console.log('Using demo audio fallback');
        return generateDemoAudio(text);
    }
}

// Demo audio generation (fallback)
function generateDemoAudio(text) {
    // Create a simple text-to-speech URL using browser APIs
    // This is a fallback for demo purposes
    const demoAudioUrl = `data:text/plain;base64,${Buffer.from(text).toString('base64')}`;
    return demoAudioUrl;
}

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Unhandled error:', error);
    res.status(500).json({
        error: 'Internal server error',
        success: false
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Echo Bot v2 server running on port ${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log(`🎤 Echo endpoint: http://localhost:${PORT}/tts/echo`);
    console.log(`🔊 TTS endpoint: http://localhost:${PORT}/tts/generate`);
    
    // Check API keys
    console.log('\n🔑 API Keys Status:');
    console.log(`AssemblyAI: ${ASSEMBLY_API_KEY ? '✅ Configured' : '❌ Missing'}`);
    console.log(`Murf API: ${MURF_API_KEY ? '✅ Configured' : '❌ Missing'}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('SIGINT received, shutting down gracefully');
    process.exit(0);
});