"""
This module imports required libraries and configurations for building
a Discord bot cog with NASA data functionality.
It utilizes aiohttp for making asynchronous HTTP requests to the NASA API,
pytz for timezone handling, and the discord library for
building the cog.
The NASA API token is imported from the config file.

Imports:
    config: Contains the nasa_token configuration for accessing the NASA API.
    discord: A library for building Discord bots using Python.
    discord.ext.commands: Provides a framework for building Discord bot commands.
    aiohttp: A library for making asynchronous HTTP requests in Python.
    datetime: Provides the ability to work with dates and times.
    pytz: A library for handling timezone conversions and operations.
"""

import datetime
import discord
from discord.ext import commands
import aiohttp
import pytz
from config import nasa_token

bot = commands.Bot(command_prefix="~", intents=discord.Intents.all())

local_timezone = pytz.timezone("America/Chicago")

APOD_URL = "https://api.nasa.gov/planetary/apod"


async def fetch_apod(ctx, year, month, day):
    """
    This asynchronous function fetches the Astronomy Picture of the Day (APOD) from the NASA API.
    It takes a Discord context (ctx) and optional year, month, and day arguments.
    If no date is provided, the function uses the current date.
    It constructs a date string and sends an API request to fetch the APOD.
    If successful, it returns the APOD's title, explanation, image URL, date, and copyright
    information in a formatted string.

    Args:
        ctx (discord.ext.commands.Context): The context in which the command is invoked.
        year (int, optional): The year for which the APOD is requested.
        month (int, optional): The month for which the APOD is requested.
        day (int, optional): The day for which the APOD is requested.
        The date info is optional. If you don't specify the date,
        the function uses the current date.

    Returns:
        str: A formatted string containing the APOD's title, explanation, image URL, date, and
             copyright information if the API request is successful.
             If not, it returns an error message.
    """

    now = datetime.datetime.now(local_timezone)

    if year is None:
        year = datetime.datetime.now().year
    if month is None:
        month = datetime.datetime.now().month
    if day is None:
        day = now.day

    date = f"{year}-{month}-{day}"

    params = {
        'date': date,
        'api_key': nasa_token,
        'hd': 'True'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(APOD_URL, params=params) as response:
                if response.status != 200:
                    return f"Error: Unable to fetch APOD for date {date}. " \
                           f"Please try again. {response.status}\n" \
                           f"{params} {nasa_token}"
                data = await response.json()
    except Exception as error_message:
        await ctx.followup.send(f"Error: {error_message}")

    title = data['title']
    explanation = data['explanation']
    image_url = data['hdurl']
    try:
        copyrights = data['copyright']
    except KeyError:
        copyrights = "No copyright info provided"
    apod_date = data['date']

    output = f"**{title}**\n\n" \
             f"{explanation}\n\n" \
             f"**Date:** {apod_date}\n" \
             f"**Credits:** {copyrights}\n" \
             f"{image_url}" \

    return output


# noinspection PyShadowingNames
class NASACog(commands.Cog):
    """
    A Discord commands.Cog class for fetching and displaying information from the NASA API,
    particularly the Astronomy Picture of the Day (APOD).
    """

    @bot.tree.command(name="apod",
                      description="Get the Astronomy Picture of the Day. "
                                  "Optionally specify a date using the format YYYY-MM-DD.")
    async def apod(self, ctx, year: int = None, month: int = None, day: int = None):
        """
        An asynchronous function that sends the Astronomy Picture of the Day (APOD) in response
        to the 'apod' command. Users can optionally provide a date in the format YYYY-MM-DD.
        If no date is provided, the function fetches the APOD for the current date.

        Args:
            ctx (discord.ext.commands.Context): The context in which the command is invoked.
            year (int, optional): The year for which the APOD is requested. Defaults to None.
            month (int, optional): The month for which the APOD is requested. Defaults to None.
            day (int, optional): The day for which the APOD is requested. Defaults to None.
        """
        await ctx.response.defer(thinking=True, ephemeral=False)
        await ctx.followup.send(await fetch_apod(ctx, year, month, day))
