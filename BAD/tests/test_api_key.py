import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load env from parent
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(PROJECT_ROOT)
ENV_PATH = os.path.join(REPO_ROOT, '.env')
print(f"Loading env from: {ENV_PATH}")
load_dotenv(ENV_PATH)

KEY = os.getenv('GOOGLE_API_KEY')
print(f"Key loaded: {KEY[:5]}...{KEY[-5:] if KEY else 'None'}")

if not KEY:
    print("❌ No key found.")
    exit(1)

genai.configure(api_key=KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

try:
    response = model.generate_content("Hello! Are you working?")
    print(f"✅ Success! Response: {response.text}")
except Exception as e:
    print(f"❌ Failed: {e}")
