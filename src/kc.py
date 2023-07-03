"""
This module imports the necessary libraries and classes for a multi-functional
Discord bot. The bot features various cogs to handle different types of commands,
such as chat interactions, text-to-speech, image processing, music playback,
weather updates, and fetching data from NASA's API.

Libraries:
    - datetime: Used for handling date and time-related operations.
    - discord: A library for creating Discord bots and interacting with the Discord API.
    - discord.ext.commands: Provides a framework for creating commands for the Discord bot.
    - config: A custom module that contains configuration settings, such as API tokens,
              and command synchronization settings for the Discord bot.

Classes:
    - ChatCog: Handles chat interactions using the GPT-3.5-turbo model.
    - GPT4Cog: An extension of ChatCog for specific GPT-4 interactions.
    - TTSCog: Handles text-to-speech functionality.
    - ImageCog: Processes image-related commands and manipulations.
    - MusicCog: Manages music playback commands and interactions.
    - WeatherCog: Provides weather updates and information.
    - NWSAlertsCog: Retrieves and displays National Weather Service alerts.
    - NASACog: Fetches data from NASA's API for various space-related information.
"""

import datetime

import discord
from discord.ext import commands

from config import command_sync, KC_TOKEN
from cogs.chat_cog import ChatCog, GPT4Cog
# from cogs.tts_cog import TTSCog
from cogs.image_cog import ImageCog
from cogs.music_cog import MusicCog
from cogs.weather_cog import WeatherCog, NWSAlertsCog
from cogs.nasa_cog import NASACog


# Get the start time of the program
start_time = datetime.datetime.now()

# Initialize a new Discord bot instance
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
        When the bot is ready to use, it adds various Cogs for
        music, chat, GPT-4, TTS, image, weather, NWS alerts, and NASA,
        and attempts to synchronize the commands.
        If an exception occurs, it prints the error message.
        The function also calculates and prints the time taken for the bot to start.
    """

    try:
        await bot.add_cog(MusicCog(bot))
        await bot.add_cog(ChatCog(bot))
        await bot.add_cog(GPT4Cog(bot))
        # await bot.add_cog(TTSCog(bot))
        await bot.add_cog(ImageCog(bot))
        await bot.add_cog(WeatherCog(bot))
        await bot.add_cog(NWSAlertsCog(bot))
        await bot.add_cog(NASACog(bot))
        await command_sync(bot)
    except Exception as error_message:
        print(error_message)
    # Calculate the time it took for the client to start
    print("Ready in:", datetime.datetime.now() - start_time)

# Start the bot with the specified token
bot.run(KC_TOKEN)
