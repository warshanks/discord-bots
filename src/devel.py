import datetime
import discord
from discord.ext import commands

from config import *
from cogs.weather_cog import WeatherCog
from cogs.image_cog import ImageCog
from cogs.f1_cog import F1Cog

# Get the start time of the program
start_time = datetime.datetime.now()

# Initialize a new Discord bot instance
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


# Event handler for when the bot is ready to use
@bot.event
async def on_ready():
    try:
        await bot.add_cog(WeatherCog(bot))
        await bot.add_cog(ImageCog(bot))
        await bot.add_cog(F1Cog(bot))
        await command_sync(bot)
    except Exception as e:
        print(e)
    # Calculate the time it took for the client to start
    print("Ready in:", datetime.datetime.now() - start_time)


# Start the bot with the specified token
bot.run(Devel_TOKEN)
