from flask import Flask, render_template, jsonify, request
import requests
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Using Open-Meteo API (completely free, no API key needed)
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

def get_city_coordinates(city_name):
    """Get latitude and longitude for a city using Open-Meteo Geocoding API"""
    try:
        response = requests.get(f"{GEOCODING_URL}?name={city_name}&count=1&language=en&format=json")
        data = response.json()
        
        if 'results' in data and len(data['results']) > 0:
            result = data['results'][0]
            return {
                'lat': result['latitude'],
                'lon': result['longitude'],
                'name': result['name'],
                'country': result.get('country', ''),
                'admin1': result.get('admin1', '')
            }
        return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None

def get_weather_description(weather_code):
    """Convert weather code to description"""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        56: "Light freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        66: "Light freezing rain", 67: "Heavy freezing rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        85: "Slight snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(weather_code, "Unknown")

def get_weather_icon(weather_code, is_day=True):
    """Get weather icon based on weather code"""
    day_icons = {
        0: "01d", 1: "02d", 2: "03d", 3: "04d",
        45: "50d", 48: "50d",
        51: "09d", 53: "09d", 55: "09d", 56: "09d", 57: "09d",
        61: "10d", 63: "10d", 65: "10d", 66: "10d", 67: "10d",
        71: "13d", 73: "13d", 75: "13d", 77: "13d",
        80: "09d", 81: "09d", 82: "09d",
        85: "13d", 86: "13d",
        95: "11d", 96: "11d", 99: "11d"
    }
    
    night_icons = {
        0: "01n", 1: "02n", 2: "03n", 3: "04n",
        45: "50n", 48: "50n",
        51: "09n", 53: "09n", 55: "09n", 56: "09n", 57: "09n",
        61: "10n", 63: "10n", 65: "10n", 66: "10n", 67: "10n",
        71: "13n", 73: "13n", 75: "13n", 77: "13n",
        80: "09n", 81: "09n", 82: "09n",
        85: "13n", 86: "13n",
        95: "11n", 96: "11n", 99: "11n"
    }
    
    icons = day_icons if is_day else night_icons
    return icons.get(weather_code, "01d")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather/<city>')
def get_weather(city):
    try:
        # Get city coordinates
        location = get_city_coordinates(city)
        if not location:
            return jsonify({"error": "City not found"}), 404
        
        # Get weather data from Open-Meteo
        params = {
            'latitude': location['lat'],
            'longitude': location['lon'],
            'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m',
            'daily': 'weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset',
            'timezone': 'auto',
            'forecast_days': 7
        }
        
        response = requests.get(WEATHER_URL, params=params)
        weather_data = response.json()
        
        if response.status_code != 200:
            return jsonify({"error": "Weather data not available"}), 404
        
        current = weather_data['current']
        daily = weather_data['daily']
        
        # Process current weather
        current_weather = {
            'city': location['name'],
            'country': location['country'],
            'temperature': round(current['temperature_2m']),
            'feels_like': round(current['apparent_temperature']),
            'description': get_weather_description(current['weather_code']),
            'icon': get_weather_icon(current['weather_code'], current['is_day']),
            'humidity': current['relative_humidity_2m'],
            'pressure': round(current['surface_pressure']),
            'wind_speed': round(current['wind_speed_10m'], 1),
            'wind_deg': current['wind_direction_10m'],
            'visibility': 10,  # Default visibility
            'sunrise': datetime.fromisoformat(daily['sunrise'][0]).strftime('%H:%M'),
            'sunset': datetime.fromisoformat(daily['sunset'][0]).strftime('%H:%M'),
        }
        
        # Process 5-day forecast
        forecast = []
        for i in range(1, 6):  # Skip today, get next 5 days
            date = datetime.fromisoformat(daily['time'][i])
            forecast.append({
                'date': date.strftime('%a, %b %d'),
                'temp_max': round(daily['temperature_2m_max'][i]),
                'temp_min': round(daily['temperature_2m_min'][i]),
                'description': get_weather_description(daily['weather_code'][i]),
                'icon': get_weather_icon(daily['weather_code'][i], True)
            })
        
        current_weather['forecast'] = forecast
        return jsonify(current_weather)
    
    except Exception as e:
        print(f"Weather error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/search-suggestions/<query>')
def search_suggestions(query):
    try:
        # Use Open-Meteo geocoding for real city suggestions
        response = requests.get(f"{GEOCODING_URL}?name={query}&count=5&language=en&format=json")
        data = response.json()
        
        suggestions = []
        if 'results' in data:
            for result in data['results']:
                city_name = result['name']
                country = result.get('country', '')
                admin1 = result.get('admin1', '')
                
                # Format: "City, State, Country" or "City, Country"
                display_name = city_name
                if admin1 and admin1 != city_name:
                    display_name += f", {admin1}"
                if country:
                    display_name += f", {country}"
                
                suggestions.append(display_name)
        
        return jsonify(suggestions[:5])
    except Exception as e:
        # Fallback to mock cities if API fails
        cities = [
            "New York", "London", "Tokyo", "Paris", "Sydney", "Mumbai", "Berlin", 
            "Toronto", "Dubai", "Singapore", "Barcelona", "Amsterdam", "Rome", 
            "Cairo", "Bangkok", "Seoul", "Moscow", "Istanbul", "Rio de Janeiro", 
            "Cape Town", "Buenos Aires", "Mexico City", "Los Angeles", "Chicago"
        ]
        suggestions = [city for city in cities if query.lower() in city.lower()][:5]
        return jsonify(suggestions)

if __name__ == '__main__':
    app.run(debug=True)



