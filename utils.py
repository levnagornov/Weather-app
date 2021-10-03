import datetime as dt

import requests
import pandas

from flask import session


class OpenWeatherApi:
    def __init__(self, api_key, units, lang) -> None:
        self.api_key = api_key
        self.units = units
        self.lang = lang


    def get_city_coordinates(self, city: str) -> str:
        """Get weather API of OpenWeatherMap from <city>. If it exist will return city coordinates as a dict.
        For example {'lon': 52.4289, 'lat': 55.7561}
        """

        api_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": self.units,
            "lang": self.lang,
        }
        response = requests.get(api_url, params=params)

        if response.ok:
            response = response.json()

            return response["coord"]


    def get_weather(self, lat, lon, part) -> str:
        """Get weather API of OpenWeatherMap from <place>. If it exist will return weather as a dict."""

        api_url = "https://api.openweathermap.org/data/2.5/onecall"
        params = {
            "lat": lat,
            "lon": lon,
            "exclude": part,
            "appid": self.api_key,
            "units": self.units,
            "lang": self.lang,
        }
        response = requests.get(api_url, params=params)
        if response.ok:
            response = response.json()

            return (weekly_forecast for weekly_forecast in response["daily"])

def get_weekly_forecast_from_xl(path_xl_file):
    weather = OpenWeatherApi(
        api_key="41c94dc66a745d6f4f245f158b18e871",
        units="metric",
        lang="ru",
    )

    workbook = pandas.read_excel(path_xl_file)
    cities = workbook.get("Город")
    if cities is None:
        return None

    data = [("Город", "Дата", "Минимальная температура"),]
    for city in cities:
        city_coordinates = weather.get_city_coordinates(city)
        if city_coordinates:
            weekly_forecast = weather.get_weather(
                lat=city_coordinates["lat"],
                lon=city_coordinates["lon"],
                part="current,minutely,hourly,alerts"
            )

            for dayly_forecast in weekly_forecast:
                forecast_datetime = dt.datetime.fromtimestamp(dayly_forecast["dt"])
                forecast_date = forecast_datetime.strftime("%d.%m.%Y")
                day_min_temp = dayly_forecast["temp"]["min"]
                data.append((city, forecast_date, day_min_temp))
        else:
            data.append((city, "Город не найден", "Город не найден"))

    resulted_forecast = pandas.DataFrame(data[1:], columns = data[0])
    now = dt.datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
    file_name = "result_" + str(now) + ".xlsx"
    session['report_name'] = file_name
    session['FORECAST_READY'] = True
    resulted_forecast.to_excel(file_name, index=False)
    

def allowed_xl_file(filename):
    """Returns True if file is allowable to Pandas excel reader"""
    
    ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'xlsm', 'xlsb'}

    return '.' in filename and \
           filename.split('.')[1].lower() in ALLOWED_EXTENSIONS