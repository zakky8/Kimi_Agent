
import os
import requests
import json
from app.config import settings

# Candidate models to test
CANDIDATE_MODELS = [
    "nvidia/llama-3.1-nemotron-70b-instruct:free",
    "nvidia/llama-3.1-nemotron-70b-instruct",
    "nvidia/nemotron-4-340b-instruct",
    "nvidia/nemotron-4-340b-reward",
    "nvidia/nemotron-3-8b-chat", 
    "mistralai/mistral-7b-instruct:free", # Fallback control
]

API_KEY = settings.OPENROUTER_API_KEY_NEMOTRON or settings.OPENROUTER_API_KEY
print(f"Testing with API Key: {API_KEY[:10]}...{API_KEY[-4:] if API_KEY else 'None'}")

if not API_KEY:
    print("Error: No API Key found in settings.")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "HTTP-Referer": "http://localhost:3000",
    "X-Title": "AI Trading Agent Pro Test",
    "Content-Type": "application/json"
}

def test_model(model_id):
    print(f"\nTesting model: {model_id}...")
    url = "https://openrouter.ai/api/v1/chat/completions"
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Hello, are you online?"}],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        if response.status_code == 200:
            print(f"✅ SUCCESS: {model_id} is working!")
            print(f"Response: {response.json()['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ FAILED: {model_id} -> Status: {response.status_code}")
            try:
                print(f"Error: {response.json()}")
            except:
                print(f"Raw: {response.text}")
            return False
            
    except Exception as e:
        print(f"⚠️ EXCEPTION: {e}")
        return False

# Run tests
found_working = False
for model in CANDIDATE_MODELS:
    if test_model(model):
        found_working = True
        print(f"\n✨ RECOMMENDATION: Update config to use '{model}'")
        break # Stop after finding the first working one

if not found_working:
    print("\n❌ No working Nemotron models found. Try a different provider or check API key permissions.")
