import asyncio
import httpx
from flask import Flask, jsonify, request
from asgiref.wsgi import WsgiToAsgi

app = Flask(__name__)

@app.route('/')
def home():
    """A basic homepage endpoint."""
    return "<h1>Hello, Uvicorn!</h1><p>This is a Flask app running on an ASGI server.</p>"

@app.route('/health')
def health_check():
    """A health check endpoint that returns a JSON response."""
    return jsonify({"status": "healthy", "service": "main_app"})

@app.route('/greet')
def greet():
    """An endpoint that greets a user based on a query parameter."""
    name = request.args.get('name', 'World')
    return f"Hello, {name}!"

# -----------------------------------------------------------
# Asynchronous LLM Test Endpoint
# -----------------------------------------------------------

@app.route('/llm/test')
async def llm_test():
    """
    An asynchronous endpoint that simulates a call to an LLM.
    
    Using 'async def' allows Uvicorn to handle other requests while this
    function 'awaits' a long-running task, like an external API call.
    """
    print("Received request for LLM test...")
    
    # Simulate a long-running API call to an LLM.
    # In a real application, you would make an actual network request here.
    await asyncio.sleep(3)  # This pauses the function for 3 seconds without blocking the server.

    # Simulate the response from the LLM.
    response_data = {
        "status": "success",
        "message": "This is a simulated response from the LLM.",
        "request_id": "12345-abcde",
        "generated_text": "The quick brown fox jumps over the lazy dog."
    }
    
    print("LLM test complete. Sending response.")
    return jsonify(response_data)


# -----------------------------------------------------------
# POST Endpoint for LLM Query
# -----------------------------------------------------------
@app.route('/llm/query', methods=['POST'])
async def llm_query():
    """
    An async endpoint to query an LLM (e.g., Google Gemini API).
    
    This endpoint expects a JSON body with a 'text' field and returns a
    JSON response with the generated text from the LLM.
    """
    try:
        # Get the request body as JSON.
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Invalid request body. 'text' field is required."}), 400

        user_prompt = data['text']
        print(f"Received LLM query: {user_prompt}")

        # --- Gemini API Configuration ---
        # NOTE: Replace 'YOUR_API_KEY' with your actual Google Gemini API key.
        # It's recommended to load this from an environment variable.
        GEMINI_API_KEY = "AIzaSyBZZeifBSpKxC1QPS88_2zCq8q-kBBZCos"
        MODEL_NAME = "gemini-2.5-flash-preview-05-20"
        API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
        
        # --- API Request Payload ---
        payload = {
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ]
        }
        
        # --- Make the Asynchronous API Call ---
        # We use httpx, an async-compatible HTTP client, to make the request.
        # You'll need to install it: pip install httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(API_URL, json=payload, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx).

        # --- Process the API Response ---
        api_response = response.json()
        generated_text = api_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Handle cases where the LLM might have safety-related blocks.
        if not generated_text:
            return jsonify({"error": "LLM response was blocked or empty. Please try a different prompt."}), 400

        print("LLM API call successful.")
        return jsonify({"generated_text": generated_text})

    except httpx.HTTPStatusError as e:
        print(f"HTTP error during LLM call: {e}")
        return jsonify({"error": f"LLM API returned an error: {e}"}), e.response.status_code
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


# -----------------------------------------------------------
# ASGI Integration
# -----------------------------------------------------------

# This is the crucial step. We wrap the Flask WSGI application instance `app`
# with WsgiToAsgi to create a new, ASGI-compatible application instance.
# Uvicorn will now be able to run this `asgi_app` variable correctly.
asgi_app = WsgiToAsgi(app)




# from fastapi import FastAPI, File, UploadFile, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# import os
# import shutil
# import tempfile
# from datetime import datetime
# from pathlib import Path
# import mimetypes
# import assemblyai as aai
# from typing import Optional

# app = FastAPI(title="AI Voice Agent Server", version="1.0.0")

# ASSEMBLYAI_API_KEY = "1facf73354b34dd68c40b02dd78d40aa"
# aai.settings.api_key = ASSEMBLYAI_API_KEY

# # Enable CORS for frontend communication
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# UPLOAD_DIRECTORY = "uploads"
# Path(UPLOAD_DIRECTORY).mkdir(exist_ok=True)

# # Your TTS endpoint
# @app.post("/generate-audio")
# async def generate_audio(request: dict):
#     """
#     Generate audio from text using a TTS service
    
#     Args:
#         request: Dictionary containing 'text' field
        
