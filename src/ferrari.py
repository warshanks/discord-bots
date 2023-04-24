import datetime
import random
import discord
from discord.ext import commands
from config import *
from cogs.f1_cog import F1Cog

start_time = datetime.datetime.now()  # Save the start time of the bot

# Create a bot instance with custom intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# Handle the "on_ready" event, which is triggered when the bot is connected and ready
@bot.event
async def on_ready():
    try:
        await bot.add_cog(F1Cog(bot))
        await command_sync(bot)
    except Exception as e:
        print(e)
    print("Ready in:", datetime.datetime.now() - start_time)  # Calculate the time it took for the bot to start


# Define the "generate_strategy" command handler
# noinspection PyUnresolvedReferences
@bot.tree.command(name="strat", description="Generate a racing strategy")
async def generate_strategy(interaction: discord.Interaction):
    global tire_str, total_distance_km, max_distance_km, selected_tires, distances_km
    print(interaction.user, interaction.guild, interaction.channel)
    # Generate a random racing strategy
    tire_types = ['Soft', 'Medium', 'Hard']
    num_tires = random.randint(1, 5)

    selected_tires = random.choices(tire_types, k=num_tires)

    max_distance_km = 300
    distances_km = [random.randint(1, max_distance_km) for _ in range(num_tires)]
    total_distance_km = sum(distances_km)

    # Format the racing strategy as a string and send it as a response
    try:
        tire_str = "\n".join(
            [f"Tire {i + 1}: {t} - Distance: {d} km" for i, (t, d) in enumerate(zip(selected_tires, distances_km))])
    except UnboundLocalError:
        pass

    try:
        if total_distance_km < max_distance_km:
            await interaction.response.send_message(
                tire_str + ", then retire. \nStrategy certified by Scuderia Ferrari 🐎")
        else:
            await interaction.response.send_message(tire_str + "\nStrategy certified by Scuderia Ferrari 🐎")
    except UnboundLocalError or NameError:
        await interaction.response.send_message("We are checking...")


# Handle the "on_message" event, which is triggered when a message is sent in a channel the bot has access to
@bot.event
async def on_message(message):
    if message.content.startswith('!strat'):
        await message.channel.send(
            "Please use /strat instead.")  # Remind the user to use the slash command instead of the old command


bot.run(Ferrari_TOKEN)  # Start the bot with the specified token
