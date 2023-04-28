import discord
from discord.ext import commands
from pyowm import OWM
from datetime import datetime

from config import owm_token


owm = OWM(owm_token)
mgr = owm.weather_manager()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

emoji_dict = {
    "01d": ":sunny:",
    "01n": ":new_moon_with_face:",
    "02d": ":white_sun_small_cloud:",
    "02n": ":cloud:",
    "03d": ":cloud:",
    "03n": ":cloud:",
    "04d": ":cloud:",
    "04n": ":cloud:",
    "09d": ":cloud_rain:",
    "09n": ":cloud_rain:",
    "10d": ":white_sun_rain_cloud:",
    "10n": ":white_sun_rain_cloud:",
    "11d": ":thunder_cloud_rain:",
    "11n": ":thunder_cloud_rain:",
    "13d": ":cloud_snow:",
    "13n": ":cloud_snow:",
    "50d": ":fog:",
    "50n": ":fog:",
}


# noinspection PyShadowingNames
class WeatherCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bot.tree.command(name="weather",
                      description="Generate a report on current conditions in a given location.")
    async def weather(self, ctx, *, location: str = "Tuscaloosa,US"):
        await ctx.response.defer(thinking=True, ephemeral=False)
        try:
            observation = mgr.weather_at_place(location)
            weather = observation.weather
            status = weather.detailed_status.title()
            icon_name = weather.weather_icon_name
            temp = weather.temperature("fahrenheit")["temp"]
            feels_like = weather.temperature("fahrenheit")["feels_like"]
            wind_speed = weather.wind(unit="miles_hour")["speed"]
            wind_direction = weather.wind(unit="miles_hour")["deg"]
            humidity = weather.humidity
            rain_dict = weather.rain
            rain_1h = rain_dict["1h"] if "1h" in rain_dict else 0
            rain_3h = rain_dict["3h"] if "3h" in rain_dict else 0

        except Exception as e:
            print(e)
            await ctx.followup.send("An error occurred while fetching weather data.")
            return

        if icon_name in emoji_dict:
            icon = emoji_dict[icon_name]
        else:
            icon = ""

        await ctx.followup.send(""
                                "**Weather Report**\n"
                                f"**Location:** {location}\n"
                                f"**Status:** {status} {icon}\n"
                                f"**Temperature:** {temp}°F\n"
                                f"**Feels Like:** {feels_like}°F\n"
                                f"**Wind Speed:** {wind_speed} mph\n"
                                f"**Wind Direction:** {wind_direction}°\n"
                                f"**Humidity:** {humidity}%\n"
                                f"**Rainfall:** Last hour: {rain_1h}mm, Last 3 hours: {rain_3h}mm\n"
                                f"**Report Generated:** {datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')}\n"
                                )