#     Returns:
#         JSON response with audio file URL or data
#     """
#     try:
#         text = request.get("text", "").strip()
        
#         if not text:
#             raise HTTPException(status_code=400, detail="Text field is required and cannot be empty")
        
#         if len(text) > 1000:
#             raise HTTPException(status_code=400, detail="Text is too long. Maximum 1000 characters allowed.")
        
#         print(f"🎵 TTS Request received:")
#         print(f"   📝 Text: {text[:100]}{'...' if len(text) > 100 else ''}")
#         print(f"   📏 Length: {len(text)} characters")
        
#         # Option 1: Using gTTS (Google Text-to-Speech) - Free option
#         try:
#             from gtts import gTTS
#             import io
#             import base64
            
#             # Generate speech
#             tts = gTTS(text=text, lang='en', slow=False)
            
#             # Save to bytes buffer
#             audio_buffer = io.BytesIO()
#             tts.write_to_fp(audio_buffer)
#             audio_buffer.seek(0)
            
#             # Convert to base64 for embedding
#             audio_data = audio_buffer.read()
#             audio_b64 = base64.b64encode(audio_data).decode()
#             audio_url = f"data:audio/mp3;base64,{audio_b64}"
            
#             print("✅ TTS generated successfully using gTTS")
            
#             return {
#                 "status": "success",
#                 "message": "Audio generated successfully",
#                 "audioFile": audio_url,
#                 "text_length": len(text),
#                 "audio_format": "mp3",
#                 "service": "gTTS"
#             }
            
#         except ImportError:
#             # Option 2: Using Web Speech API simulation (fallback)
#             print("⚠️ gTTS not available, using fallback method")
            
#             # Create a simple response for Web Speech API to handle on frontend
#             return {
#                 "status": "success",
#                 "message": "Use browser's speech synthesis",
#                 "audioFile": None,
#                 "text": text,
#                 "use_browser_tts": True,
#                 "service": "Browser Speech API"
#             }
            
#     except Exception as e:
#         print(f"❌ TTS Error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

# # New endpoint for audio transcription
# @app.post("/transcribe/file")
# async def transcribe_file(file: UploadFile = File(...)):
#     try:
#         # Validate file type
#         if not file.content_type or not file.content_type.startswith('audio/'):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid file type. Expected audio file, got {file.content_type}"
#             )
        
#         print(f"     Starting transcription for file: {file.filename}")
#         print(f"     Content Type: {file.content_type}")
#         print(f"   📏 File Size: {file.size if hasattr(file, 'size') else 'Unknown'} bytes")
        
#         # Create a temporary file to store the uploaded audio
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
#             # Read and write the uploaded file content
#             content = await file.read()
#             temp_file.write(content)
#             temp_file_path = temp_file.name
        
#         try:
#             # Configure transcription settings (using correct AssemblyAI parameters)
#             config = aai.TranscriptionConfig(
#                 # Use correct parameter names for AssemblyAI
#                 speaker_labels=False,  # Enable speaker diarization if needed
#                 punctuate=True,        # Correct parameter name for punctuation
#                 format_text=True,      # Format the text properly
#                 language_code="en",    # Specify language
#             )
            
#             # Create transcriber instance
#             transcriber = aai.Transcriber(config=config)
            
#             print("🔄 Sending audio to AssemblyAI for transcription...")
            
#             # Transcribe the audio file
#             transcript = transcriber.transcribe(temp_file_path)
            
#             # Check if transcription was successful
#             if transcript.status == aai.TranscriptStatus.error:
#                 raise HTTPException(
#                     status_code=500,
#                     detail=f"Transcription failed: {transcript.error}"
#                 )
            
#             # Extract transcription details
#             transcription_text = transcript.text or ""
#             confidence = transcript.confidence or 0.0
#             audio_duration = transcript.audio_duration or 0
            
#             # Count words
#             word_count = len(transcription_text.split()) if transcription_text else 0
            
#             print(f"✅ Transcription completed successfully:")
#             print(f"   📝 Text: {transcription_text[:100]}{'...' if len(transcription_text) > 100 else ''}")
#             print(f"   📊 Confidence: {confidence:.2%}")
#             print(f"   ⏱️ Duration: {audio_duration}s")
#             print(f"   📝 Words: {word_count}")
            
#             # Prepare response
#             response_data = {
#                 "status": "success",
#                 "message": "Audio transcribed successfully",
#                 "transcription": transcription_text,
#                 "confidence": confidence,
#                 "audio_duration": audio_duration,
#                 "words": word_count,
#                 "language_detected": getattr(transcript, 'language_code', 'en'),
#                 "transcript_id": transcript.id,
#             }
            
