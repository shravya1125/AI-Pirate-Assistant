# Robust Error Handling Guide

This guide explains the comprehensive error handling and fallback mechanisms implemented in the AI Voice Agent application.

## 🛡️ Error Handling Overview

The application now includes robust error handling for all major components:

- **Speech-to-Text (STT)** - AssemblyAI API failures
- **Language Model (LLM)** - Gemini API failures  
- **Text-to-Speech (TTS)** - Murf API failures
- **Network connectivity** - Timeout and connection issues
- **File processing** - Audio file validation and processing errors

## 🔧 Key Features

### 1. Comprehensive Error Categories

```python
class ErrorType(Enum):
    STT_ERROR = "stt_error"        # Speech recognition failures
    LLM_ERROR = "llm_error"        # AI processing failures
    TTS_ERROR = "tts_error"        # Voice generation failures
    FILE_ERROR = "file_error"      # Audio file issues
    NETWORK_ERROR = "network_error" # Connection problems
    CONFIG_ERROR = "config_error"  # Missing API keys
```

### 2. Fallback Responses

Each error type has a specific fallback response:

- **STT Error**: "I'm sorry, I'm having trouble understanding your audio right now. Could you please try speaking again?"
- **LLM Error**: "I'm experiencing some technical difficulties processing your request. Please try again in a moment."
- **TTS Error**: "I understood your request but I'm having trouble generating audio. Here's my text response."
- **Network Error**: "I'm having trouble connecting to my services right now. Please check your connection and try again."
- **Config Error**: "The service is temporarily unavailable due to configuration issues. Please try again later."

### 3. Multiple TTS Fallback Strategies

The TTS system implements a multi-layered fallback approach:

1. **Primary**: Murf API with multiple header/payload combinations
2. **Fallback**: gTTS (Google Text-to-Speech) for local generation
3. **Final**: Text-only response with "TEXT_ONLY:" prefix

### 4. Client-Side Error Handling

The frontend includes:

- **Timeout handling** (60-second request timeout)
- **Specific error type detection** and display
- **Retry functionality** with stored audio blob
- **Health monitoring** with API status checking
- **User-friendly error messages** with recovery suggestions

## 🧪 Testing Error Scenarios

### Using the Test Scripts

#### 1. Error Simulation Tool

```bash
# Create backup of main.py
python simulate_failures.py backup

# Simulate specific API failures
python simulate_failures.py fail assemblyai  # Speech recognition failure
python simulate_failures.py fail gemini      # AI processing failure  
python simulate_failures.py fail murf        # Voice generation failure
python simulate_failures.py fail all         # All APIs fail

# Check current status
python simulate_failures.py status

# Restore original configuration
python simulate_failures.py restore
```

#### 2. Comprehensive Test Suite

```bash
# Run all error handling tests
python test_errors.py
```

This will test:
- Health endpoint functionality
- Error simulation endpoints
- Diagnostics and monitoring
- Chat endpoint with various error conditions

### Manual Testing Steps

1. **Start the server** with normal configuration
2. **Test normal operation** to ensure everything works
3. **Simulate API failures** using the simulation tool
4. **Restart the server** to apply changes
5. **Test error handling** by making requests
6. **Verify fallback responses** are provided
7. **Check client-side error display** and retry functionality

## 📊 Monitoring and Diagnostics

### Health Endpoint

```bash
curl http://127.0.0.1:8000/health
```

Returns:
```json
{
  "status": "ok",
  "message": "Robust AI Voice Agent server is running",
  "api_status": {
    "assemblyai": true,
    "gemini": true, 
    "murf": true,
    "gtts_fallback": true
  },
  "error_counts": {
    "stt_error": 0,
    "llm_error": 0,
    "tts_error": 0,
    "file_error": 0,
    "network_error": 0,
    "config_error": 0
  }
}
```

### Diagnostics Endpoint

```bash
curl http://127.0.0.1:8000/agent/diagnostics
```

Provides detailed system statistics including:
- Active sessions and message counts
- API configuration status
- Error statistics
- Session activity tracking

## 🎯 Error Recovery Strategies

### 1. Automatic Recovery

- **Network timeouts**: Automatic retry with exponential backoff
- **API rate limits**: Graceful degradation to fallback services
- **Temporary failures**: Multiple retry attempts with different configurations

### 2. User-Initiated Recovery

- **Retry button**: Users can retry failed requests with the same audio
- **Clear error state**: Automatic reset after error display
- **Health monitoring**: Real-time status updates

### 3. Graceful Degradation

- **Partial failures**: Continue processing with available services
- **Fallback responses**: Always provide some form of response
- **Error tracking**: Monitor and log all failures for analysis

## 🔍 Error Detection and Logging

### Server-Side Logging

All errors are logged with:
- Error type and category
- Session ID for tracking
- Detailed error message
- Timestamp and context

### Client-Side Monitoring

- Real-time health checks every 30 seconds
- API status monitoring
- Connection timeout detection
- User-friendly error display

## 🚀 Best Practices

### For Development

1. **Test error scenarios** regularly using the provided tools
2. **Monitor error statistics** through the diagnostics endpoint
3. **Update fallback responses** based on user feedback
4. **Add new error types** as needed for specific scenarios

### For Production

1. **Set up monitoring** for error rates and types
2. **Configure alerts** for critical service failures
3. **Regular health checks** to ensure fallback services work
4. **User communication** about service status and expected behavior

## 🔧 Configuration

### Environment Variables

The system gracefully handles missing API keys:

```bash
# Required (will use fallbacks if missing)
ASSEMBLYAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here  
MURF_API_KEY=your_key_here

# Optional
FFMPEG_PATH=/path/to/ffmpeg
```

### Fallback Configuration

- **gTTS**: Automatically installed and used as TTS fallback
- **Error responses**: Customizable fallback messages
- **Timeout values**: Configurable request timeouts

## 📈 Performance Impact

The error handling adds minimal overhead:

- **Request timeouts**: 60 seconds maximum
- **Health checks**: 5-second timeout, every 30 seconds
- **Fallback generation**: Typically 1-3 seconds
- **Error tracking**: In-memory with minimal impact

##  Success Metrics

A robust system should achieve:

- **99%+ uptime** even with API failures
- **<5 second** fallback response time
- **<1%** complete request failures
- **User satisfaction** maintained during outages

## 🔮 Future Enhancements

Potential improvements:

1. **Persistent error tracking** with database storage
2. **Advanced retry logic** with exponential backoff
3. **Service health dashboards** for monitoring
4. **Automated failover** between multiple service providers
5. **Predictive error detection** using historical data

---

This robust error handling system ensures the AI Voice Agent remains functional and user-friendly even when external services are unavailable or experiencing issues.
