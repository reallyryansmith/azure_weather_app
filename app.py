import os
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

API_KEY = os.getenv("WEATHER_API_KEY")  # Set this in App Service config

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    city = ""
    if request.method == 'POST':
        city = request.form['city']
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&units=imperial&appid={API_KEY}'
        response = requests.get(url)
        if response.ok:
            weather_data = response.json()
        else:
            weather_data = {'error': 'City not found'}
    return render_template('index.html', weather=weather_data, city=city)

if __name__ == '__main__':
    app.run(debug=True)
