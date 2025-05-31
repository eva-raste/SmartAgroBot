import requests
import config
import re
import string
import os
import speech_recognition as sr
from gtts import gTTS
from deep_translator import GoogleTranslator
from langdetect import detect

# ========== Chatbot API (OpenRouter) ==========

api_url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {config.api_key}",
    "Content-Type": "application/json"
}

messages = [
    {"role": "system", "content": "You are an expert agricultural assistant. Provide a structured, science-based response using Integrated Pest Management (IPM) principles to address this topic. Use clear headings or bullet points. Start with sustainable and eco-friendly approaches such as biological control, cultural practices, and monitoring. Then, include practical and easy-to-follow methods for general users (like neem oil, soap spray, or trap crops). Mention chemical solutions only as a last resort. Keep the explanation simple but accurate, and recommend consulting local agricultural services for region-specific advice.Respond only in English unless asked in other language."}
]

def get_chatbot_response(user_input):
    messages.append({"role": "user", "content": user_input})
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,  # Slightly lower for more focused responses
        "max_tokens": 2000,  # Increased token limit
        "stream": False  # Ensure complete response
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()  # Raises exception for 4XX/5XX errors
        
        result = response.json()
        if "choices" in result:
            reply = result["choices"][0]["message"]["content"]
            messages.append({"role": "assistant", "content": reply})
            return reply.strip()
        return "Sorry, I couldn't generate a proper response. Please try again."
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return "Sorry, I'm having trouble responding right now. Please try again later."
    

def get_weather(city_name):
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_name,
        "appid": config.weather_api_key,
        "units": "metric"
    }

    response = requests.get(base_url, params=params)
    print(f"[DEBUG] Weather API status code: {response.status_code}")
    print(f"[DEBUG] Weather API raw response: {response.text}")

    try:
        data = response.json()
    except Exception as e:
        print("[DEBUG] JSON parse error:", e)
        return "Weather service error."

    if response.status_code == 200:
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        humidity = data['main']['humidity']
        return f"Weather in {city_name.capitalize()}: {temp}°C, {desc}, Humidity: {humidity}%"
    else:
        return "Couldn't fetch weather data. Please check the city name."


# ========== Voice Input ==========

def get_voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Speak now...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Sorry, I could not understand."
    except sr.RequestError as e:
        return f"Speech recognition error: {e}"


# ========== Voice Output ==========

import platform

def speak_text(text):
    try:
        tts = gTTS(text=text, lang='en')  # Change 'en' to 'hi', 'gu', etc. for different languages
        filename = "response.mp3"
        tts.save(filename)

        system_platform = platform.system()
        if system_platform == "Windows":
            os.system(f"start {filename}")
        else:
            print("Unsupported OS. Please play the file manually.")
    except Exception as e:
        print("Voice output error:", e)


# ========== Weather Query Detection ==========

def is_weather_query(user_input):
    keywords = ["weather", "wheather", "rain", "temperature", "forecast", "climate", "humidity"]
    return any(word in user_input.lower() for word in keywords)


def extract_city_from_input(user_input):
    patterns = [
        r'(?:weather|temperature|forecast|rain).*?(?:in|at|for)\s+([A-Za-z\s]+)',  # "rain in Bhuj"
        r'(?:in|at|for)\s+([A-Za-z\s]+?)\s+(?:weather|temperature|forecast|rain)',  # "in Bhuj today"
        r'(?:what is|will there be).*?(?:weather|rain).*?(?:in|at|for)\s+([A-Za-z\s]+)'  # "will it rain in Bhuj"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_input.lower())
        if match:
            city = match.group(1).strip().strip(string.punctuation)
            return city.title()
    
    return None


# ========== Input Handler ==========

from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # Make language detection deterministic

def handle_user_input(user_input):
    try:
        # Detect language only if input is longer than a few words
        if len(user_input.split()) >= 4:
            source_lang = detect(user_input)
        else:
            source_lang = 'en'

        if source_lang != 'en':
            translated_input = GoogleTranslator(source='auto', target='en').translate(user_input)
        else:
            translated_input = user_input

        if is_weather_query(translated_input):
            city = extract_city_from_input(translated_input)
            if city:
                weather_response = get_weather(city)
                if "Couldn't fetch" not in weather_response:
                    advice_prompt = f"Based on this weather: {weather_response}, provide brief farming advice."
                    english_advice = get_chatbot_response(advice_prompt)
                    combined_response = f"{weather_response}\n\nFarming advice: {english_advice}"
                else:
                    combined_response = weather_response
            else:
                combined_response = get_chatbot_response(translated_input)
        else:
            combined_response = get_chatbot_response(translated_input)

        return translate_back(combined_response, source_lang)

    except Exception as e:
        print("[ERROR] Multilingual handling failed:", e)
        return "An error occurred while processing your message. Please try again."



def translate_back(text, target_lang):
    if target_lang != 'en':
        try:
            # Split long text into chunks for translation
            max_chunk_size = 5000  # Google Translate limit
            chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
            translated_chunks = []
            
            for chunk in chunks:
                translated = GoogleTranslator(
                    source='en', 
                    target=target_lang,
                    timeout=10
                ).translate(chunk)
                translated_chunks.append(translated)
                
            return ' '.join(translated_chunks)
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    return text


