import datetime
import discord
from discord.ext import commands

from cogs.f1_cog import F1Cog, CacheCog, EventsCog
from cogs.weather_cog import WeatherCog
from config import Ferrari_TOKEN, command_sync

start_time = datetime.datetime.now()  # Save the start time of the bot

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


# Handle the "on_ready" event, which is triggered when the bot is connected and ready
@bot.event
async def on_ready():
    try:
        await bot.add_cog(F1Cog(bot))
        await bot.add_cog(CacheCog(bot))
        await bot.add_cog(EventsCog(bot))
        await bot.add_cog(WeatherCog(bot))
        await command_sync(bot)
    except Exception as e:
        print(e)
    print("Ready in:", datetime.datetime.now() - start_time)  # Calculate the time it took for the bot to start


bot.run(Ferrari_TOKEN)  # Start the bot with the specified token
