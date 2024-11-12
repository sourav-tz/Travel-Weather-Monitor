import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import os

app = Flask(__name__)

API_KEY = open('api_key', 'r').read().strip()
BASE_URL_CURRENT = 'http://api.openweathermap.org/data/2.5/weather'
BASE_URL_FORECAST = 'http://api.openweathermap.org/data/2.5/forecast'
BASE_URL_AQI = 'http://api.openweathermap.org/data/2.5/air_pollution'

# Mapping of weather conditions to corresponding icon files
condition_icons = {
    "Clear": "clear.png",
    "Clouds": "clouds.png",
    "Rain": "rain.png",
    "Drizzle": "drizzle.png",
    "Thunderstorm": "thunderstorm.png",
    "Snow": "snow.png",
    "Mist": "mist.png",
    "Smoke": "smoke.png",
    "Haze": "haze.png",
    "Fog": "fog.png",
    "Sand": "sand.png",
    "Dust": "dust.png",
    "Ash": "ash.png",
    "Squalls": "squalls.png",
    "Tornado": "tornado.png"
}

def get_icon_for_condition(condition):
    for key in condition_icons:
        if key.lower() in condition.lower():
            return f"/static/icons/{condition_icons[key]}"
    return "/static/icons/default.png"  

def get_aqi_color(aqi_level):
    if aqi_level == "Good":
        return "#00E400"  # Bright Green
    elif aqi_level == "Fair":
        return "#9ACD32"  # Yellow-Green
    elif aqi_level == "Moderate":
        return "#FFBF00"  # Amber Yellow
    elif aqi_level == "Poor":
        return "#FF4500"  # Orange-Red
    elif aqi_level == "Very Poor":
        return "#B22222"  # Firebrick Red
    return "#A9A9A9"  # Dark Gray (for unknown or unspecified AQI levels)


def get_aqi_description(aqi):
    """Convert AQI index to a descriptive label."""
    if aqi == 1:
        return "Good"
    elif aqi == 2:
        return "Fair"
    elif aqi == 3:
        return "Moderate"
    elif aqi == 4:
        return "Poor"
    elif aqi == 5:
        return "Very Poor"
    return "Unknown"

def get_air_quality(lat, lon):
    """Fetch AQI data based on latitude and longitude."""
    params = {
        'lat': lat,
        'lon': lon,
        'appid': API_KEY
    }
    response = requests.get(BASE_URL_AQI, params=params)
    aqi_data = response.json()
    if aqi_data.get("list"):
        aqi_value = aqi_data["list"][0]["main"]["aqi"]
        return get_aqi_description(aqi_value)
    return None

def get_weather_data(city_name):
    current_weather_params = {
        'q': city_name,
        'appid': API_KEY,
        'units': 'metric'
    }
    response_current = requests.get(BASE_URL_CURRENT, params=current_weather_params)
    current_data = response_current.json()
    
    forecast_params = {
        'q': city_name,
        'appid': API_KEY,
        'units': 'metric'
    }
    response_forecast = requests.get(BASE_URL_FORECAST, params=forecast_params)
    forecast_data = response_forecast.json()

    if current_data.get("coord"):
        lat = current_data["coord"]["lat"]
        lon = current_data["coord"]["lon"]
        aqi = get_air_quality(lat, lon)
        current_data["aqi_description"] = aqi
    else:
        current_data["aqi_description"] = None
    
    return current_data, forecast_data

def plot_forecast(forecast_data, city_name):
    dates = []
    temperatures = []
    
    for item in forecast_data['list']:
        date = datetime.fromtimestamp(item['dt'])
        temp = item['main']['temp']
        dates.append(date)
        temperatures.append(temp)
    
    plt.figure(figsize=(10, 5))
    plt.plot(dates, temperatures, marker='o', linestyle='-', color='b')
    plt.title(f"5-Day Temperature Forecast for {(city_name).title()}")
    plt.xlabel("Date")
    plt.ylabel("Temperature (°C)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plot_path = os.path.join('static', f'plot_{city_name}.png')
    plt.savefig(plot_path)
    plt.close()
    return plot_path

@app.route("/", methods=["GET", "POST"])
def index():
    weather_data = []
    
    if request.method == "POST":
        cities = request.form.get("city").split(",")
        
        for city in cities:
            current_data, forecast_data = get_weather_data(city.strip())
            
            if current_data.get("cod") != 200:
                weather_data.append(({"error": current_data.get("message", "City not found. Please provide a correct name and try again!")}, None))
            else:
                condition = current_data['weather'][0]['description'].title()
                icon_path = get_icon_for_condition(condition)
                
                weather_info = {
                    "city": city.strip().title(),
                    "temperature": round(current_data['main']['temp']),
                    "feels_like": round(current_data['main']['feels_like']),
                    "condition": condition,
                    "country": current_data['sys']['country'],
                    "humidity": current_data['main']['humidity'],
                    "visibility": current_data['visibility'],
                    "wind_speed": current_data['wind']['speed'],
                    "aqi_description": current_data.get("aqi_description"),
                    "aqi_color": get_aqi_color(current_data.get("aqi_description")),
                    "icon_path": icon_path
                }
                plot_path = plot_forecast(forecast_data, city)
                weather_data.append((weather_info, plot_path))
    
    return render_template("index.html", weather_data=weather_data)

if __name__ == "__main__":
    app.run(debug=True)
