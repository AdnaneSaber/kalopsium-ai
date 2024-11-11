from config import config
import openai
import requests
import json
from fastapi import FastAPI


app = FastAPI()

api_key = config['OPENWEATHER_API_KEY']


def handle_message(query: str) -> dict:
    url = 'https://words.kalopsium.com/weather/'
    body = json.dumps({"question": query})
    response = requests.post(url, body)
    data = response.json()
    city, day, lang = data['city'], data['day'], data['language']
    get_lon_lat_url = f'http://api.openweathermap.org/geo/1.0/direct?appid={api_key}&q={city}&units=metric'
    response_2 = requests.get(get_lon_lat_url)
    _data = response_2.json()[0]
    lon, lat, _city = _data['lon'], _data['lat'], _data['name']
    city = _city
    weather_data = fetch_weather_data(lon, lat)
    days_data = weather_data['list']
    todays_weather_data = None
    if len(days_data):
        for day_data in days_data:
            if day in day_data['dt_txt']:
                todays_weather_data = day_data
                break
        del weather_data['list']
        return {**weather_data, "day_data": todays_weather_data, "lang": lang, 'city': city}
    else:
        return {"error": "out of scoop"}


def fetch_weather_data(lon: float, lat: float) -> dict:
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Could not retrieve weather data"}


def process_user_query(query: str) -> dict:
    data = handle_message(query)
    weather_data = data['day_data']
    if weather_data is None:
        return {"error": "Could not retrieve weather data"}
    if "error" in weather_data:
        return {"error": weather_data["error"]}
    city = data['city']

    # Structure weather data for SAMBANOVA
    weather_info = {
        "temperature": weather_data["main"]["temp"],
        "condition": weather_data["weather"][0]["description"],
        "city": city,
    }
    return weather_info


def send_to_sambanova(weather_info: dict) -> str:
    # Create a prompt for the weather inquiry
    prompt = (
        f"The user asked about the weather in {weather_info['city']}. "
        f"Here is the weather data:\n"
        f"Temperature: {weather_info['temperature']}°C\n"
        f"Condition: {weather_info['condition']}."
        "Please generate a friendly response."
    )

    # Send the prompt to OpenAI (or another model if needed)
    client = openai.OpenAI(
        api_key=config['SAMBANOVA_API_KEY'],
        base_url="https://api.sambanova.ai/v1",
    )
    response = client.chat.completions.create(
        model='Meta-Llama-3.1-8B-Instruct',
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user",
                "content": f"Tell me about the weather in {weather_info['city']}."}
        ],
        temperature=0.1,
        top_p=0.1
    )
    return response.choices[0].message.content


def handle_weather_query(query: str) -> str:
    weather_info = process_user_query(query)

    if "error" in weather_info:
        return weather_info["error"]

    return send_to_sambanova(weather_info)


@app.post('/messenger')
async def handle_message(query: str):
    return handle_weather_query(query)
