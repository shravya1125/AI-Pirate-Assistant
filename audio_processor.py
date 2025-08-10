import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple, List, BinaryIO

import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import which
import assemblyai as aai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, assemblyai_api_key: Optional[str] = None):
        self.assemblyai_api_key = assemblyai_api_key
        if assemblyai_api_key:
            aai.settings.api_key = assemblyai_api_key
        
        # Check for ffmpeg
        if not which("ffmpeg"):
            logger.warning("ffmpeg not found. Audio conversion may fail.")
        
    def validate_audio_file(self, file_path: str) -> bool:
        """Validate that the file contains audio data"""
        try:
            # Try to load with pydub
            audio = AudioSegment.from_file(file_path)
            
            # Check basic properties
            if len(audio) == 0:
                logger.error("Audio file has zero duration")
                return False
                
            if audio.frame_rate == 0:
                logger.error("Audio file has invalid frame rate")
                return False
                
            logger.info(f"Audio validation passed: {len(audio)}ms duration, {audio.frame_rate}Hz, {audio.channels} channels")
            return True
            
        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            return False

    def convert_to_wav(self, input_path: str, output_path: str) -> bool:
        """Convert audio file to WAV format with proper settings"""
        try:
            logger.info(f"Converting {input_path} to WAV...")
            
            # Load the audio file
            audio = AudioSegment.from_file(input_path)
            
            # Normalize audio settings for better transcription
            # Convert to mono, 16kHz, 16-bit (standard for speech recognition)
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(16000)  # 16kHz
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Normalize volume
            audio = audio.normalize()
            
            # Export to WAV
            audio.export(output_path, format="wav")
            
            logger.info(f"Successfully converted to WAV: {output_path}")
            logger.info(f"Final audio specs: {len(audio)}ms, {audio.frame_rate}Hz, {audio.channels}ch")
            
            return True
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return False

    def transcribe_with_assemblyai(self, audio_path: str) -> Optional[str]:
        """Transcribe audio using AssemblyAI"""
        if not self.assemblyai_api_key:
            logger.info("No AssemblyAI API key provided, skipping...")
            return None
            
        try:
            logger.info("Starting AssemblyAI transcription...")
            
            # Validate file exists and has content
            if not os.path.exists(audio_path):
                raise Exception(f"Audio file not found: {audio_path}")
                
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                raise Exception("Audio file is empty")
                
            logger.info(f"Audio file size: {file_size} bytes")
            
            # Upload and transcribe
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_path)
            
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"AssemblyAI transcription failed: {transcript.error}")
                
            if not transcript.text or transcript.text.strip() == "":
                logger.warning("AssemblyAI returned empty transcription")
                return None
                
            logger.info(f"AssemblyAI transcription successful: '{transcript.text[:100]}...'")
            return transcript.text.strip()
            
        except Exception as e:
            logger.error(f"AssemblyAI transcription error: {e}")
            return None

    def transcribe_with_speech_recognition(self, audio_path: str) -> Optional[str]:
        """Transcribe audio using speech_recognition library"""
        try:
            logger.info("Starting speech_recognition transcription...")
            
            recognizer = sr.Recognizer()
            
            # Load audio file
            with sr.AudioFile(audio_path) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Record the audio
                audio_data = recognizer.record(source)
                
            # Try Google Speech Recognition (free)
            try:
                text = recognizer.recognize_google(audio_data)
                if text and text.strip():
                    logger.info(f"Google Speech Recognition successful: '{text[:100]}...'")
                    return text.strip()
            except sr.UnknownValueError:
                logger.warning("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                logger.error(f"Google Speech Recognition request failed: {e}")
            
            # Fallback to Sphinx (offline)
            try:
                text = recognizer.recognize_sphinx(audio_data)
                if text and text.strip():
                    logger.info(f"Sphinx recognition successful: '{text[:100]}...'")
                    return text.strip()
            except sr.UnknownValueError:
                logger.warning("Sphinx could not understand audio")
            except sr.RequestError as e:
                logger.error(f"Sphinx recognition failed: {e}")
                
        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            
        return None

    def process_audio_file(self, uploaded_file: BinaryIO, file_extension: str = None) -> Tuple[Optional[str], List[str]]:
        """
        Process uploaded audio file and return transcription
        Returns: (transcription_text, cleanup_files)
        """
        temp_files = []
        
        try:
            # Determine file extension
            if not file_extension:
                file_extension = '.webm'  # Default for web recordings
            
            # Save uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_input:
                temp_input.write(uploaded_file.read())
                temp_input_path = temp_input.name
                temp_files.append(temp_input_path)
                
            logger.info(f"Saved uploaded file: {temp_input_path}")
            
            # Validate the original file
            if not self.validate_audio_file(temp_input_path):
                raise Exception("Uploaded file validation failed - file may be corrupted or empty")
            
            # Convert to WAV
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
                temp_wav_path = temp_wav.name
                temp_files.append(temp_wav_path)
                
            if not self.convert_to_wav(temp_input_path, temp_wav_path):
                raise Exception("Audio format conversion failed")
            
            # Validate converted WAV file
            if not self.validate_audio_file(temp_wav_path):
                raise Exception("WAV conversion produced invalid audio file")
            
            # Try transcription methods in order of preference
            transcription = None
            
            # Method 1: AssemblyAI
            if self.assemblyai_api_key:
                transcription = self.transcribe_with_assemblyai(temp_wav_path)
            
            # Method 2: Speech Recognition fallback
            if not transcription:
                logger.info("Trying speech_recognition fallback...")
                transcription = self.transcribe_with_speech_recognition(temp_wav_path)
            
            if not transcription:
                raise Exception("All transcription methods failed - audio may be unclear or too quiet")
            
            return transcription, temp_files
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            return None, temp_files


# # # Option 1: OpenAI Integration
# # async def call_llm_api(transcription: str) -> str:
# #     """Call OpenAI GPT API"""
# #     try:
# #         import openai
# #         import os
        
# #         client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
# #         response = client.chat.completions.create(
# #             model="gpt-3.5-turbo",  # or "gpt-4"
# #             messages=[
# #                 {"role": "system", "content": "You are a helpful AI assistant. Provide clear, concise answers."},
# #                 {"role": "user", "content": transcription}
# #             ],
# #             max_tokens=500,
# #             temperature=0.7
# #         )
        
# #         return response.choices[0].message.content.strip()
        
# #     except Exception as e:
# #         logger.error(f"OpenAI API call failed: {e}")
# #         raise Exception(f"LLM processing failed: {str(e)}")

# import google.generativeai as genai
# import os
# import logging
# import time
# import requests
# import json
# import tempfile
# import uuid

import os
import requests

async def call_llm_api(transcription: str) -> str:
    """Call Groq API using a currently supported model."""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise Exception("GROQ_API_KEY not found in environment variables")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant. Keep responses short and conversational for voice output."},
                {"role": "user", "content": transcription}
            ],
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        raise Exception(f"Groq API call failed: {e}")



