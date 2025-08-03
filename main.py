from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()
MURF_API_KEY = os.getenv("MURF_API_KEY")

app = FastAPI()

# Input model
class TextInput(BaseModel):
    text: str

# POST endpoint to generate audio
@app.post("/generate-audio")
def generate_audio(input_data: TextInput, voice_id: str = Query(default="en-AU-kylie")):
    if not MURF_API_KEY:
        raise HTTPException(status_code=500, detail="Missing Murf API Key")

    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }


    payload = {
        "text": input_data.text,
        "voice_id": voice_id
    }

    murf_url = "https://api.murf.ai/v1/speech/generate"
    response = requests.post(murf_url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)



# from fastapi import FastAPI, HTTPException, Request
# from pydantic import BaseModel
# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()  # Load .env file

# MURF_API_KEY = os.getenv("MURF_API_KEY")
# MURF_API_URL = "https://api.murf.ai/v1/speech/generate"

# app = FastAPI()

# class TextInput(BaseModel):
#     text: str

# @app.post("/generate-audio")
# def generate_audio(input_data: TextInput):
#     headers = {
#     "api-key": MURF_API_KEY,
#     "Content-Type": "application/json"
#    }


#     payload = {
#         "text": input_data.text,
#         "voice_id": "en-UK-theo"  # Replace with your preferred voice ID from Murf
#     }

#     response = requests.post(MURF_API_URL, json=payload, headers=headers)

#     if response.status_code == 200:
#         data = response.json()
#         return {"audio_url": data.get("audio_url")}
#     else:
#         raise HTTPException(status_code=response.status_code, detail=response.text)


# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# import requests
# import os
# from dotenv import load_dotenv
# import asyncio
# from typing import Optional

# # Load environment variables
# load_dotenv()

# app = FastAPI(
#     title="TTS API Server",
#     description="A FastAPI server that converts text to speech using Murf's REST API",
#     version="1.0.0"
# )

# class TTSRequest(BaseModel):
#     text: str
#     voiceId: Optional[str] = "en-US-sarah"  # Changed from voice_id to voiceId
#     speed: Optional[float] = 1.0
#     pitch: Optional[float] = 1.0
#     audioFormat: Optional[str] = "MP3"  # Added audioFormat
#     model: Optional[str] = "GEN2"  # Added model parameter
#     sampleRate: Optional[int] = 44100  # Added sampleRate

# class TTSResponse(BaseModel):
#     success: bool
#     audio_url: Optional[str] = None
#     message: str
#     job_id: Optional[str] = None

# @app.get("/")
# async def root():
#     """Root endpoint with API information"""
#     return {
#         "message": "TTS API Server is running",
#         "docs": "/docs",
#         "endpoints": {
#             "generate_speech": "/generate-speech",
#             "health": "/health"
#         }
#     }

# @app.get("/health")
# async def health_check():
#     """Health check endpoint"""
#     return {"status": "healthy", "service": "TTS API Server"}

# @app.post("/generate-speech", response_model=TTSResponse)
# async def generate_speech(request: TTSRequest):
#     """
#     Generate speech from text using Murf's TTS API
    
#     Args:
#         request: TTSRequest containing text and voice parameters
        
#     Returns:
#         TTSResponse with audio URL or error message
#     """
    
#     # Get API key from environment variables
#     murf_api_key = os.getenv("MURF_API_KEY")
#     if not murf_api_key:
#         raise HTTPException(
#             status_code=500, 
#             detail="MURF_API_KEY not found in environment variables"
#         )
    
#     # Murf API endpoint - corrected URL
#     murf_api_url = "https://api.murf.ai/v1/speech/generate"
    
#     # Prepare headers
#     headers = {
#         "Authorization": f"Bearer {murf_api_key}",
#         "Content-Type": "application/json",
#         "Accept": "application/json"
#     }
    
#     # Prepare payload for Murf API - corrected structure
#     payload = {
#         "text": request.text,
#         "voiceId": request.voiceId,  # Changed from voice_id to voiceId
#         "speed": request.speed,
#         "pitch": request.pitch,
#         "audioFormat": request.audioFormat,  # Use audioFormat instead of format
#         "model": request.model,
#         "sampleRate": request.sampleRate
#     }
    
#     try:
#         # Make request to Murf API using requests (synchronous)
#         response = requests.post(
#             murf_api_url,
#             json=payload,
#             headers=headers,
#             timeout=30.0
#         )
            
#         if response.status_code == 200:
#             result = response.json()
            
#             # Murf API returns audio URL in 'audioFile' field
#             if "audioFile" in result:
#                 return TTSResponse(
#                     success=True,
#                     audio_url=result["audioFile"],
#                     message="Speech generated successfully"
#                 )
#             else:
#                 # Return the full response for debugging
#                 return TTSResponse(
#                     success=False,
#                     message=f"Unexpected response format: {result}"
#                 )
        
#         elif response.status_code == 401:
#             raise HTTPException(
#                 status_code=401,
#                 detail="Invalid API key. Please check your MURF_API_KEY."
#             )
        
#         elif response.status_code == 429:
#             raise HTTPException(
#                 status_code=429,
#                 detail="Rate limit exceeded. Please try again later."
#             )
        
#         else:
#             # Enhanced error logging
#             error_detail = f"Murf API returned {response.status_code}"
#             try:
#                 error_data = response.json()
#                 error_detail += f": {error_data}"
#             except:
#                 error_detail += f": {response.text}"
            
#             # Log the full request for debugging (without API key)
#             debug_payload = payload.copy()
#             print(f"Request payload: {debug_payload}")
#             print(f"Response: {error_detail}")
            
#             raise HTTPException(
#                 status_code=response.status_code, 
#                 detail=f"Murf API error: {response.status_code} - {error_detail}"
#             )
            
#     except requests.exceptions.Timeout:
#         raise HTTPException(
#             status_code=504,
#             detail="Request to Murf API timed out"
#         )
#     except requests.exceptions.RequestException as e:
#         raise HTTPException(
#             status_code=503,
#             detail=f"Error connecting to Murf API: {str(e)}"
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal server error: {str(e)}"
#         )

# @app.get("/check-job/{job_id}")
# async def check_job_status(job_id: str):
#     """
#     Check the status of a TTS generation job (if Murf uses async processing)
    
#     Args:
#         job_id: The job ID returned from generate-speech endpoint
        
#     Returns:
#         Job status and audio URL when ready
#     """
#     murf_api_key = os.getenv("MURF_API_KEY")
#     if not murf_api_key:
#         raise HTTPException(
#             status_code=500,
#             detail="MURF_API_KEY not found in environment variables"
#         )
    
#     headers = {
#         "Authorization": f"Bearer {murf_api_key}",
#         "Accept": "application/json"
#     }
    
#     try:
#         response = requests.get(
#             f"https://api.murf.ai/v1/speech/jobs/{job_id}",
#             headers=headers,
#             timeout=10.0
#         )
        
#         if response.status_code == 200:
#             return response.json()
#         else:
#             raise HTTPException(
#                 status_code=response.status_code,
#                 detail=f"Error checking job status: {response.text}"
#             )
                
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error checking job status: {str(e)}"
#         )

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)