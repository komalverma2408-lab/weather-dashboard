from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pymongo import MongoClient
from datetime import datetime

app = FastAPI()


# =========================================
# CORS
# =========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================
# MONGODB
# =========================================

mongo_client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=5000
)

db = mongo_client["weather_dashboard"]

search_history = db["search_history"]


# =========================================
# HOME
# =========================================

@app.get("/")
def home():

    return {
        "message": "Weather Dashboard Backend is Running!"
    }


# =========================================
# CURRENT WEATHER
# =========================================

@app.get("/weather")
async def get_weather(city: str):

    async with httpx.AsyncClient(timeout=10.0) as client:

        # -------------------------------
        # Find city coordinates
        # -------------------------------

        geo_response = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            }
        )

        geo_response.raise_for_status()

        geo_data = geo_response.json()


        # City not found

        if "results" not in geo_data:

            return {
                "error": "City not found"
            }


        location = geo_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]


        # -------------------------------
        # Get current weather
        # -------------------------------

        weather_response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "wind_speed_10m,"
                    "weather_code"
                ),
                "timezone": "auto"
            }
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()


        # -------------------------------
        # Save search history
        # -------------------------------

        search_history.insert_one({

            "city": location["name"],

            "country": location.get("country"),

            "searched_at": datetime.now()

        })


        # -------------------------------
        # Send response
        # -------------------------------

        return {

            "city": location["name"],

            "country": location.get("country"),

            "temperature":
                weather_data["current"]["temperature_2m"],

            "humidity":
                weather_data["current"]["relative_humidity_2m"],

            "wind_speed":
                weather_data["current"]["wind_speed_10m"],

            "weather_code":
                weather_data["current"]["weather_code"],

            "unit": "°C"

        }


# =========================================
# 5-DAY FORECAST
# =========================================

@app.get("/forecast/{city}")
async def get_forecast(city: str):

    async with httpx.AsyncClient(timeout=10.0) as client:

        # -------------------------------
        # Find city
        # -------------------------------

        location_response = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json"
            }
        )

        location_response.raise_for_status()

        location_data = location_response.json()


        # City not found

        if "results" not in location_data:

            return {
                "error": "City not found"
            }


        location = location_data["results"][0]

        latitude = location["latitude"]
        longitude = location["longitude"]


        # -------------------------------
        # Get 5-day forecast
        # -------------------------------

        forecast_response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": (
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "weather_code"
                ),
                "forecast_days": 5,
                "timezone": "auto"
            }
        )

        forecast_response.raise_for_status()

        forecast_data = forecast_response.json()


        # -------------------------------
        # Send forecast response
        # -------------------------------

        return {

            "city": location["name"],

            "dates":
                forecast_data["daily"]["time"],

            "max_temperature":
                forecast_data["daily"]["temperature_2m_max"],

            "min_temperature":
                forecast_data["daily"]["temperature_2m_min"],

            "weather_code":
                forecast_data["daily"]["weather_code"]

        }


# =========================================
# SEARCH HISTORY
# =========================================

@app.get("/history")
def get_history():

    history = list(

        search_history.find(
            {},
            {"_id": 0}
        )
        .sort("searched_at", -1)
        .limit(10)

    )

    return history