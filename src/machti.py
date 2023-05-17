import datetime

import discord
from discord.ext import commands

from cogs.machti_cog import MachtiCog

from config import Machti_TOKEN, command_sync

# Get the start time of the program
start_time = datetime.datetime.now()

# Initialize a new Discord bot instance
bot = commands.Bot(command_prefix="~", intents=discord.Intents.all())


# Event handler for when the bot is ready to use
@bot.event
async def on_ready():
    try:
        await bot.add_cog(MachtiCog(bot))
        await command_sync(bot)
    except Exception as e:
        print(e)
    # Calculate the time it took for the client to start
    print("Ready in:", datetime.datetime.now() - start_time)


# Start the bot with the specified token
bot.run(Machti_TOKEN)
