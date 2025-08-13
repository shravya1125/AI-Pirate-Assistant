#!/usr/bin/env python3
"""
Test script to simulate different error scenarios for the robust AI voice agent.
This script helps test the error handling and fallback mechanisms.
"""

import os
import sys
import tempfile
import time
import requests
import json
from pathlib import Path

# Test configuration
SERVER_URL = "http://127.0.0.1:8000"
TEST_SESSION = "test_error_handling"

def test_health_endpoint():
    """Test the health endpoint"""
    print(" Testing health endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.ok:
            data = response.json()
            print("✅ Health check passed")
            print(f"   API Status: {data.get('api_status', {})}")
            print(f"   Error Counts: {data.get('error_counts', {})}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_simulate_errors():
    """Test error simulation endpoints"""
    print("\n🧪 Testing error simulation...")
    
    error_types = [
        "stt_error",
        "llm_error", 
        "tts_error",
        "file_error",
        "network_error",
        "config_error"
    ]
    
    for error_type in error_types:
        print(f"   Testing {error_type}...")
        try:
            response = requests.post(f"{SERVER_URL}/test/simulate-error/{error_type}", timeout=10)
            if response.ok:
                data = response.json()
                print(f"   ✅ {error_type}: {data.get('llm_response', 'No response')}")
            else:
                print(f"   ❌ {error_type}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {error_type}: {e}")

def test_diagnostics():
    """Test diagnostics endpoint"""
    print("\n Testing diagnostics endpoint...")
    try:
        response = requests.get(f"{SERVER_URL}/agent/diagnostics", timeout=5)
        if response.ok:
            data = response.json()
            print("✅ Diagnostics retrieved")
            print(f"   Active sessions: {data.get('system_status', {}).get('total_sessions', 0)}")
            print(f"   Total messages: {data.get('system_status', {}).get('total_messages', 0)}")
            print(f"   Error statistics: {data.get('error_statistics', {})}")
        else:
            print(f"❌ Diagnostics failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Diagnostics error: {e}")

def create_test_audio():
    """Create a minimal test audio file"""
    # Create a simple test audio file (silence)
    test_audio_path = Path("test_audio.webm")
    
    # For testing, we'll create a minimal WebM file
    # In a real scenario, you'd record actual audio
    try:
        # Create a minimal WebM header (this is just for testing)
        with open(test_audio_path, "wb") as f:
            # Minimal WebM file structure
            f.write(b'\x1a\x45\xdf\xa3')  # EBML header
            f.write(b'\x01\x00\x00\x00')  # Version 1
            f.write(b'\x00\x00\x00\x00')  # Empty content
        
        print(f"✅ Created test audio file: {test_audio_path}")
        return test_audio_path
    except Exception as e:
        print(f"❌ Failed to create test audio: {e}")
        return None

def test_chat_endpoint_with_errors():
    """Test the chat endpoint with various error conditions"""
    print("\n🗣️ Testing chat endpoint with error conditions...")
    
    # Test with missing API keys (simulated by commenting them out in main.py)
    print("   Testing with missing API keys...")
    
    test_audio = create_test_audio()
    if not test_audio:
        print("   ❌ Cannot test without audio file")
        return
    
    try:
        with open(test_audio, "rb") as f:
            files = {"file": ("test.webm", f, "audio/webm")}
            data = {"voice_id": "en-US-natalie"}
            
            response = requests.post(
                f"{SERVER_URL}/agent/chat/{TEST_SESSION}",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.ok:
                result = response.json()
                print(f"   ✅ Chat response received")
                print(f"   Success: {result.get('success', False)}")
                print(f"   Fallback used: {result.get('fallback_used', False)}")
                print(f"   Error type: {result.get('error_type', 'None')}")
                print(f"   Response: {result.get('llm_response', 'No response')[:100]}...")
            else:
                print(f"   ❌ Chat request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                    
    except Exception as e:
        print(f"   ❌ Chat test error: {e}")
    finally:
        # Cleanup test file
        if test_audio and test_audio.exists():
            test_audio.unlink()

def main():
    """Run all tests"""
    print("🚀 Starting Robust Error Handling Tests")
    print("=" * 50)
    
    # Test 1: Health endpoint
    if not test_health_endpoint():
        print("❌ Server not responding, exiting tests")
        return
    
    # Test 2: Error simulation
    test_simulate_errors()
    
    # Test 3: Diagnostics
    test_diagnostics()
    
    # Test 4: Chat endpoint with errors
    test_chat_endpoint_with_errors()
    
    print("\n" + "=" * 50)
    print("✅ Error handling tests completed")
    print("\n To test with missing API keys:")
    print("   1. Comment out API key assignments in main.py")
    print("   2. Restart the server")
    print("   3. Run this test script again")
    print("   4. Check that fallback responses are provided")

if __name__ == "__main__":
    main()
