import requests
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather_risk(city="Kozhikode"):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }
    response = requests.get(url, params=params).json()

    if "weather" not in response:
        print("❌ API Error:", response)
        return {"weather_risk": 0.1, "description": "unknown", "temperature": 0, "humidity": 0}

    weather_id = response["weather"][0]["id"]
    description = response["weather"][0]["description"]
    temp = response["main"]["temp"]
    humidity = response["main"]["humidity"]

    if weather_id < 300:
        W_weather = 1.0      # Thunderstorm
    elif weather_id < 600:
        W_weather = 0.7      # Rain / Drizzle
    elif weather_id < 700:
        W_weather = 0.8      # Snow
    elif weather_id < 800:
        W_weather = 0.5      # Fog / Mist / Haze
    else:
        W_weather = 0.1      # Clear / Clouds

    return {
        "weather_risk": W_weather,
        "description": description,
        "temperature": temp,
        "humidity": humidity
    }

if __name__ == "__main__":
    print("API KEY loaded:", API_KEY)
    result = get_weather_risk("Kozhikode")
    print("Result:", result)