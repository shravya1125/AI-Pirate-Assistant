from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
import mimetypes
import assemblyai as aai
from typing import Optional

app = FastAPI(title="AI Voice Agent Server", version="1.0.0")

ASSEMBLYAI_API_KEY = "1facf73354b34dd68c40b02dd78d40aa"
aai.settings.api_key = ASSEMBLYAI_API_KEY

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIRECTORY = "uploads"
Path(UPLOAD_DIRECTORY).mkdir(exist_ok=True)

# Your TTS endpoint
@app.post("/generate-audio")
async def generate_audio(request: dict):
    """
    Generate audio from text using a TTS service
    
    Args:
        request: Dictionary containing 'text' field
        
    Returns:
        JSON response with audio file URL or data
    """
    try:
        text = request.get("text", "").strip()
        
        if not text:
            raise HTTPException(status_code=400, detail="Text field is required and cannot be empty")
        
        if len(text) > 1000:
            raise HTTPException(status_code=400, detail="Text is too long. Maximum 1000 characters allowed.")
        
        print(f"🎵 TTS Request received:")
        print(f"   📝 Text: {text[:100]}{'...' if len(text) > 100 else ''}")
        print(f"   📏 Length: {len(text)} characters")
        
        # Option 1: Using gTTS (Google Text-to-Speech) - Free option
        try:
            from gtts import gTTS
            import io
            import base64
            
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            # Convert to base64 for embedding
            audio_data = audio_buffer.read()
            audio_b64 = base64.b64encode(audio_data).decode()
            audio_url = f"data:audio/mp3;base64,{audio_b64}"
            
            print("✅ TTS generated successfully using gTTS")
            
            return {
                "status": "success",
                "message": "Audio generated successfully",
                "audioFile": audio_url,
                "text_length": len(text),
                "audio_format": "mp3",
                "service": "gTTS"
            }
            
        except ImportError:
            # Option 2: Using Web Speech API simulation (fallback)
            print("⚠️ gTTS not available, using fallback method")
            
            # Create a simple response for Web Speech API to handle on frontend
            return {
                "status": "success",
                "message": "Use browser's speech synthesis",
                "audioFile": None,
                "text": text,
                "use_browser_tts": True,
                "service": "Browser Speech API"
            }
            
    except Exception as e:
        print(f"❌ TTS Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

# New endpoint for audio transcription
@app.post("/transcribe/file")
async def transcribe_file(file: UploadFile = File(...)):
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Expected audio file, got {file.content_type}"
            )
        
        print(f"     Starting transcription for file: {file.filename}")
        print(f"     Content Type: {file.content_type}")
        print(f"   📏 File Size: {file.size if hasattr(file, 'size') else 'Unknown'} bytes")
        
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            # Read and write the uploaded file content
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Configure transcription settings (using correct AssemblyAI parameters)
            config = aai.TranscriptionConfig(
                # Use correct parameter names for AssemblyAI
                speaker_labels=False,  # Enable speaker diarization if needed
                punctuate=True,        # Correct parameter name for punctuation
                format_text=True,      # Format the text properly
                language_code="en",    # Specify language
            )
            
            # Create transcriber instance
            transcriber = aai.Transcriber(config=config)
            
            print("🔄 Sending audio to AssemblyAI for transcription...")
            
            # Transcribe the audio file
            transcript = transcriber.transcribe(temp_file_path)
            
            # Check if transcription was successful
            if transcript.status == aai.TranscriptStatus.error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Transcription failed: {transcript.error}"
                )
            
            # Extract transcription details
            transcription_text = transcript.text or ""
            confidence = transcript.confidence or 0.0
            audio_duration = transcript.audio_duration or 0
            
            # Count words
            word_count = len(transcription_text.split()) if transcription_text else 0
            
            print(f"✅ Transcription completed successfully:")
            print(f"   📝 Text: {transcription_text[:100]}{'...' if len(transcription_text) > 100 else ''}")
            print(f"   📊 Confidence: {confidence:.2%}")
            print(f"   ⏱️ Duration: {audio_duration}s")
            print(f"   📝 Words: {word_count}")
            
            # Prepare response
            response_data = {
                "status": "success",
                "message": "Audio transcribed successfully",
                "transcription": transcription_text,
                "confidence": confidence,
                "audio_duration": audio_duration,
                "words": word_count,
                "language_detected": getattr(transcript, 'language_code', 'en'),
                "transcript_id": transcript.id,
            }
            
            # Add word-level details if available
            if hasattr(transcript, 'words') and transcript.words:
                response_data['word_details'] = [
                    {
                        "text": word.text,
                        "start": word.start,
                        "end": word.end,
                        "confidence": word.confidence
                    }
                    for word in transcript.words[:50]  # Limit to first 50 words for response size
                ]
            
            return response_data
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
                print(f"🧹 Cleaned up temporary file: {temp_file_path}")
            except OSError as e:
                print(f"⚠️ Warning: Could not delete temporary file {temp_file_path}: {e}")
        
    except Exception as e:
        print(f"❌ Error during transcription: {str(e)}")
        if "API key" in str(e).lower():
            raise HTTPException(
                status_code=500, 
                detail="AssemblyAI API key not configured or invalid. Please check your API key."
            )
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {str(e)}")

