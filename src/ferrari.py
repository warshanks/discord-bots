"""
This module initializes a Discord bot with various Cogs related to Formula 1 and weather.
It imports required modules, Cogs, and configurations.
The Cogs added to the bot include F1Cog, CacheCog, EventsCog, and WeatherCog,
providing functionality for Formula 1 information, caching, events, and
weather information.

Imports:
    datetime: Provides the ability to work with dates and times.
    discord: A library for building Discord bots using Python.
    discord.ext.commands: Provides a framework for building Discord bot commands.
    cogs.f1_cog: Contains the F1Cog, CacheCog, and EventsCog classes for Formula 1 functionality.
    cogs.weather_cog: Contains the WeatherCog class for providing weather information.
    config: Contains the Ferrari_TOKEN and command_sync configurations.
"""

import datetime

import discord
from discord.ext import commands

from cogs.f1_cog import F1Cog, CacheCog, EventsCog
from cogs.weather_cog import WeatherCog
from config import Ferrari_TOKEN, command_sync

start_time = datetime.datetime.now()  # Save the start time of the bot

bot = commands.Bot(command_prefix="~", intents=discord.Intents.all())


@bot.event
async def on_ready():
    """
    Event handler for when the bot is ready to use.
    This function adds various Cogs to the bot and
    attempts to synchronize the commands.
    It also calculates the time taken for the bot to start.

    Usage:
        This function is used as an event listener within the Discord bot.
        When the bot is ready to use,
        it adds various Cogs for F1, cache, events, and weather,
        and attempts to synchronize the commands.
        If an exception occurs, it prints the error message.
        The function also calculates and prints the
        time taken for the bot to start.
    """

    try:
        await bot.add_cog(F1Cog(bot))
        await bot.add_cog(CacheCog(bot))
        await bot.add_cog(EventsCog(bot))
        await bot.add_cog(WeatherCog(bot))
        await command_sync(bot)
    except Exception as error_message:
        print(error_message)
    # Calculate the time it took for the bot to start
    print("Ready in:", datetime.datetime.now() - start_time)

# Start the bot with the specified token
bot.run(Ferrari_TOKEN)
