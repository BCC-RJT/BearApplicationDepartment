import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key:
    # Try looking in parent dirs
    current_dir = os.path.dirname(os.path.abspath(__file__))
    env_paths = [
        os.path.join(current_dir, '..', '..', '.env'),
        os.path.join(current_dir, '..', '..', '..', '.env')
    ]
    for path in env_paths:
        if os.path.exists(path):
            load_dotenv(path)
            api_key = os.getenv('GOOGLE_API_KEY')
            if api_key: break

if not api_key:
    print("No API Key found.")
    exit(1)

genai.configure(api_key=api_key)

print("Listing models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