# async def call_llm_api(transcription: str) -> str:
#     """Call Google Gemini API (OpenAI replacement)"""
#     try:
#         # Configure Gemini API
#         gemini_api_key = os.getenv('GEMINI_API_KEY')
#         if not gemini_api_key:
#             raise Exception("GEMINI_API_KEY not found in environment variables")
        
#         genai.configure(api_key=gemini_api_key)
        
#         # Initialize the model
#         model = genai.GenerativeModel('gemini-pro')
        
#         logger.info("Calling Google Gemini API...")
        
#         # Create the prompt with system instructions
#         prompt = f"""You are a helpful AI assistant. Provide clear, concise answers that are appropriate for voice interaction.

# User's voice message: "{transcription}"

# Please respond in a conversational, natural way that would work well when spoken aloud. Keep your response informative but not too lengthy for voice interaction."""
        
#         # Generate response
#         response = model.generate_content(
#             prompt,
#             generation_config=genai.types.GenerationConfig(
#                 candidate_count=1,
#                 max_output_tokens=500,
#                 temperature=0.7,
#             )
#         )
        
#         if not response or not response.text:
#             raise Exception("Gemini returned empty response")
        
#         result = response.text.strip()
#         logger.info(f"Gemini API successful: '{result[:100]}...'")
#         return result
        
