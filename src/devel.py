import datetime
import discord
from discord.ext import commands

from config import Devel_TOKEN, command_sync
# from cogs.weather_cog import WeatherCog
# from cogs.image_cog import ImageCog
# from cogs.chat_cog import ChatCog
# from cogs.music_cog import MusicCog
# from cogs.tts_cog import TTSCog
from cogs.f1_cog import F1Cog, EventsCog
from cogs.f1_cog import CacheCog
from cogs.weather_cog import NWSAlertsCog

# Get the start time of the program
start_time = datetime.datetime.now()

# Initialize a new Discord bot instance
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


# Event handler for when the bot is ready to use
@bot.event
async def on_ready():
    try:
        await bot.add_cog(EventsCog(bot))
        await bot.add_cog(NWSAlertsCog(bot))
        await command_sync(bot)
    except Exception as e:
        print(e)
    # Calculate the time it took for the client to start
    print("Ready in:", datetime.datetime.now() - start_time)


# Start the bot with the specified token
bot.run(Devel_TOKEN)