#             # Add word-level details if available
#             if hasattr(transcript, 'words') and transcript.words:
#                 response_data['word_details'] = [
#                     {
#                         "text": word.text,
#                         "start": word.start,
#                         "end": word.end,
#                         "confidence": word.confidence
#                     }
#                     for word in transcript.words[:50]  # Limit to first 50 words for response size
#                 ]
            
#             return response_data
            
#         finally:
#             # Clean up temporary file
#             try:
#                 os.unlink(temp_file_path)
#                 print(f"🧹 Cleaned up temporary file: {temp_file_path}")
#             except OSError as e:
#                 print(f"⚠️ Warning: Could not delete temporary file {temp_file_path}: {e}")
        
#     except Exception as e:
#         print(f"❌ Error during transcription: {str(e)}")
#         if "API key" in str(e).lower():
#             raise HTTPException(
#                 status_code=500, 
#                 detail="AssemblyAI API key not configured or invalid. Please check your API key."
#             )
#         raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {str(e)}")

# # Enhanced upload endpoint (optional - for backward compatibility)
# @app.post("/upload-audio")
# async def upload_audio(audio: UploadFile = File(...)):
#     """
#     Upload audio file to server
    
#     Args:
#         audio: The audio file to upload
        
#     Returns:
#         JSON response with file details
#     """
#     try:
#         # Validate file type
#         if not audio.content_type.startswith('audio/'):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid file type. Expected audio file, got {audio.content_type}"
#             )
        
#         # Generate unique filename with timestamp
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         file_extension = os.path.splitext(audio.filename)[1] or '.webm'
#         unique_filename = f"recording_{timestamp}{file_extension}"
        
#         # Create full file path
#         file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)
        
#         # Save the file
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(audio.file, buffer)
        
#         # Get file information
#         file_stats = os.stat(file_path)
#         file_size = file_stats.st_size
        
#         # Determine content type
#         content_type = audio.content_type or mimetypes.guess_type(file_path)[0] or 'audio/webm'
        
#         # Log the upload
#         print(f"✅ Audio file uploaded successfully:")
#         print(f"   📁 Filename: {unique_filename}")
#         print(f"   📊 Size: {file_size} bytes ({file_size / 1024:.2f} KB)")
#         print(f"   🎵 Content Type: {content_type}")
#         print(f"   📍 Path: {file_path}")
        
#         # Return file information
#         return {
#             "status": "success",
#             "message": "Audio file uploaded successfully",
#             "filename": unique_filename,
#             "original_filename": audio.filename,
#             "size": file_size,
#             "size_formatted": format_file_size(file_size),
#             "content_type": content_type,
#             "upload_path": file_path,
#             "timestamp": timestamp
#         }
        
#     except Exception as e:
#         print(f"❌ Error uploading audio file: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to upload audio file: {str(e)}")

# def format_file_size(size_bytes):
#     """
#     Convert bytes to human readable format
    
#     Args:
#         size_bytes: Size in bytes
        
#     Returns:
#         Formatted string (e.g., "1.23 KB", "2.45 MB")
#     """
#     if size_bytes == 0:
#         return "0 B"
    
#     size_names = ["B", "KB", "MB", "GB", "TB"]
#     import math
#     i = int(math.floor(math.log(size_bytes, 1024)))
#     p = math.pow(1024, i)
#     s = round(size_bytes / p, 2)
#     return f"{s} {size_names[i]}"

# # Optional: Endpoint to list uploaded files
# @app.get("/list-uploads")
# async def list_uploads():
#     """
#     List all uploaded audio files
    
#     Returns:
#         JSON response with list of uploaded files
#     """
#     try:
#         files = []
#         upload_path = Path(UPLOAD_DIRECTORY)
        
#         for file_path in upload_path.glob("*"):
#             if file_path.is_file():
#                 file_stats = file_path.stat()
#                 files.append({
#                     "filename": file_path.name,
#                     "size": file_stats.st_size,
#                     "size_formatted": format_file_size(file_stats.st_size),
#                     "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
#                     "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
#                 })
        
#         return {
#             "status": "success",
#             "count": len(files),
#             "files": files
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

# # Optional: Endpoint to delete uploaded files
# @app.delete("/delete-upload/{filename}")
# async def delete_upload(filename: str):
#     """
#     Delete a specific uploaded file
    
#     Args:
#         filename: Name of the file to delete
        
#     Returns:
#         JSON response confirming deletion
#     """
#     try:
#         file_path = os.path.join(UPLOAD_DIRECTORY, filename)
        
