import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY not set.")
else:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    try:
        print("Listing models...")
        for m in client.models.list(config={"page_size": 100}):
            print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
