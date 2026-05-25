import os

from dotenv import load_dotenv

load_dotenv()

# === Gemini Flash 2.5 ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
