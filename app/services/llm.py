import os
from dotenv import load_dotenv
import google.generativeai as genai


# Load environment variables from .env
load_dotenv()

api_key=os.getenv("GEMINI_API_KEY")
# Configure Gemini API
genai.configure(
    api_key=api_key
)


# Load Gemini model
model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

print(api_key)

def generate_answer(prompt: str):

    response = model.generate_content(prompt)

    return response.text