#         if not os.path.exists(file_path):
#             raise HTTPException(status_code=404, detail="File not found")
        
#         # Security check - ensure file is in uploads directory
#         if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_DIRECTORY)):
#             raise HTTPException(status_code=400, detail="Invalid file path")
        
#         os.remove(file_path)
        
#         return {
#             "status": "success",
#             "message": f"File {filename} deleted successfully"
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

# # Health check endpoint
# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     return {
#         "status": "healthy",
#         "message": "AI Voice Agent Server is running",
#         "upload_directory": UPLOAD_DIRECTORY,
#         "upload_directory_exists": os.path.exists(UPLOAD_DIRECTORY)
#     }

# if __name__ == "__main__":
#     import uvicorn
    
#     print("🚀 Starting AI Voice Agent Server...")
#     print(f"📁 Upload directory: {os.path.abspath(UPLOAD_DIRECTORY)}")
#     print("🌐 Server will be available at: http://127.0.0.1:8000")
#     print("📋 API Documentation: http://127.0.0.1:8000/docs")
    
#     uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)


# from fastapi import FastAPI, File, UploadFile, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# import os
# import shutil
# import tempfile
# from datetime import datetime
# from pathlib import Path
# import mimetypes
# import assemblyai as aai
# import httpx
# import json
# from typing import Optional

# app = FastAPI(title="AI Voice Agent Server - Echo Bot v2", version="2.0.0")

# # API Keys - Replace with your actual keys
# ASSEMBLYAI_API_KEY = "1facf73354b34dd68c40b02dd78d40aa"  # Replace with your key
# MURF_API_KEY = "your_murf_api_key_here"  # Replace with your Murf API key

# aai.settings.api_key = ASSEMBLYAI_API_KEY

# # Enable CORS for frontend communication
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# UPLOAD_DIRECTORY = "uploads"
# Path(UPLOAD_DIRECTORY).mkdir(exist_ok=True)

# # NEW: Echo Bot v2 endpoint - Main feature for Day 7
# @app.post("/tts/echo")
# async def echo_bot_v2(file: UploadFile = File(...)):
#     """
#     Echo Bot v2: Transcribe audio with AssemblyAI and generate new audio with Murf API
    
#     Args:
#         file: Audio file to transcribe and convert back to speech
        
#     Returns:
#         JSON response with transcription and Murf-generated audio URL
#     """
#     try:
#         # Validate file type
#         if not file.content_type or not file.content_type.startswith('audio/'):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid file type. Expected audio file, got {file.content_type}"
#             )
        
#         print(f"🎤 Echo Bot v2 - Processing file: {file.filename}")
#         print(f"   📊 Content Type: {file.content_type}")
        
#         # Step 1: Save uploaded audio temporarily
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
#             content = await file.read()
#             temp_file.write(content)
#             temp_file_path = temp_file.name
        
#         try:
#             # Step 2: Transcribe audio with AssemblyAI
#             print("🔄 Step 1: Transcribing audio with AssemblyAI...")
#             transcription = await transcribe_with_assemblyai(temp_file_path)
            
#             if not transcription or transcription.strip() == "":
#                 raise HTTPException(
#                     status_code=400,
#                     detail="No speech detected in the audio file"
#                 )
            
#             print(f"✅ Transcription completed: {transcription[:100]}{'...' if len(transcription) > 100 else ''}")
            
#             # Step 3: Generate new audio with Murf API
#             print("🔄 Step 2: Generating speech with Murf AI...")
#             murf_audio_url = await generate_murf_audio(transcription)
            
#             print("✅ Echo Bot v2 processing completed successfully!")
            
#             return {
#                 "status": "success",
#                 "message": "Echo Bot v2 processing completed",
#                 "transcription": transcription,
#                 "murf_audio_url": murf_audio_url,
#                 "original_filename": file.filename,
#                 "processing_steps": [
#                     "Audio uploaded and validated",
#                     "Speech transcribed with AssemblyAI", 
#                     "New audio generated with Murf AI"
#                 ]
#             }
            
#         finally:
#             # Clean up temporary file
#             try:
#                 os.unlink(temp_file_path)
#                 print(f"🧹 Cleaned up temporary file: {temp_file_path}")
#             except OSError as e:
#                 print(f"⚠️ Warning: Could not delete temporary file {temp_file_path}: {e}")
        
#     except Exception as e:
#         print(f"❌ Echo Bot v2 Error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Echo Bot v2 failed: {str(e)}")

