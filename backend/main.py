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

        city_name = location["name"]
        country_name = location.get("country")

        existing_searches = list(
            search_history.find(
                {
                    "city": city_name,
                    "country": country_name
                }
            ).sort("searched_at", -1)
        )


        if existing_searches:

            # Keep the latest entry
            latest_id = existing_searches[0]["_id"]

            search_history.update_one(
                {"_id": latest_id},
                {
                    "$set": {
                        "searched_at": datetime.now()
                    }
                }
            )


            # Remove older duplicate entries
            duplicate_ids = [
                item["_id"]
                for item in existing_searches[1:]
            ]

            if duplicate_ids:

                search_history.delete_many(
                    {
                        "_id": {
                            "$in": duplicate_ids
                        }
                    }
                )

        else:

            search_history.insert_one({

                "city": city_name,

                "country": country_name,

                "searched_at": datetime.now()

            })


        # -------------------------------
        # Send response
        # -------------------------------

        return {

            "city": city_name,

            "country": country_name,

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

    # Get all history so duplicate entries
    # can also be cleaned automatically.

    history = list(

        search_history.find(
            {}
        )
        .sort("searched_at", -1)

    )


    unique_history = []

    seen_cities = set()

    duplicate_ids = []


    for item in history:

        city = item.get("city", "").strip().lower()

        country = (
            item.get("country") or ""
        ).strip().lower()


        city_key = (
            city,
            country
        )


        if city_key in seen_cities:

            duplicate_ids.append(
                item["_id"]
            )

            continue


        seen_cities.add(city_key)


        item.pop("_id", None)

        unique_history.append(item)


    # Remove duplicate database entries

    if duplicate_ids:

        search_history.delete_many(
            {
                "_id": {
                    "$in": duplicate_ids
                }
            }
        )


    # Return only latest 10 unique searches

    return unique_history[:10]


# =========================================
# DELETE ONE SEARCH
# =========================================

@app.delete("/history/{city}")
def delete_history(city: str):

    result = search_history.delete_many(
        {
            "city": city
        }
    )


    return {
        "message": "Search deleted",
        "deleted_count": result.deleted_count
    }


# =========================================
# CLEAR ALL SEARCH HISTORY
# =========================================

@app.delete("/history")
def clear_history():

    result = search_history.delete_many({})


    return {
        "message": "All search history cleared",
        "deleted_count": result.deleted_count
    }