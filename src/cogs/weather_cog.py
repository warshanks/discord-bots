import urllib.request
import discord
from discord.ext import commands
from pyowm import OWM
from datetime import datetime
import pytz

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
    "10n": ":cloud_rain:",
    "11d": ":thunder_cloud_rain:",
    "11n": ":thunder_cloud_rain:",
    "13d": ":cloud_snow:",
    "13n": ":cloud_snow:",
    "50d": ":fog:",
    "50n": ":fog:",
}


def degrees_to_cardinal(degrees: int) -> str:
    # List of cardinal directions in clockwise order.
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

    # Divide the input angle (in degrees) by 22.5, which is the angular width of each cardinal direction.
    # Then, round the result to find the nearest cardinal direction index.
    index = round(degrees / 22.5)

    # Use the modulo operation to ensure that the index stays within the bounds of the list (0-15).
    index = index % 16

    # Return the cardinal direction corresponding to the calculated index.
    return directions[index]


# noinspection PyShadowingNames
class WeatherCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # This is the main weather command that generates a weather report for a specified location
    @bot.tree.command(name="weather",
                      description="Generate a report on current conditions in a given location.")
    async def weather(self, ctx, *,
                      city: str = "Tuscaloosa",
                      country_code: str = "US"):
        # Defer response to give time to fetch data
        await ctx.response.defer(thinking=True, ephemeral=False)
        # Format input data
        city = city.title()
        country_code = country_code.upper()
        location = f"{city},{country_code}"
        try:
            # Fetch weather data for the location
            observation = mgr.weather_at_place(location)
            weather = observation.weather

            # Process and format weather data
            status = weather.detailed_status.title()
            icon_name = weather.weather_icon_name
            temp = weather.temperature("fahrenheit")["temp"]
            feels_like = weather.temperature("fahrenheit")["feels_like"]
            wind_speed = round(weather.wind(unit="miles_hour")["speed"], 2)
            wind_direction = weather.wind(unit="miles_hour")["deg"]
            wind_cardinal = degrees_to_cardinal(wind_direction)
            humidity = weather.humidity
            visibility = weather.visibility(unit="miles")
            rain_dict = weather.rain
            rain_1h = rain_dict.get("1h", 0)

        except Exception as e:
            await ctx.followup.send(e)
            return

        # Get the current date and time in UTC
        now_utc = datetime.utcnow()

        # Convert UTC timezone to US/Central timezone
        us_central_time_zone = pytz.timezone('US/Central')
        now_cst = now_utc.replace(tzinfo=pytz.utc).astimezone(us_central_time_zone)

        icon = emoji_dict.get(icon_name, "")

        # Send formatted weather report
        await ctx.followup.send(f"""
    **Weather Report**
    **Location:** {location}
    **Status:** {status} {icon}
    **Temperature:** {temp}°F
    **Feels Like:** {feels_like}°F
    **Wind Speed:** {wind_speed} mph
    **Wind Direction:** {wind_direction}° {wind_cardinal}
    **Humidity:** {humidity}%
    **Visibility:** {visibility} mi.
    **Rainfall:** Last hour: {rain_1h}mm
    **Report Generated:** {now_cst.strftime('%m/%d/%Y %I:%M:%S %p')} CST
    """)

    # Command to retrieve the latest convective outlook from the SPC at NOAA
    @bot.tree.command(name="outlook", description="Retrieve the latest convective outlook from the SPC at NOAA.")
    async def outlook(self, ctx):
        await ctx.response.defer(thinking=True, ephemeral=False)
        now = datetime.now()

        # Determine the closest time for the outlook image
        time_strings = ["0100", "1200", "1300", "1630", "2000"]
        times = [datetime.strptime(x, '%H%M').replace(
            year=now.year,
            month=now.month,
            day=(now.day + 1 if x < now.strftime('%H%M') else now.day)) for x in time_strings]
        closest_time_index = min(range(len(times)), key=lambda i: abs(times[i] - now))
        print(time_strings[closest_time_index])

        try:
            # Retrieve the outlook image
            url = f"https://www.spc.noaa.gov/products/outlook/day1otlk_{time_strings[closest_time_index]}.gif"
            urllib.request.urlretrieve(url, "./images/outlook.gif")
        except Exception as e:
            await ctx.followup.send(e)
            return

        # Send the outlook image
        await ctx.followup.send(file=discord.File("./images/outlook.gif"))

        # Command to retrieve a radar loop from the NWS

    @bot.tree.command(name="radar-loop", description="Retrieve a radar loop from the NWS.")
    async def radar_loop(self, ctx):
        await ctx.response.defer(thinking=True, ephemeral=False)

        try:
            # Retrieve the radar loop image
            url = f"https://radar.weather.gov/ridge/standard/SOUTHMISSVLY_loop.gif"
            urllib.request.urlretrieve(url, "./images/activity_loop.gif")
        except Exception as e:
            await ctx.followup.send(e)
            return

        # Send the radar loop image
        await ctx.followup.send(file=discord.File("./images/activity_loop.gif"))

    # Command to retrieve a radar loop from the NWS for a specific region (BMX)
    @bot.tree.command(name="bmx-radar", description="Retrieve a radar loop from the NWS.")
    async def bmx_radar(self, ctx):
        await ctx.response.defer(thinking=True, ephemeral=False)

        try:
            # Retrieve the BMX radar loop image
            url = f"https://radar.weather.gov/ridge/standard/KBMX_loop.gif"
            urllib.request.urlretrieve(url, "./images/bmx_radar.gif")
        except Exception as e:
            await ctx.followup.send(e)
            return

        # Send the BMX radar loop image
        await ctx.followup.send(file=discord.File("./images/bmx_radar.gif"))