# async def transcribe_with_assemblyai(audio_file_path: str) -> str:
#     """
#     Transcribe audio file using AssemblyAI
    
#     Args:
#         audio_file_path: Path to the audio file
        
#     Returns:
#         Transcribed text
#     """
#     try:
#         # Configure transcription settings
#         config = aai.TranscriptionConfig(
#             speaker_labels=False,
#             punctuate=True,
#             format_text=True,
#             language_code="en",
#         )
        
#         # Create transcriber instance
#         transcriber = aai.Transcriber(config=config)
        
#         # Transcribe the audio file
#         transcript = transcriber.transcribe(audio_file_path)
        
#         # Check if transcription was successful
#         if transcript.status == aai.TranscriptStatus.error:
#             raise Exception(f"AssemblyAI transcription failed: {transcript.error}")
        
#         return transcript.text or ""
        
#     except Exception as e:
#         raise Exception(f"AssemblyAI transcription error: {str(e)}")

# async def generate_murf_audio(text: str, voice_id: str = "en-US-natalie") -> str:
#     """
#     Generate audio using Murf API
    
#     Args:
#         text: Text to convert to speech
#         voice_id: Murf voice ID (default: en-US-natalie)
        
#     Returns:
#         URL to the generated audio file
#     """
#     try:
#         # Murf API endpoint for text-to-speech
#         murf_api_url = "https://api.murf.ai/v1/speech/generate"
        
#         # Prepare request headers
#         headers = {
#             "Authorization": f"Bearer {MURF_API_KEY}",
#             "Content-Type": "application/json"
#         }
        
#         # Prepare request payload according to Murf API documentation
#         payload = {
#             "text": text,
#             "voiceId": voice_id,
#             "format": "mp3",  # Audio format
#             "speed": 1.0,     # Normal speed
#             "pitch": 1.0,     # Normal pitch
#             "volume": 1.0,    # Normal volume
#             "pauseAfter": 0,  # No pause after
#             "encodeAsBase64": False  # Return URL, not base64
#         }
        
#         print(f"🎵 Generating Murf audio with voice: {voice_id}")
#         print(f"   📝 Text length: {len(text)} characters")
        
#         # Make API request to Murf
#         async with httpx.AsyncClient(timeout=30.0) as client:
#             response = await client.post(
#                 murf_api_url,
#                 headers=headers,
#                 json=payload
#             )
        
#         if response.status_code != 200:
#             error_detail = ""
#             try:
#                 error_data = response.json()
#                 error_detail = error_data.get("message", response.text)
#             except:
#                 error_detail = response.text
            
#             raise Exception(f"Murf API error (HTTP {response.status_code}): {error_detail}")
        
#         # Parse response
#         result = response.json()
        
#         # Extract audio URL from response
#         if "audioFile" in result:
#             audio_url = result["audioFile"]
#         elif "url" in result:
#             audio_url = result["url"]
#         elif "audioUrl" in result:
#             audio_url = result["audioUrl"]
#         else:
#             # Fallback - look for any URL-like field in response
#             audio_url = None
#             for key, value in result.items():
#                 if isinstance(value, str) and (value.startswith("http") or "audio" in key.lower()):
#                     audio_url = value
#                     break
            
#             if not audio_url:
#                 raise Exception(f"No audio URL found in Murf API response: {result}")
        
#         print(f"✅ Murf audio generated successfully: {audio_url[:100]}...")
#         return audio_url
        
#     except Exception as e:
#         print(f"❌ Murf API Error: {str(e)}")
#         # Return a fallback TTS option
#         raise Exception(f"Murf audio generation failed: {str(e)}")

# # Enhanced endpoint to get available Murf voices
# @app.get("/murf/voices")
# async def get_murf_voices():
#     """
#     Get list of available Murf voices
    
#     Returns:
#         JSON response with available voices
#     """
#     try:
#         murf_voices_url = "https://api.murf.ai/v1/speech/voices"
        
#         headers = {
#             "Authorization": f"Bearer {MURF_API_KEY}",
#             "Content-Type": "application/json"
#         }
        
#         async with httpx.AsyncClient(timeout=15.0) as client:
#             response = await client.get(murf_voices_url, headers=headers)
        
#         if response.status_code != 200:
#             raise Exception(f"Failed to fetch Murf voices (HTTP {response.status_code})")
        
#         voices_data = response.json()
        
#         return {
#             "status": "success",
#             "voices": voices_data,
#             "count": len(voices_data) if isinstance(voices_data, list) else "unknown"
#         }
        
