from config import *
import discord
from discord.ext import commands
import aiohttp
import datetime
import pytz

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

local_timezone = pytz.timezone("America/Chicago")


async def fetch_apod(ctx, year, month, day):

    now = datetime.datetime.now(local_timezone)
    
    apod_url = "https://api.nasa.gov/planetary/apod"
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
            async with session.get(apod_url, params=params) as response:
                if response.status != 200:
                    return f"Error: Unable to fetch APOD for date {date}. " \
                           f"Please try again. {response.status}\n" \
                           f"{params} {nasa_token}"
                data = await response.json()
    except Exception as e:
        await ctx.followup.send(f"Error: {e}")

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
class NasaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bot.tree.command(name="apod", description="Get the Astronomy Picture of the Day. "
                                               "Optionally specify a date using the format YYYY-MM-DD.")
    async def apod(self, ctx, year: int = None, month: int = None, day: int = None):
        await ctx.response.defer(thinking=True, ephemeral=False)
        await ctx.followup.send(await fetch_apod(ctx, year, month, day))