#     except Exception as e:
#         logger.error(f"Gemini API call failed: {e}")


async def generate_murf_audio(text: str, voice_id: str) -> str:
    """Generate audio using Murf API"""
    try:
        import requests
        import json
        import os
        import time
        
        murf_api_key = os.getenv('MURF_API_KEY')
        if not murf_api_key:
            raise Exception("MURF_API_KEY not found in environment variables")
        
        # Murf API endpoint (check their documentation for the exact URL)
        base_url = "https://api.murf.ai/v1"
        
        headers = {
            "Authorization": f"Bearer {murf_api_key}",
            "Content-Type": "application/json"
        }
        
        # Step 1: Create TTS job
        payload = {
            "voiceId": voice_id,
            "text": text,
            "format": "WAV",  # or MP3
            "sampleRate": 22050,
            "speed": 1.0,
            "pitch": 1.0
        }
        
        logger.info(f"Creating Murf TTS job for voice: {voice_id}")
        
        response = requests.post(
            f"{base_url}/speech/generate",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Murf API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # Step 2: Check if we get direct audio URL or need to poll
        if "audioUrl" in result:
            logger.info("Murf audio generation successful")
            return result["audioUrl"]
        
        elif "jobId" in result:
            # Poll for completion
            job_id = result["jobId"]
            logger.info(f"Polling Murf job: {job_id}")
            
            for _ in range(30):  # Poll for 30 seconds max
                time.sleep(1)
                
                status_response = requests.get(
                    f"{base_url}/speech/status/{job_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    if status_data.get("status") == "completed":
                        logger.info("Murf job completed")
                        return status_data.get("audioUrl")
                    elif status_data.get("status") == "failed":
                        raise Exception("Murf job failed")
            
            raise Exception("Murf job timeout")
        
        else:
            raise Exception("Unexpected Murf API response format")
        
    except Exception as e:
        logger.error(f"Murf TTS failed: {e}")
        
        # Fallback to browser TTS or other service
        logger.info("Falling back to alternative TTS...")
        return await fallback_tts(text, voice_id)


async def fallback_tts(text: str, voice_id: str) -> str:
    """Fallback TTS using other services"""
    try:
        # Option 1: Use OpenAI TTS
        import openai
        import os
        import tempfile
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",  # or nova, echo, fable, onyx, shimmer
            input=text
        )
        
        # Save to temporary file and return path
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            response.stream_to_file(tmp_file.name)
            logger.info(f"OpenAI TTS fallback successful: {tmp_file.name}")
            return tmp_file.name
        
    except Exception as e:
        logger.error(f"Fallback TTS also failed: {e}")
        return None

# Alternative: Simple Python TTS fallback
async def simple_fallback_tts(text: str) -> str:
    """Very simple TTS using pyttsx3"""
    try:
        import pyttsx3
        import tempfile
        
        engine = pyttsx3.init()
        
        # Configure voice
        voices = engine.getProperty('voices')
        if voices:
            engine.setProperty('voice', voices[0].id)  # Use first available voice
        
        engine.setProperty('rate', 150)  # Speed
        engine.setProperty('volume', 0.9)  # Volume
        
        # Save to file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            engine.save_to_file(text, tmp_file.name)
            engine.runAndWait()
            logger.info(f"pyttsx3 fallback successful: {tmp_file.name}")
            return tmp_file.name
        
    except Exception as e:
        logger.error(f"Simple TTS fallback failed: {e}")
        return None

async def process_llm_query(file: BinaryIO, voice_id: str = "en-US-natalie") -> dict:
    """Process LLM query with improved audio handling"""
    temp_files = []
    
    try:
        logger.info("Starting LLM query pipeline...")
        logger.info(f"Requested voice: {voice_id}")
        
        # Initialize audio processor
        assemblyai_key = os.getenv('ASSEMBLYAI_API_KEY')  # Make sure this is set
        processor = AudioProcessor(assemblyai_key)
        
        # Process the audio file
        transcription, temp_files = processor.process_audio_file(file, '.webm')
        
        if not transcription:
            raise Exception("Failed to transcribe audio. Please speak clearly and try again.")
        
        logger.info(f"Transcription successful: '{transcription[:100]}...'")
        
        # Send transcription to LLM
        llm_response = await call_llm_api(transcription)
        logger.info("LLM processing complete")
        
        # Generate audio response with Murf
        audio_url = await generate_murf_audio(llm_response, voice_id)
        
        return {
            "transcription": transcription,
            "llm_response": llm_response,
            "audioFile": audio_url,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"LLM pipeline error: {e}")
        raise Exception(f"Pipeline failed: {str(e)}")
        
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.info(f"Deleted temp file: {temp_file}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temp file {temp_file}: {cleanup_error}")


# import os
# import tempfile
# import logging
# from pathlib import Path
# from typing import Optional, Tuple, List, BinaryIO

# import speech_recognition as sr
# from pydub import AudioSegment
# from pydub.utils import which
# import assemblyai as aai

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class AudioProcessor:
#     def __init__(self, assemblyai_api_key: Optional[str] = None):
#         self.assemblyai_api_key = assemblyai_api_key
#         if assemblyai_api_key:
#             aai.settings.api_key = assemblyai_api_key
        
#         # Check for ffmpeg
#         if not which("ffmpeg"):
#             logger.warning("ffmpeg not found. Audio conversion may fail.")
        
#     def validate_audio_file(self, file_path: str) -> bool:
#         """Validate that the file contains audio data"""
#         try:
#             # Try to load with pydub
#             audio = AudioSegment.from_file(file_path)
            
#             # Check basic properties
#             if len(audio) == 0:
#                 logger.error("Audio file has zero duration")
#                 return False
                
#             if audio.frame_rate == 0:
#                 logger.error("Audio file has invalid frame rate")
#                 return False
                
#             logger.info(f"Audio validation passed: {len(audio)}ms duration, {audio.frame_rate}Hz, {audio.channels} channels")
#             return True
            
#         except Exception as e:
#             logger.error(f"Audio validation failed: {e}")
#             return False

#     def convert_to_wav(self, input_path: str, output_path: str) -> bool:
#         """Convert audio file to WAV format with proper settings"""
#         try:
#             logger.info(f"Converting {input_path} to WAV...")
            
#             # Load the audio file
#             audio = AudioSegment.from_file(input_path)
            
#             # Normalize audio settings for better transcription
#             # Convert to mono, 16kHz, 16-bit (standard for speech recognition)
#             audio = audio.set_channels(1)  # Mono
#             audio = audio.set_frame_rate(16000)  # 16kHz
#             audio = audio.set_sample_width(2)  # 16-bit
            
#             # Normalize volume
#             audio = audio.normalize()
            
#             # Export to WAV
#             audio.export(output_path, format="wav")
            
#             logger.info(f"Successfully converted to WAV: {output_path}")
#             logger.info(f"Final audio specs: {len(audio)}ms, {audio.frame_rate}Hz, {audio.channels}ch")
            
#             return True
            
#         except Exception as e:
#             logger.error(f"Audio conversion failed: {e}")
#             return False

#     def transcribe_with_assemblyai(self, audio_path: str) -> Optional[str]:
#         """Transcribe audio using AssemblyAI"""
#         if not self.assemblyai_api_key:
#             logger.info("No AssemblyAI API key provided, skipping...")
#             return None
            
#         try:
#             logger.info("Starting AssemblyAI transcription...")
            
#             # Validate file exists and has content
#             if not os.path.exists(audio_path):
#                 raise Exception(f"Audio file not found: {audio_path}")
                
#             file_size = os.path.getsize(audio_path)
#             if file_size == 0:
#                 raise Exception("Audio file is empty")
                
#             logger.info(f"Audio file size: {file_size} bytes")
            
#             # Upload and transcribe
#             transcriber = aai.Transcriber()
#             transcript = transcriber.transcribe(audio_path)
            
#             if transcript.status == aai.TranscriptStatus.error:
#                 raise Exception(f"AssemblyAI transcription failed: {transcript.error}")
                
#             if not transcript.text or transcript.text.strip() == "":
#                 logger.warning("AssemblyAI returned empty transcription")
#                 return None
                
#             logger.info(f"AssemblyAI transcription successful: '{transcript.text[:100]}...'")
#             return transcript.text.strip()
            
#         except Exception as e:
#             logger.error(f"AssemblyAI transcription error: {e}")
#             return None

#     def transcribe_with_speech_recognition(self, audio_path: str) -> Optional[str]:
#         """Transcribe audio using speech_recognition library"""
#         try:
#             logger.info("Starting speech_recognition transcription...")
            
#             recognizer = sr.Recognizer()
            
#             # Load audio file
#             with sr.AudioFile(audio_path) as source:
#                 # Adjust for ambient noise
#                 recognizer.adjust_for_ambient_noise(source, duration=0.5)
#                 # Record the audio
#                 audio_data = recognizer.record(source)
                
#             # Try Google Speech Recognition (free)
#             try:
#                 text = recognizer.recognize_google(audio_data)
#                 if text and text.strip():
#                     logger.info(f"Google Speech Recognition successful: '{text[:100]}...'")
#                     return text.strip()
#             except sr.UnknownValueError:
#                 logger.warning("Google Speech Recognition could not understand audio")
#             except sr.RequestError as e:
#                 logger.error(f"Google Speech Recognition request failed: {e}")
            
#             # Fallback to Sphinx (offline)
#             try:
#                 text = recognizer.recognize_sphinx(audio_data)
#                 if text and text.strip():
#                     logger.info(f"Sphinx recognition successful: '{text[:100]}...'")
#                     return text.strip()
#             except sr.UnknownValueError:
#                 logger.warning("Sphinx could not understand audio")
#             except sr.RequestError as e:
#                 logger.error(f"Sphinx recognition failed: {e}")
                
#         except Exception as e:
#             logger.error(f"Speech recognition failed: {e}")
            
#         return None

#     def process_audio_file(self, uploaded_file: BinaryIO, file_extension: str = None) -> Tuple[Optional[str], List[str]]:
#         """
#         Process uploaded audio file and return transcription
#         Returns: (transcription_text, cleanup_files)
#         """
#         temp_files = []
        
#         try:
#             # Determine file extension
#             if not file_extension:
#                 file_extension = '.webm'  # Default for web recordings
            
#             # Save uploaded file
#             with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_input:
#                 temp_input.write(uploaded_file.read())
#                 temp_input_path = temp_input.name
#                 temp_files.append(temp_input_path)
                
#             logger.info(f"Saved uploaded file: {temp_input_path}")
            
#             # Validate the original file
#             if not self.validate_audio_file(temp_input_path):
#                 raise Exception("Uploaded file validation failed - file may be corrupted or empty")
            
#             # Convert to WAV
#             with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_wav:
#                 temp_wav_path = temp_wav.name
#                 temp_files.append(temp_wav_path)
                
#             if not self.convert_to_wav(temp_input_path, temp_wav_path):
#                 raise Exception("Audio format conversion failed")
            
#             # Validate converted WAV file
#             if not self.validate_audio_file(temp_wav_path):
#                 raise Exception("WAV conversion produced invalid audio file")
            
#             # Try transcription methods in order of preference
#             transcription = None
            
#             # Method 1: AssemblyAI
#             if self.assemblyai_api_key:
#                 transcription = self.transcribe_with_assemblyai(temp_wav_path)
            
#             # Method 2: Speech Recognition fallback
#             if not transcription:
#                 logger.info("Trying speech_recognition fallback...")
#                 transcription = self.transcribe_with_speech_recognition(temp_wav_path)
            
#             if not transcription:
#                 raise Exception("All transcription methods failed - audio may be unclear or too quiet")
            
#             return transcription, temp_files
            
#         except Exception as e:
#             logger.error(f"Audio processing failed: {e}")
#             return None, temp_files


# async def call_llm_api(transcription: str) -> str:
#     """Smart rule-based AI responses - no API key needed"""
#     text = transcription.lower().strip()
    
#     logger.info(f"Processing question: '{text}'")
    
#     if "artificial intelligence" in text or " ai " in text or text.startswith("ai "):
#         return """Artificial Intelligence (AI) is a fascinating field of computer science that focuses 
#         on creating machines and systems capable of performing tasks that typically require human 
#         intelligence. This includes learning from data, recognizing patterns, making decisions, 
#         understanding natural language, and solving complex problems. 

#         AI can be categorized into narrow AI, which is designed for specific tasks like image 
#         recognition or language translation, and general AI, which would have human-like cognitive 
#         abilities across multiple domains. 

#         Today's AI systems use techniques like machine learning, deep learning, and neural networks 
#         to process vast amounts of data and improve their performance over time. Some common 
#         applications include virtual assistants like me, recommendation systems, autonomous vehicles, 
#         medical diagnosis, and natural language processing.

#         What's exciting is that AI is constantly evolving and finding new applications in fields 
#         like healthcare, education, finance, and entertainment!"""
    
#     elif "hello" in text or "hi " in text or "hey" in text or text.startswith("hi"):
#         return "Hello there! I'm your AI voice assistant, and I'm delighted to chat with you! I can help answer questions about technology, science, explain concepts, or just have a friendly conversation. What would you like to talk about today?"
    
#     elif "how are you" in text or "how do you do" in text:
#         return "I'm doing wonderful, thank you for asking! I'm here and ready to help with whatever questions or topics interest you. I love learning about what's on people's minds. How are you doing today?"
    
#     elif "machine learning" in text or "deep learning" in text:
#         return """Machine Learning is a subset of AI where computers learn to make predictions or 
#         decisions by finding patterns in data, rather than being explicitly programmed for every task. 

#         Deep Learning is a more advanced form of machine learning that uses neural networks with 
#         multiple layers - hence 'deep' - to process information in ways inspired by how the human 
#         brain works. 

#         These technologies power many things you use daily: photo recognition in your phone, 
#         language translation, recommendation systems on streaming platforms, and even this 
#         conversation we're having right now!"""
    
#     elif "weather" in text:
#         return "I don't have access to real-time weather data, but I'd recommend checking your local weather app or a reliable weather service like Weather.com or your phone's built-in weather app for the most current conditions and forecasts in your area."
    
#     elif "time" in text or "what time" in text:
#         import datetime
#         current_time = datetime.datetime.now()
#         formatted_time = current_time.strftime("%I:%M %p on %A, %B %d, %Y")
#         return f"The current time is {formatted_time}."
    
#     elif "joke" in text or "funny" in text or "laugh" in text:
#         jokes = [
#             "Why don't scientists trust atoms? Because they make up everything!",
#             "What do you call a fake noodle? An impasta!",
#             "Why did the scarecrow win an award? He was outstanding in his field!",
#             "What do you call a bear with no teeth? A gummy bear!",
#             "Why don't eggs tell jokes? They'd crack each other up!",
#             "What's the best thing about Switzerland? I don't know, but the flag is a big plus!",
#             "Why did the math book look so sad? Because it had too many problems!"
#         ]
#         import random
#         selected_joke = random.choice(jokes)
#         return f"Here's a joke for you: {selected_joke} I hope that brought a smile to your face!"
    
#     elif "python" in text or "programming" in text or "coding" in text:
#         return """Python is an incredibly popular and versatile programming language! It's known for 
#         its clean, readable syntax that makes it perfect for beginners, yet it's powerful enough for 
#         complex applications. 

#         Python is widely used in web development, data science, artificial intelligence, automation, 
#         scientific computing, and much more. Companies like Google, Netflix, Instagram, and Spotify 
#         use Python extensively. 

#         What makes Python special is its philosophy of making code readable and its vast ecosystem 
#         of libraries that let you accomplish almost anything you can imagine!"""
    
#     elif "science" in text:
#         return """Science is the systematic study of the natural world through observation, 
#         experimentation, and analysis. It's humanity's best tool for understanding how things work, 
#         from the tiniest particles to the vast cosmos. 

#         Science has given us incredible advances in medicine, technology, space exploration, and 
#         our understanding of life itself. What's beautiful about science is that it's always 
#         evolving - new discoveries constantly expand our knowledge and sometimes completely change 
#         how we see the world!"""
    
#     elif "music" in text:
#         return "Music is such a universal language! It has this amazing ability to evoke emotions, bring people together, and express things that words sometimes can't. Whether you enjoy classical symphonies, energetic rock, smooth jazz, or any other genre, music enriches our lives in countless ways. Do you have a favorite type of music or artist?"
    
#     elif "book" in text or "reading" in text:
#         return "Reading is like having a superpower! Books can transport you to different worlds, teach you new skills, introduce you to fascinating people and ideas, and expand your perspective. Whether you prefer thrilling novels, informative non-fiction, poetry, or graphic novels, there's something magical about getting lost in a good book."
    
#     elif "help" in text or "what can you" in text or "capabilities" in text:
#         return """I'm here to help with lots of things! I can:

#         • Answer questions about technology, science, and general knowledge
#         • Explain complex concepts in simple terms
#         • Have friendly conversations about various topics
#         • Share interesting facts and information
#         • Tell jokes and lighten the mood
#         • Provide information about programming, AI, and other subjects

#         Just speak naturally and ask me anything you're curious about. I love learning what interests people!"""
    
#     elif "thank you" in text or "thanks" in text:
#         return "You're very welcome! I'm happy I could help. It's my pleasure to chat with you and share information. Feel free to ask me anything else - I'm here whenever you need assistance or just want to have an interesting conversation!"
    
#     else:
#         # Extract key words for a more intelligent response
#         key_words = [word for word in text.split() if len(word) > 3]
        
#         response = f"""That's a great question! You asked: "{transcription}"

#         As your AI assistant, I find that really interesting to think about. """
        
#         if key_words:
#             response += f"I notice you mentioned {', '.join(key_words[:3])} - those are fascinating topics! "
        
#         response += """While I may not have a specific answer for everything, I'm always happy to explore ideas and share what I know. 

#         Is there a particular aspect of this topic you'd like to dive deeper into? Or feel free to ask me about technology, science, or anything else that sparks your curiosity!"""
        
#         return response


# async def generate_murf_audio(text: str, voice_id: str) -> str:
#     """
#     Generate audio using pyttsx3 (offline TTS) - completely free!
#     """
#     try:
#         import pyttsx3
#         import tempfile
#         import os
#         import uuid
#         import shutil
        
#         logger.info(f"Generating speech using pyttsx3 for voice: {voice_id}")
        
#         # Initialize the TTS engine
#         engine = pyttsx3.init()
        
#         # Configure voice properties
#         voices = engine.getProperty('voices')
#         if voices:
#             logger.info(f"Available voices: {len(voices)}")
#             # Try to find a good voice based on voice_id preference
#             selected_voice = None
            
#             if 'natalie' in voice_id.lower() or 'female' in voice_id.lower():
#                 # Look for female voices
#                 for voice in voices:
#                     if any(name in voice.name.lower() for name in ['zira', 'hazel', 'female', 'woman']):
#                         selected_voice = voice
#                         break
            
#             if not selected_voice and len(voices) > 1:
#                 # Use second voice if available (often different gender)
#                 selected_voice = voices[1]
#             elif not selected_voice:
#                 selected_voice = voices[0]
            
#             engine.setProperty('voice', selected_voice.id)
#             logger.info(f"Using voice: {selected_voice.name}")
        
#         # Set speech properties for natural-sounding speech
#         engine.setProperty('rate', 150)    # Slightly slower for clarity
#         engine.setProperty('volume', 0.9)  # High volume
        
#         # Create a unique filename in temp directory
#         filename = f"ai_response_{uuid.uuid4().hex[:8]}.wav"
#         temp_audio_path = os.path.join(tempfile.gettempdir(), filename)
        
#         # Generate the audio file
#         logger.info(f"Generating audio to: {temp_audio_path}")
#         engine.save_to_file(text, temp_audio_path)
#         engine.runAndWait()
        
#         # Verify the file was created and has content
#         if os.path.exists(temp_audio_path) and os.path.getsize(temp_audio_path) > 0:
#             file_size = os.path.getsize(temp_audio_path)
#             logger.info(f"Audio generated successfully: {temp_audio_path} ({file_size} bytes)")
            
#             # For web access, we need to serve this file
#             # Option 1: Return file path for local testing
#             return temp_audio_path.replace('\\', '/')
            
#         else:
#             logger.error("Audio file was not created or is empty")
#             return None
        
#     except ImportError:
#         logger.error("pyttsx3 not installed. Install with: pip install pyttsx3")
#         return None
#     except Exception as e:
#         logger.error(f"TTS generation failed: {e}")
#         return None


# async def process_llm_query(file: BinaryIO, voice_id: str = "en-US-natalie") -> dict:
#     """Process LLM query with improved audio handling"""
#     temp_files = []
    
#     try:
#         logger.info("Starting LLM query pipeline...")
#         logger.info(f"Requested voice: {voice_id}")
        
#         # Initialize audio processor
#         assemblyai_key = os.getenv('ASSEMBLYAI_API_KEY')  # Make sure this is set
#         processor = AudioProcessor(assemblyai_key)
        
#         # Process the audio file
#         transcription, temp_files = processor.process_audio_file(file, '.webm')
        
#         if not transcription:
#             raise Exception("Failed to transcribe audio. Please speak clearly and try again.")
        
#         logger.info(f"Transcription successful: '{transcription[:100]}...'")
        
#         # Send transcription to LLM
#         llm_response = await call_llm_api(transcription)
#         logger.info("LLM processing complete")
        
#         # Generate audio response with Murf
#         audio_url = await generate_murf_audio(llm_response, voice_id)
        
#         return {
#             "transcription": transcription,
#             "llm_response": llm_response,
#             "audioFile": audio_url,
#             "status": "success"
#         }
        
#     except Exception as e:
#         logger.error(f"LLM pipeline error: {e}")
#         raise Exception(f"Pipeline failed: {str(e)}")
        
#     finally:
#         # Cleanup temporary files
#         for temp_file in temp_files:
#             try:
#                 if os.path.exists(temp_file):
#                     os.unlink(temp_file)
#                     logger.info(f"Deleted temp file: {temp_file}")
#             except Exception as cleanup_error:
#                 logger.warning(f"Failed to delete temp file {temp_file}: {cleanup_error}")