#     except Exception as e:
#         # Return some default voices as fallback
#         default_voices = [
#             {"voiceId": "en-US-natalie", "name": "Natalie", "language": "en-US", "gender": "female"},
#             {"voiceId": "en-US-marcus", "name": "Marcus", "language": "en-US", "gender": "male"},
#             {"voiceId": "en-US-aria", "name": "Aria", "language": "en-US", "gender": "female"},
#             {"voiceId": "en-US-guy", "name": "Guy", "language": "en-US", "gender": "male"},
#             {"voiceId": "en-GB-sarah", "name": "Sarah", "language": "en-GB", "gender": "female"},
#         ]
        
#         return {
#             "status": "fallback",
#             "message": f"Could not fetch live voices: {str(e)}",
#             "voices": default_voices,
#             "count": len(default_voices)
#         }

# # Your existing TTS endpoint (enhanced)
# @app.post("/generate-audio")
# async def generate_audio(request: dict):
#     """
#     Generate audio from text using TTS service (now with Murf fallback)
#     """
#     try:
#         text = request.get("text", "").strip()
#         voice_id = request.get("voice_id", "en-US-natalie")
        
#         if not text:
#             raise HTTPException(status_code=400, detail="Text field is required and cannot be empty")
        
#         if len(text) > 1000:
#             raise HTTPException(status_code=400, detail="Text is too long. Maximum 1000 characters allowed.")
        
#         print(f"🎵 TTS Request received:")
#         print(f"   📝 Text: {text[:100]}{'...' if len(text) > 100 else ''}")
#         print(f"   🎤 Voice: {voice_id}")
        
#         # Try Murf API first
#         try:
#             murf_audio_url = await generate_murf_audio(text, voice_id)
            
#             return {
#                 "status": "success",
#                 "message": "Audio generated successfully with Murf AI",
#                 "audioFile": murf_audio_url,
#                 "text_length": len(text),
#                 "audio_format": "mp3",
#                 "service": "Murf AI",
#                 "voice_id": voice_id
#             }
            
#         except Exception as murf_error:
#             print(f"⚠️ Murf API failed, trying gTTS fallback: {murf_error}")
            
#             # Fallback to gTTS
#             try:
#                 from gtts import gTTS
#                 import io
#                 import base64
                
#                 tts = gTTS(text=text, lang='en', slow=False)
#                 audio_buffer = io.BytesIO()
#                 tts.write_to_fp(audio_buffer)
#                 audio_buffer.seek(0)
                
#                 audio_data = audio_buffer.read()
#                 audio_b64 = base64.b64encode(audio_data).decode()
#                 audio_url = f"data:audio/mp3;base64,{audio_b64}"
                
#                 return {
#                     "status": "success",
#                     "message": "Audio generated successfully using gTTS (Murf fallback)",
#                     "audioFile": audio_url,
#                     "text_length": len(text),
#                     "audio_format": "mp3",
#                     "service": "gTTS (fallback)"
#                 }
                
#             except ImportError:
#                 return {
#                     "status": "success",
#                     "message": "Use browser's speech synthesis",
#                     "audioFile": None,
#                     "text": text,
#                     "use_browser_tts": True,
#                     "service": "Browser Speech API"
#                 }
            
#     except Exception as e:
#         print(f"❌ TTS Error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

# # Your existing transcription endpoint (kept for compatibility)
# @app.post("/transcribe/file")
# async def transcribe_file(file: UploadFile = File(...)):
#     """
#     Transcribe audio file (existing endpoint)
#     """
#     try:
#         if not file.content_type or not file.content_type.startswith('audio/'):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid file type. Expected audio file, got {file.content_type}"
#             )
        
#         print(f"🎤 Starting transcription for file: {file.filename}")
        
#         with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
#             content = await file.read()
#             temp_file.write(content)
#             temp_file_path = temp_file.name
        
#         try:
#             transcription = await transcribe_with_assemblyai(temp_file_path)
            
#             return {
#                 "status": "success",
#                 "message": "Audio transcribed successfully",
#                 "transcription": transcription,
#                 "confidence": 0.95,  # Placeholder
#                 "audio_duration": 0,  # Placeholder
#                 "words": len(transcription.split()) if transcription else 0,
#                 "service": "AssemblyAI"
#             }
            
#         finally:
#             try:
#                 os.unlink(temp_file_path)
#             except OSError:
#                 pass
        
#     except Exception as e:
#         print(f"❌ Error during transcription: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {str(e)}")

