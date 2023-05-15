"""
This module contains a Discord cog that provides weather-related functionality,
including fetching current weather conditions, forecasts, and weather alerts.
It uses the OpenWeatherMap API to retrieve weather data and
posts updates to a specified Discord channel.

Imports:
    - os: To interact with the operating system.
    - urllib.request: To handle URL-related tasks.
    - aiohttp: To perform asynchronous HTTP requests.
    - asyncio: To handle asynchronous tasks.
    - discord: To interact with the Discord API.
    - commands, tasks (from discord.ext): To create bot commands and background tasks.
    - OWM (from pyowm): To access the OpenWeatherMap API.
    - datetime, timedelta: To work with dates and times.
    - randint (from random): To generate a random delay.
    - pytz: To handle timezone conversions.
    - owm_token, weather_alert_channel (from config): To access the bot's configuration settings.
"""

import os
import urllib.request
import asyncio
from datetime import datetime, timedelta
from random import randint
import aiohttp
import discord
from discord.ext import commands, tasks
from pyowm import OWM
import pytz

from config import owm_token, weather_alert_channel

owm = OWM(owm_token)
mgr = owm.weather_manager()

bot = commands.Bot(command_prefix="~", intents=discord.Intents.all())

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

radar_dict = {
    "ALC125": "https://radar.weather.gov/ridge/standard/KBMX_loop.gif",
    "ALC089": "https://radar.weather.gov/ridge/standard/KHTX_loop.gif",
    "ALC049": "https://radar.weather.gov/ridge/standard/KHTX_loop.gif",
    "ALZ010": "https://radar.weather.gov/ridge/standard/KHTX_loop.gif",
    "ALZ006": "https://radar.weather.gov/ridge/standard/KHTX_loop.gif",
    "ALZ023": "https://radar.weather.gov/ridge/standard/KBMX_loop.gif",
}

SENT_ALERTS_FILE = "./logs/sent_alerts.txt"


def log_time():
    """
    Log the current time in the US/Central timezone to a log file (kc_stdout.log)
    with a message indicating that NWS alerts are being fetched.
    The time is formatted as a string in the format "HH:mm:ss AM/PM".
    """

    # Create a timezone object for the CST timezone
    time_zone = pytz.timezone("US/Central")

    # Get the current time in the CST timezone
    now = datetime.now(time_zone)

    # Format the time as a string
    time_str = now.strftime("%I:%M:%S %p")

    # Write the message to the log file
    with open("./logs/kc_stdout.log", "a", encoding="utf-8") as log_file:
        log_file.write("Fetching NWS Alerts @ " + time_str + "\n")


def wait_time():
    """
    Generate a random number of seconds between 60 and 180.
    """
    return randint(60, 180)


def api_timestamp_to_cst(api_timestamp):
    """
        Convert an API timestamp to a formatted datetime string in the CST timezone.

        Args:
            api_timestamp (str): A string representing the API timestamp in ISO format.

        Returns:
            str: A formatted datetime string in the CST timezone,
                 in the format 'mm-dd-yyyy hh:mm AM/PM'.
        """
    api_dt = datetime.fromisoformat(api_timestamp)
    cst = pytz.timezone('America/Chicago')
    dt_cst = api_dt.astimezone(cst)
    return dt_cst.strftime('%m-%d-%Y %I:%M %p')


def build_output(alert):
    """
    Build an output string for a given alert.

    Args:
        alert (dict): A dictionary containing alert information, with nested 'properties'.

    Returns:
        str: A formatted output string containing alert details.
    """
    properties = ["headline", "description", "instruction", "areaDesc", "urgency", "severity"]
    time_properties = ["effective", "onset", "expires"]
    output = ""
    for prop in properties:
        try:
            output += "\n" + alert["properties"][prop]
        except TypeError:
            pass
    for time_prop in time_properties:
        try:
            api_timestamp = alert["properties"][time_prop]
            cst_time = api_timestamp_to_cst(api_timestamp)
            output += f"\n{time_prop.capitalize()}: {cst_time}"
        except TypeError:
            pass

    try:
        # Get the list of affected zones.
        zone_list = alert["properties"]["geocode"]["UGC"]

        # Get the first matching zone from the radar dictionary.
        first_matching_zone = list(set(zone_list) & set(radar_dict))[0]

        # Add the radar loop url for the first matching zone to the output string.
        output += "\n" + radar_dict[first_matching_zone]
    except (KeyError, IndexError):
        pass

    output += "\n@here"
    return output