# Enhanced upload endpoint (optional - for backward compatibility)
@app.post("/upload-audio")
async def upload_audio(audio: UploadFile = File(...)):
    """
    Upload audio file to server
    
    Args:
        audio: The audio file to upload
        
    Returns:
        JSON response with file details
    """
    try:
        # Validate file type
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Expected audio file, got {audio.content_type}"
            )
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(audio.filename)[1] or '.webm'
        unique_filename = f"recording_{timestamp}{file_extension}"
        
        # Create full file path
        file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # Get file information
        file_stats = os.stat(file_path)
        file_size = file_stats.st_size
        
        # Determine content type
        content_type = audio.content_type or mimetypes.guess_type(file_path)[0] or 'audio/webm'
        
        # Log the upload
        print(f"✅ Audio file uploaded successfully:")
        print(f"   📁 Filename: {unique_filename}")
        print(f"   📊 Size: {file_size} bytes ({file_size / 1024:.2f} KB)")
        print(f"   🎵 Content Type: {content_type}")
        print(f"   📍 Path: {file_path}")
        
        # Return file information
        return {
            "status": "success",
            "message": "Audio file uploaded successfully",
            "filename": unique_filename,
            "original_filename": audio.filename,
            "size": file_size,
            "size_formatted": format_file_size(file_size),
            "content_type": content_type,
            "upload_path": file_path,
            "timestamp": timestamp
        }
        
    except Exception as e:
        print(f"❌ Error uploading audio file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload audio file: {str(e)}")

def format_file_size(size_bytes):
    """
    Convert bytes to human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.23 KB", "2.45 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

# Optional: Endpoint to list uploaded files
@app.get("/list-uploads")
async def list_uploads():
    """
    List all uploaded audio files
    
    Returns:
        JSON response with list of uploaded files
    """
    try:
        files = []
        upload_path = Path(UPLOAD_DIRECTORY)
        
        for file_path in upload_path.glob("*"):
            if file_path.is_file():
                file_stats = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": file_stats.st_size,
                    "size_formatted": format_file_size(file_stats.st_size),
                    "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                })
        
        return {
            "status": "success",
            "count": len(files),
            "files": files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

# Optional: Endpoint to delete uploaded files
@app.delete("/delete-upload/{filename}")
async def delete_upload(filename: str):
    """
    Delete a specific uploaded file
    
    Args:
        filename: Name of the file to delete
        
    Returns:
        JSON response confirming deletion
    """
    try:
        file_path = os.path.join(UPLOAD_DIRECTORY, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check - ensure file is in uploads directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_DIRECTORY)):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        os.remove(file_path)
        
        return {
            "status": "success",
            "message": f"File {filename} deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "AI Voice Agent Server is running",
        "upload_directory": UPLOAD_DIRECTORY,
        "upload_directory_exists": os.path.exists(UPLOAD_DIRECTORY)
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting AI Voice Agent Server...")
    print(f"📁 Upload directory: {os.path.abspath(UPLOAD_DIRECTORY)}")
    print("🌐 Server will be available at: http://127.0.0.1:8000")
    print("📋 API Documentation: http://127.0.0.1:8000/docs")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)