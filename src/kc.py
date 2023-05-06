import datetime

import discord
from discord.ext import commands

from config import *
from cogs.chat_cog import ChatCog, GPT4Cog
from cogs.tts_cog import TTSCog
from cogs.image_cog import ImageCog
from cogs.music_cog import MusicCog
from cogs.weather_cog import WeatherCog, NWSAlertsCog
from cogs.nasa_cog import NASACog

# Get the start time of the program
start_time = datetime.datetime.now()

# Initialize a new Discord bot instance
bot = commands.Bot(command_prefix="~", intents=discord.Intents.all())


# Event handler for when the bot is ready to use
@bot.event
async def on_ready():
    try:
        await bot.add_cog(MusicCog(bot))
        await bot.add_cog(ChatCog(bot))
        await bot.add_cog(GPT4Cog(bot))
        await bot.add_cog(TTSCog(bot))
        await bot.add_cog(ImageCog(bot))
        await bot.add_cog(WeatherCog(bot))
        await bot.add_cog(NWSAlertsCog(bot))
        await bot.add_cog(NASACog(bot))
        await command_sync(bot)
    except Exception as e:
        print(e)
    # Calculate the time it took for the client to start
    print("Ready in:", datetime.datetime.now() - start_time)

# Start the bot with the specified token
bot.run(KC_TOKEN)
