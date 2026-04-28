from dotenv import load_dotenv
import os

# load the .env file
load_dotenv()

# Read the API Key
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    print("API key loaded successfully!")
    # Print the first 10 characters for verification
    print(f"Key starts with: {api_key[:10]}...")
else:
    print("API key NOT found. Check your .env file.")
