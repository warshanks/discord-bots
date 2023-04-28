from os import makedirs
import random

import discord
import fastf1
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from discord.ext import commands
from fastf1 import plotting, utils
from matplotlib import cm
from matplotlib.collections import LineCollection

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

makedirs('./fastf1_cache/Data', exist_ok=True)
makedirs('./images', exist_ok=True)
makedirs('./csv_output', exist_ok=True)
fastf1.Cache.enable_cache('./fastf1_cache/Data')

background_color = (0.212, 0.224, 0.243)  # Set the background color for the plots


# noinspection PyShadowingNames
class F1Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Define a custom command for generating a gear map for a given session
    @bot.tree.command(name='gear-map',
                      description="Generate a gear map for a given session")
    async def generate_gear_map(self, ctx, year: int, event: str, session: str = 'Q'):
        # Defer the response to show that the bot is working on the request
        await ctx.response.defer(thinking=True, ephemeral=False)

        # Set the plot background color
        plt.rcParams['axes.facecolor'] = background_color

        # Load the specified session data and handle possible errors
        try:
            ff1session = fastf1.get_session(year, event, session)
            ff1session.load()
        except Exception as e:
            await ctx.followup.send(e)
            return

        # Get the fastest lap from the session and its telemetry data
        lap = ff1session.laps.pick_fastest()
        tel = lap.get_telemetry()

        # Prepare data for the gear map visualization
        x = np.array(tel['X'].values)
        y = np.array(tel['Y'].values)
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        gear = tel['nGear'].to_numpy().astype(float)

        # Set up the color map for the gear map visualization
        cmap = cm.get_cmap('Paired')
        lc_comp = LineCollection(segments, norm=plt.Normalize(1, cmap.N + 1), cmap=cmap)
        lc_comp.set_array(gear)
        lc_comp.set_linewidth(4)

        # Add the gear map to the plot
        plt.gca().add_collection(lc_comp)
        plt.axis('equal')
        plt.tick_params(
            labelleft=False,
            left=False,
            labelbottom=False,
            bottom=False,
            labelcolor='white'
        )

        # Set the title for the plot
        plt.suptitle(
            f"Fastest Lap Gear Shift Visualization\n"
            f"{lap['Driver']} - {ff1session.event['EventName']} {session.upper()} {year}",
            color='white'
        )

        # Add a color bar to the plot to indicate gear values
        cbar = plt.colorbar(mappable=lc_comp, label='Gear', boundaries=np.arange(1, 10))
        cbar.set_ticks(np.arange(1.5, 9.5))
        cbar.set_ticklabels(np.arange(1, 9))
        cbar.ax.yaxis.set_tick_params(color='white', labelcolor='white')
        cbar.set_label('Gear', color='white')

        # Set the figure background color
        plt.gcf().set_facecolor(background_color)

        # Save the plot as an image file
        plt.savefig('./images/gear_map.png', facecolor=background_color)

        # Send the image file in the follow-up message
        await ctx.followup.send(file=discord.File('./images/gear_map.png'))

        # Close the plot to free up resources
        plt.close()

    # Define a custom command for comparing two drivers' telemetry
    @bot.tree.command(name='driver-compare', description="Compare two drivers' telemetry")
    async def compare_drivers(self, ctx, year: int, event: str, session: str,
                              driver1: str, driver2: str, lap: int = None):
        # Defer the response to show that the bot is working on the request
        await ctx.response.defer(thinking=True, ephemeral=False)

        # Set the plot background color
        plt.rcParams['axes.facecolor'] = background_color

        # Format the driver, event, and session names
        driver1 = driver1.upper()
        driver2 = driver2.upper()
        event = event.title()
        session = session.upper()

        # Load the specified session data and handle possible errors
        try:
            ff1session = fastf1.get_session(year, event, session)
            ff1session.load()
        except Exception as e:
            await ctx.followup.send(e)
            return

        # Retrieve the drivers' lap data, either the fastest lap or a specific lap
        if lap is None:
            driver1_lap = ff1session.laps.pick_driver(driver1).pick_fastest()
            driver2_lap = ff1session.laps.pick_driver(driver2).pick_fastest()

        elif lap > 0:
            driver1_laps = ff1session.laps.pick_driver(driver1)
            driver1_lap = driver1_laps[driver1_laps['LapNumber'] == lap].iloc[0]

            driver2_laps = ff1session.laps.pick_driver(driver2)
            driver2_lap = driver2_laps[driver2_laps['LapNumber'] == lap].iloc[0]
        else:
            await ctx.followup.send("Lap number must be greater than 0")
            return

        # Get telemetry data for both drivers
        driver1_tel = driver1_lap.get_car_data().add_distance()
        driver2_tel = driver2_lap.get_car_data().add_distance()

        # Calculate the time difference between the drivers
        delta_time, ref_tel, compare_tel = utils.delta_time(driver1_lap, driver2_lap)

        # Get the colors associated with each driver
        driver1_color = plotting.driver_color(driver1)
        driver2_color = plotting.driver_color(driver2)

        # Create the figure and axes for the plots
        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(10, 14))

        # First plot (RPM comparison)
        ax1.plot(driver1_tel['Distance'], driver1_tel['RPM'], color=driver1_color, label=driver1)
        ax1.plot(driver2_tel['Distance'], driver2_tel['RPM'], color=driver2_color, label=driver2)
        ax1.set_xlabel('Distance in m', color='white')
        ax1.set_ylabel('RPM', color='white')
        ax1.tick_params(axis='both', colors='white')
        leg1 = ax1.legend()
        for text in leg1.get_texts():
            text.set_color('white')

        # Second plot (Speed and DRS comparison)
        ax2.plot(driver1_tel['Distance'], driver1_tel['Speed'], color=driver1_color, label=driver1)
        ax2.plot(driver1_tel['Distance'], driver1_tel['DRS'], '--', color=driver1_color, label=driver1 + " DRS")
        ax2.plot(driver2_tel['Distance'], driver2_tel['Speed'], color=driver2_color, label=driver2)
        ax2.plot(driver2_tel['Distance'], driver2_tel['DRS'], '--', color=driver2_color, label=driver2 + " DRS")

        ax2.set_xlabel('Distance in m', color='white')
        ax2.set_ylabel('Speed in km/h\nDRS (>10 = Active)', color='white')
        ax2.tick_params(axis='both', colors='white')

        # Create a twin axis for the time difference plot
        twin = ax2.twinx()
        twin.plot(ref_tel['Distance'], delta_time, '--', color='white')
        twin.set_ylabel("<-- " + driver2 + " ahead | " + driver1 + " ahead -->",
                        color='white')
        twin.tick_params(axis='both', colors='white')

        # Format the legend for the second plot
        leg2 = ax2.legend()
        for text in leg2.get_texts():
            text.set_color('white')

        # Set the title for the entire plot
        title = f"{'Fastest' if lap is None else f'L{lap}'} Lap Comparison \n "
        title += f"{ff1session.event['EventName']} {ff1session.event.year} {session}"
        plt.suptitle(title, color='white', y=0.95)

        # Set the figure background color
        plt.gcf().set_facecolor(background_color)

        # Save the plot as an image file
        plt.savefig('./images/driver_comparison.png', facecolor=background_color)

        # Send the image file in the follow-up message
        await ctx.followup.send(file=discord.File('./images/driver_comparison.png'))

        # Close the plot to free up resources
        plt.close()

    # Define the "data_dump" command handler
    @bot.tree.command(name="data-dump", description="Generate a .CSV data dump of a given session")
    async def data_dump(self, ctx, year: int, event: str, session: str, driver: str):
        await ctx.response.defer(thinking=True, ephemeral=False)
        event = event.title()
        session = session.upper()
        driver = driver.upper()
        # Load the specified session data and handle possible errors
        try:
            ff1session = fastf1.get_session(year, event, session)
            ff1session.load(telemetry=False)
        except Exception as e:
            await ctx.followup.send(e)
            return

        laps = ff1session.laps.pick_driver(driver)
        laps = laps.reset_index(drop=True)
        weather_data = ff1session.laps.pick_driver(driver).get_weather_data()
        weather_data = weather_data.reset_index(drop=True)
        joined = pd.concat([laps, weather_data.loc[:, ~(weather_data.columns == 'Time')]], axis=1)

        joined.to_csv("./csv_output/dump.csv")
        await ctx.followup.send(file=discord.File("./csv_output/dump.csv"))

    # Define the "Year vs Year" command handler
    @bot.tree.command(name="year-vs-year", description="Generate a comparison of two years")
    async def year_vs_year(self, ctx, year1: int, year2: int, event: str, session: str,
                           driver1: str = None, driver2: str = None):
        await ctx.response.defer(thinking=True, ephemeral=False)

        # Set the plot background color
        plt.rcParams['axes.facecolor'] = background_color

        event = event.title()
        session = session.upper()

        # Load the specified session data and handle possible errors
        try:
            ff1year1 = fastf1.get_session(year1, event, session)
            ff1year1.load()
            ff1year2 = fastf1.get_session(year2, event, session)
            ff1year2.load()
        except Exception as e:
            await ctx.followup.send(e)
            return

        if driver1 is None:
            driver1_lap = ff1year1.laps.pick_fastest()
            driver1 = driver1_lap['Driver']
        elif driver1 is not None:
            driver1 = driver1.upper()
            driver1_lap = ff1year1.laps.pick_driver(driver1).pick_fastest()
        else:
            await ctx.followup.send("Something went wrong, try again.")
            return

        if driver2 is None:
            driver2_lap = ff1year2.laps.pick_fastest()
            driver2 = driver2_lap['Driver']
        elif driver2 is not None:
            driver2 = driver2.upper()
            driver2_lap = ff1year2.laps.pick_driver(driver2).pick_fastest()
        else:
            await ctx.followup.send("Something went wrong, try again.")
            return

        # Get car data and add distance
        driver1_tel = driver1_lap.get_car_data().add_distance()
        driver2_tel = driver2_lap.get_car_data().add_distance()

        # Setup delta time comparisons
        delta_time, ref_tel, compare_tel = utils.delta_time(driver1_lap, driver2_lap)

        # Set driver colors
        driver1_color = plotting.driver_color(driver1)
        driver2_color = plotting.driver_color(driver2)

        # Setup plot and pick data
        # Assign attributes to each graph like driver name and color
        fig, ax = plt.subplots()

        # Speed over Distance with a condition for legibility when the drivers being compared are the same color
        if driver1 == driver2:
            ax.plot(driver1_tel['Distance'], driver1_tel['Speed'], color=driver1_color,
                    label=driver1 + str(year1))
            ax.plot(driver2_tel['Distance'], driver2_tel['Speed'], '--', color=driver2_color,
                    label=driver2 + str(year2))

        else:
            ax.plot(driver1_tel['Distance'], driver1_tel['Speed'], color=driver1_color,
                    label=driver1 + str(year1))
            ax.plot(driver2_tel['Distance'], driver2_tel['Speed'], color=driver2_color,
                    label=driver2 + str(year2))

        # Label the plot
        ax.set_xlabel('Distance in m', color='white')
        ax.set_ylabel('Speed in km/h', color='white')
        ax.tick_params(axis='both', colors='white')

        # Define twin x-axis
        twin = ax.twinx()
        twin.plot(ref_tel['Distance'], delta_time, '--', color='white', label="Delta")
        twin.set_ylabel("<-- " + driver2 + str(year2) + " ahead | " + driver1 + str(year1) + " ahead -->",
                        color='white')
        twin.tick_params(axis='both', colors='white')

        leg1 = ax.legend()
        for text in leg1.get_texts():
            text.set_color('white')

        # Set the figure background color
        plt.gcf().set_facecolor(background_color)

        # Plot subtitle with session information
        plt.suptitle(f"Year vs Year Comparison \n "
                     f"{ff1year1.event['EventName']} {year1} {year2} {session}", color='white')

        # Save the plot to a file
        plt.savefig("./images/year_vs_year.png")

        # Send the plot to the user
        await ctx.followup.send(file=discord.File("./images/year_vs_year.png"))

        plt.close()

    # Define the "generate_strategy" command handler
    # noinspection PyUnresolvedReferences
    @bot.tree.command(name="strat", description="Generate a racing strategy")
    async def generate_strategy(self, ctx):
        # Declare global variables to be used in this function
        global tire_str, total_distance_km, max_distance_km, selected_tires, distances_km

        # Print user, guild, and channel information for debugging purposes
        print(ctx.user, ctx.guild, ctx.channel)

        # Initialize the tire types and randomly select the number of tires to be used
        tire_types = ['Soft', 'Medium', 'Hard']
        num_tires = random.randint(1, 5)
        selected_tires = random.choices(tire_types, k=num_tires)

        # Set the maximum distance and generate random distances for each tire
        max_distance_km = 300
        distances_km = [random.randint(1, max_distance_km) for _ in range(num_tires)]
        total_distance_km = sum(distances_km)

        # Create a formatted string for the racing strategy, handling possible errors
        try:
            tire_str = "\n".join(
                [f"Tire {i + 1}: {t} - Distance: {d} km" for i, (t, d) in enumerate(zip(selected_tires, distances_km))])
        except UnboundLocalError:
            pass

        # Send the racing strategy as a message, handling possible errors and checking for total distance
        try:
            if total_distance_km < max_distance_km:
                await ctx.response.send_message(
                    tire_str + ", then retire. \nStrategy certified by Scuderia Ferrari 🐎")
            else:
                await ctx.response.send_message(tire_str + "\nStrategy certified by Scuderia Ferrari 🐎")
        except UnboundLocalError or NameError:
            await ctx.response.send_message("We are checking...")  # Send a message in case of errors