# # Your other existing endpoints...
# @app.post("/upload-audio")
# async def upload_audio(audio: UploadFile = File(...)):
#     """Upload audio file to server"""
#     try:
#         if not audio.content_type.startswith('audio/'):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Invalid file type. Expected audio file, got {audio.content_type}"
#             )
        
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         file_extension = os.path.splitext(audio.filename)[1] or '.webm'
#         unique_filename = f"recording_{timestamp}{file_extension}"
#         file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)
        
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(audio.file, buffer)
        
#         file_stats = os.stat(file_path)
#         file_size = file_stats.st_size
#         content_type = audio.content_type or mimetypes.guess_type(file_path)[0] or 'audio/webm'
        
#         print(f"✅ Audio file uploaded successfully: {unique_filename} ({file_size} bytes)")
        
#         return {
#             "status": "success",
#             "message": "Audio file uploaded successfully",
#             "filename": unique_filename,
#             "original_filename": audio.filename,
#             "size": file_size,
#             "size_formatted": format_file_size(file_size),
#             "content_type": content_type,
#             "upload_path": file_path,
#             "timestamp": timestamp
#         }
        
#     except Exception as e:
#         print(f"❌ Error uploading audio file: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Failed to upload audio file: {str(e)}")

# def format_file_size(size_bytes):
#     """Convert bytes to human readable format"""
#     if size_bytes == 0:
#         return "0 B"
    
#     size_names = ["B", "KB", "MB", "GB", "TB"]
#     import math
#     i = int(math.floor(math.log(size_bytes, 1024)))
#     p = math.pow(1024, i)
#     s = round(size_bytes / p, 2)
#     return f"{s} {size_names[i]}"

# @app.get("/list-uploads")
# async def list_uploads():
#     """List all uploaded audio files"""
#     try:
#         files = []
#         upload_path = Path(UPLOAD_DIRECTORY)
        
#         for file_path in upload_path.glob("*"):
#             if file_path.is_file():
#                 file_stats = file_path.stat()
#                 files.append({
#                     "filename": file_path.name,
#                     "size": file_stats.st_size,
#                     "size_formatted": format_file_size(file_stats.st_size),
#                     "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
#                     "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
#                 })
        
#         return {
#             "status": "success",
#             "count": len(files),
#             "files": files
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

# @app.delete("/delete-upload/{filename}")
# async def delete_upload(filename: str):
#     """Delete a specific uploaded file"""
#     try:
#         file_path = os.path.join(UPLOAD_DIRECTORY, filename)
        
#         if not os.path.exists(file_path):
#             raise HTTPException(status_code=404, detail="File not found")
        
#         if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_DIRECTORY)):
#             raise HTTPException(status_code=400, detail="Invalid file path")
        
#         os.remove(file_path)
        
#         return {
#             "status": "success",
#             "message": f"File {filename} deleted successfully"
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

# # Enhanced health check endpoint
# @app.get("/health")
# async def health_check():
#     """Health check endpoint with API status"""
#     return {
#         "status": "healthy",
#         "message": "AI Voice Agent Server - Echo Bot v2 is running",
#         "version": "2.0.0",
#         "features": ["Echo Bot v2", "AssemblyAI Transcription", "Murf TTS", "File Upload"],
#         "upload_directory": UPLOAD_DIRECTORY,
#         "upload_directory_exists": os.path.exists(UPLOAD_DIRECTORY),
#         "api_keys_configured": {
#             "assemblyai": bool(ASSEMBLYAI_API_KEY and ASSEMBLYAI_API_KEY != "your_assembly_api_key_here"),
#             "murf": bool(MURF_API_KEY and MURF_API_KEY != "your_murf_api_key_here")
#         }
#     }

# if __name__ == "__main__":
#     import uvicorn
    
#     print("🚀 Starting AI Voice Agent Server - Echo Bot v2...")
#     print("📋 New Features:")
#     print("   🎤 Echo Bot v2 with Murf AI voice synthesis")
#     print("   🎵 Enhanced TTS with Murf API integration")
#     print("   🔊 Multiple voice options from Murf")
#     print(f"📁 Upload directory: {os.path.abspath(UPLOAD_DIRECTORY)}")
#     print("🌐 Server will be available at: http://127.0.0.1:8000")
#     print("📋 API Documentation: http://127.0.0.1:8000/docs")
#     print("\n⚠️ Important: Make sure to update your Murf API key in the code!")
    
#     uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

# from fastapi import FastAPI, File, UploadFile, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import os
# import tempfile
# from pathlib import Path
# import assemblyai as aai
# import httpx

# app = FastAPI(title="AI Voice Agent Server - Echo Bot v2", version="2.1.0")

