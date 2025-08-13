#!/usr/bin/env python3
"""
Script to simulate API failures by temporarily commenting out API keys in main.py
This helps test the robust error handling and fallback mechanisms.
"""

import os
import sys
import shutil
from pathlib import Path

def backup_main_py():
    """Create a backup of main.py"""
    main_py = Path("main.py")
    backup_py = Path("main.py.backup")
    
    if main_py.exists():
        shutil.copy2(main_py, backup_py)
        print("✅ Created backup: main.py.backup")
        return True
    else:
        print("❌ main.py not found")
        return False

def restore_main_py():
    """Restore main.py from backup"""
    main_py = Path("main.py")
    backup_py = Path("main.py.backup")
    
    if backup_py.exists():
        shutil.copy2(backup_py, main_py)
        print("✅ Restored main.py from backup")
        return True
    else:
        print("❌ Backup file not found")
        return False

def simulate_api_failure(api_name):
    """Simulate failure of a specific API by commenting out its key"""
    main_py = Path("main.py")
    
    if not main_py.exists():
        print("❌ main.py not found")
        return False
    
    # Read the file
    with open(main_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the API key patterns to comment out
    api_patterns = {
        'assemblyai': 'ASSEMBLYAI_API_KEY = safe_env_get("ASSEMBLYAI_API_KEY", required=True)',
        'gemini': 'GEMINI_API_KEY = safe_env_get("GEMINI_API_KEY", required=True)',
        'murf': 'MURF_API_KEY = safe_env_get("MURF_API_KEY", required=True)',
        'all': None  # Special case for all APIs
    }
    
    if api_name not in api_patterns:
        print(f"❌ Unknown API: {api_name}")
        print(f"   Available: {', '.join(api_patterns.keys())}")
        return False
    
    # Comment out the specified API key(s)
    if api_name == 'all':
        # Comment out all API keys
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if any(pattern in line for pattern in [
                'ASSEMBLYAI_API_KEY = safe_env_get',
                'GEMINI_API_KEY = safe_env_get', 
                'MURF_API_KEY = safe_env_get'
            ]):
                new_lines.append(f"# {line}  # SIMULATED FAILURE")
            else:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
        print("✅ Commented out all API keys")
        
    else:
        # Comment out specific API key
        pattern = api_patterns[api_name]
        if pattern in content:
            content = content.replace(pattern, f"# {pattern}  # SIMULATED FAILURE")
            print(f"✅ Commented out {api_name} API key")
        else:
            print(f"❌ Could not find {api_name} API key pattern")
            return False
    
    # Write the modified content back
    with open(main_py, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def show_status():
    """Show current status of API keys in main.py"""
    main_py = Path("main.py")
    
    if not main_py.exists():
        print("❌ main.py not found")
        return
    
    with open(main_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(" Current API Key Status:")
    
    apis = [
        ('AssemblyAI', 'ASSEMBLYAI_API_KEY = safe_env_get'),
        ('Gemini', 'GEMINI_API_KEY = safe_env_get'),
        ('Murf', 'MURF_API_KEY = safe_env_get')
    ]
    
    for name, pattern in apis:
        if pattern in content:
            if f"# {pattern}" in content:
                print(f"   {name}: ❌ COMMENTED OUT (simulated failure)")
            else:
                print(f"   {name}: ✅ ACTIVE")
        else:
            print(f"   {name}: ❓ NOT FOUND")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🔧 API Failure Simulation Tool")
        print("=" * 40)
        print("Usage:")
        print("  python simulate_failures.py backup")
        print("  python simulate_failures.py restore") 
        print("  python simulate_failures.py fail <api_name>")
        print("  python simulate_failures.py status")
        print("")
        print("API names: assemblyai, gemini, murf, all")
        print("")
        print("Examples:")
        print("  python simulate_failures.py backup")
        print("  python simulate_failures.py fail assemblyai")
        print("  python simulate_failures.py fail all")
        print("  python simulate_failures.py restore")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'backup':
        backup_main_py()
        
    elif command == 'restore':
        restore_main_py()
        
    elif command == 'fail':
        if len(sys.argv) < 3:
            print("❌ Please specify which API to fail")
            print("   Options: assemblyai, gemini, murf, all")
            return
        
        api_name = sys.argv[2].lower()
        simulate_api_failure(api_name)
        
    elif command == 'status':
        show_status()
        
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
