import os

# Fetch API keys from environment variables
api_key = os.getenv("OPENROUTER_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")

# Optional: fallback values (ONLY for local testing; NOT recommended in production)
if api_key is None:
    print("⚠️ OPENROUTER_API_KEY not set in environment")
if weather_api_key is None:
    print("⚠️ WEATHER_API_KEY not set in environment")