# # Replace with your actual API keys
# ASSEMBLYAI_API_KEY = "1facf73354b34dd68c40b02dd78d40aa"
# MURF_API_KEY = "ap2_65243dd8-74e5-42f7-aacc-c0de2533c137"

# aai.settings.api_key = ASSEMBLYAI_API_KEY

# # CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# UPLOAD_DIRECTORY = "uploads"
# Path(UPLOAD_DIRECTORY).mkdir(exist_ok=True)

# # ---------- Helper Functions ---------- #
# async def transcribe_with_assemblyai(audio_file_path: str) -> str:
#     """Transcribe audio using AssemblyAI"""
#     config = aai.TranscriptionConfig(
#         speaker_labels=False,
#         punctuate=True,
#         format_text=True,
#         language_code="en",
#     )
#     transcriber = aai.Transcriber(config=config)
#     transcript = transcriber.transcribe(audio_file_path)

#     if transcript.status == aai.TranscriptStatus.error:
#         raise Exception(f"AssemblyAI transcription failed: {transcript.error}")

#     return transcript.text or ""


# async def generate_murf_audio(text: str, voice_id: str = "en-US-natalie") -> str:
#     murf_api_url = "https://api.murf.ai/v1/speech/generate"
#     headers = {
#         "api-key": MURF_API_KEY,
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "text": text,
#         "voiceId": voice_id,
#         "format": "mp3",
#         "speed": 1.0,
#         "pitch": 1.0,
#         "volume": 1.0,
#         "pauseAfter": 0,
#         "encodeAsBase64": False
#     }

#     async with httpx.AsyncClient(timeout=30.0) as client:
#         response = await client.post(murf_api_url, headers=headers, json=payload)

#     if response.status_code != 200:
#         raise Exception(f"Murf API error: {response.text}")

#     result = response.json()
#     return result.get("audioFile") or result.get("url") or result.get("audioUrl")




# async def generate_murf_audio(text: str, voice_id: str = "en-US-natalie") -> str:
#     """Generate audio using Murf API"""
#     murf_api_url = "https://api.murf.ai/v1/speech/generate"
#     headers = {
#         "Authorization": f"Bearer {MURF_API_KEY}",
#         "Content-Type": "application/json"
#     }
#     payload = {
#         "text": text,
#         "voiceId": voice_id,
#         "format": "mp3",
#         "speed": 1.0,
#         "pitch": 1.0,
#         "volume": 1.0,
#         "pauseAfter": 0,
#         "encodeAsBase64": False
#     }

#     async with httpx.AsyncClient(timeout=30.0) as client:
#         response = await client.post(murf_api_url, headers=headers, json=payload)

#     if response.status_code != 200:
#         raise Exception(f"Murf API error: {response.text}")

#     result = response.json()
#     # Murf returns `audioFile` field
#     return result.get("audioFile") or result.get("url") or result.get("audioUrl")




# ---------- API Endpoints ---------- #
# @app.post("/tts/echo")
# async def echo_bot_v2(file: UploadFile = File(...), voice_id: str = "en-US-natalie"):
#     """
#     Echo Bot v2: Transcribe audio with AssemblyAI, generate speech with Murf API
#     """
#     if not file.content_type or not file.content_type.startswith("audio/"):
#         raise HTTPException(status_code=400, detail="Invalid file type. Must be audio.")

#     with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
#         temp_file.write(await file.read())
#         temp_path = temp_file.name

#     try:
#         transcription = await transcribe_with_assemblyai(temp_path)
#         if not transcription.strip():
#             raise HTTPException(status_code=400, detail="No speech detected in the audio.")

#         murf_audio_url = await generate_murf_audio(transcription, voice_id)

#         return {
#             "status": "success",
#             "transcription": transcription,
#             "murf_audio_url": murf_audio_url,
#             "voice_id": voice_id
#         }
#     finally:
#         try:
#             os.unlink(temp_path)
#         except:
#             pass


# @app.get("/murf/voices")
# async def get_murf_voices():
#     murf_voices_url = "https://api.murf.ai/v1/speech/voices"
#     headers = {"api-key": MURF_API_KEY}

#     async with httpx.AsyncClient(timeout=15.0) as client:
#         response = await client.get(murf_voices_url, headers=headers)

#     if response.status_code != 200:
#         raise HTTPException(status_code=500, detail="Failed to fetch Murf voices.")

#     return {"voices": response.json()}



# @app.get("/health")
# async def health_check():
#     return {"status": "ok"}



# 