def save_sent_alerts(alert_id):
    """
    Save the sent alert ID to a file.

    Args:
        alert_id (str): The ID of the sent alert.
    """
    with open(SENT_ALERTS_FILE, "a", encoding="utf-8") as file:
        file.write(alert_id + "\n")


def load_sent_alerts():
    """
    Load the sent alert IDs from a file and return them as a set.

    Returns:
        set: A set of sent alert IDs. Returns an empty set if the file doesn't exist.
    """
    if not os.path.exists(SENT_ALERTS_FILE):
        return set()

    with open(SENT_ALERTS_FILE, "r", encoding="utf-8") as file:
        return set(line.strip() for line in file.readlines())


# noinspection PyShadowingNames
async def fetch_api_data(bot, url):
    """
    Fetch API data and send alerts if they haven't been sent before.

    Args:
        bot (discord.ext.commands.Bot): The bot instance.
        url (str): The API endpoint URL to fetch data from.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            alerts = data["features"]
            if len(alerts) == 0:
                return

            sent_alerts = load_sent_alerts()
            for alert in alerts:
                alert_id = alert["properties"]["id"]
                if alert_id not in sent_alerts:
                    output = build_output(alert)
                    channel = bot.get_channel(weather_alert_channel)
                    await channel.send(output)
                    save_sent_alerts(alert_id)


# noinspection PyShadowingNames
async def fetch_loop(bot):
    """
        Fetch alerts for multiple locations in a loop.

        Args:
            bot (discord.ext.commands.Bot): The bot instance.
    """
    api_urls = [
        "https://api.weather.gov/alerts/active?zone=ALC125",  # Tuscaloosa
        "https://api.weather.gov/alerts/active?zone=ALC089",  # Huntsville
        "https://api.weather.gov/alerts/active?zone=ALC049",  # Henagar
        # Add more URLs as needed
    ]

    for county in api_urls:
        await fetch_api_data(bot, county)


def degrees_to_cardinal(degrees: int) -> str:
    """
    Convert a given angle in degrees to the nearest cardinal direction.

    Args:
        degrees (int): The angle in degrees, with 0 being North and 360 being a full circle.

    Returns:
        str: The nearest cardinal direction (e.g., N, NE, E, SE, S, SW, W, NW).
    """

    # List of cardinal directions in clockwise order.
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

    # Divide the input angle (in degrees) by 22.5,
    # which is the angular width of each cardinal direction.
    # Then, round the result to find the nearest cardinal direction index.
    index = round(degrees / 22.5)

    # Use the modulo operation to ensure that the index stays within the bounds of the list (0-15).
    index = index % 16

    # Return the cardinal direction corresponding to the calculated index.
    return directions[index]


# noinspection PyShadowingNames
class WeatherCog(commands.Cog):
    """
        A Discord Cog that provides various weather-related commands.
    """
    # This is the main weather command that generates a weather report for a specified location
    @bot.tree.command(name="weather",
                      description="Generate a report on current conditions in a given location.")
    async def weather(self, ctx, *,
                      city: str = "Tuscaloosa",
                      country_code: str = "US"):
        """
        Generates a weather report for the specified location.
        If no location is provided, defaults to Tuscaloosa, US.
        """
        # Defer response to give time to fetch data
        await ctx.response.defer(thinking=True, ephemeral=False)
        # Format input data
        location = f"{city.title()},{country_code.upper()}"
        try:
            # Fetch weather data for the location
            observation = mgr.weather_at_place(location)
            weather = observation.weather

            # Process and format weather data
            icon_name = weather.weather_icon_name
            rain_dict = weather.rain
            rain_1h = rain_dict.get("1h", 0)

        except Exception as error_message:
            await ctx.followup.send(error_message)
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
    **Status:** {weather.detailed_status.title()} {icon}
    **Temperature:** {weather.temperature("fahrenheit")["temp"]}°F
    **Feels Like:** {weather.temperature("fahrenheit")["feels_like"]}°F
    **Wind Speed:** {round(weather.wind(unit="miles_hour")["speed"], 2)} mph
    **Wind Direction:** {weather.wind(unit="miles_hour")["deg"]}°{
        degrees_to_cardinal(weather.wind(unit="miles_hour")["deg"])}
    **Humidity:** {weather.humidity}%
    **Visibility:** {weather.visibility(unit="miles")} mi.
    **Rainfall:** Last hour: {rain_1h}mm
    **Report Generated:** {now_cst.strftime('%m/%d/%Y %I:%M:%S %p')} CST
    """)

    # Command to retrieve the latest convective outlook from the SPC at NOAA
    @bot.tree.command(name="outlook",
                      description="Retrieve the latest convective outlook from the SPC at NOAA.")
    async def outlook(self, ctx):
        """
        Retrieves the latest convective outlook image from
        the SPC at NOAA and sends it as a message.
        """
        # Defer the response to indicate the bot is thinking
        await ctx.response.defer(thinking=True, ephemeral=False)

        # Get the current datetime
        now = datetime.now()

        # Define the possible time strings for the outlook images
        time_strings = ["0100", "1200", "1300", "1630", "2000"]

        # Calculate the datetimes corresponding to the time_strings,
        # with the correct year, month, and day
        times = [datetime.strptime(x, '%H%M').replace(
            year=now.year,
            month=now.month,
            # Add 1 day to the current date
            # if the time_string is less than the current time,
            # otherwise keep the current day
            day=(now + timedelta(days=1)).day if x < now.strftime('%H%M') else now.day)
            for x in time_strings
        ]

        # Find the index of the closest datetime in the times list to the current datetime
        closest_time_index = min(range(len(times)), key=lambda i: abs(times[i] - now))

        # Print the corresponding time string for the closest datetime
        print(time_strings[closest_time_index])

        try:
            # Construct the URL for the outlook image using the closest time string
            url = f"https://www.spc.noaa.gov/products/outlook/day1otlk_" \
                  f"{time_strings[closest_time_index]}.gif"

            # Retrieve the outlook image and save it to the local "images" folder
            urllib.request.urlretrieve(url, "./images/outlook.gif")
        except Exception as error_message:
            # If there is an error, send the error message as a follow-up message and return
            await ctx.followup.send(error_message)
            return

        # Send the outlook image as a follow-up message
        await ctx.followup.send(file=discord.File("./images/outlook.gif"))

    # Command to retrieve a radar loop from the NWS
    @bot.tree.command(name="radar-loop",
                      description="Retrieve a radar loop from the NWS.")
    async def radar_loop(self, ctx):
        """
        Retrieves a radar loop image from the NWS and sends it as a message.
        """
        await ctx.response.defer(thinking=True, ephemeral=False)

        try:
            # Retrieve the radar loop image
            url = "https://radar.weather.gov/ridge/standard/SOUTHMISSVLY_loop.gif"
            urllib.request.urlretrieve(url, "./images/activity_loop.gif")
        except Exception as error_message:
            await ctx.followup.send(error_message)
            return

        # Send the radar loop image
        await ctx.followup.send(file=discord.File("./images/activity_loop.gif"))

    # Command to retrieve a radar loop from the NWS for a specific region (BMX)
    @bot.tree.command(name="bmx-radar", description="Retrieve a radar loop from the NWS.")
    async def bmx_radar(self, ctx):
        """
        Retrieves a BMX radar loop image from the NWS and sends it as a message.
        """
        await ctx.response.defer(thinking=True, ephemeral=False)

        try:
            # Retrieve the BMX radar loop image
            url = "https://radar.weather.gov/ridge/standard/KBMX_loop.gif"
            urllib.request.urlretrieve(url, "./images/bmx_radar.gif")
        except Exception as error_message:
            await ctx.followup.send(error_message)
            return

        # Send the BMX radar loop image
        await ctx.followup.send(file=discord.File("./images/bmx_radar.gif"))


# noinspection PyShadowingNames
class NWSAlertsCog(commands.Cog):
    """
    A Discord Cog class for periodically fetching and sending National Weather Service (NWS) alerts.

    Attributes:
        bot (commands.Bot): The instance of the bot connected to the Discord server.
        nws_alerts (tasks.loop): A loop running the NWS alerts fetching and sending process.
    """

    def __init__(self, bot):
        """
        Initialize the NWSAlertsCog with a reference to the bot and start the nws_alerts task loop.

        Args:
            bot (commands.Bot): The instance of the bot connected to the Discord server.
        """
        self.bot = bot
        self.nws_alerts.start()

    @tasks.loop(minutes=1)
    async def nws_alerts(self):
        """
        Periodically fetch NWS alerts and send them to a designated Discord channel.
        This function is executed every minute as part of a task loop.
        """
        log_time()
        await fetch_loop(self.bot)
        await asyncio.sleep(wait_time())
