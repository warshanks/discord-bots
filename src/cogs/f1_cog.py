from os import makedirs

import discord
import fastf1
import matplotlib.pyplot as plt
import numpy as np
from discord.ext import commands
from fastf1 import plotting, utils
from matplotlib import cm
from matplotlib.collections import LineCollection

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

makedirs('../fastf1_cache/Data', exist_ok=True)
makedirs('./images', exist_ok=True)
fastf1.Cache.enable_cache('../fastf1_cache/Data')

background_color = (0.2, 0.2, 0.2)


# noinspection PyShadowingNames
class F1Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bot.tree.command(name='gear-map',
                      description="Generate a gear map for a given session")
    async def generate_gear_map(self, ctx, year: int, event: str, session: str = 'Q'):
        await ctx.response.defer(thinking=True, ephemeral=False)

        plt.rcParams['axes.facecolor'] = background_color

        ff1session = fastf1.get_session(year, event, session)
        ff1session.load()

        lap = ff1session.laps.pick_fastest()
        tel = lap.get_telemetry()

        x = np.array(tel['X'].values)
        y = np.array(tel['Y'].values)

        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        gear = tel['nGear'].to_numpy().astype(float)

        # Setup color map
        cmap = cm.get_cmap('Paired')
        lc_comp = LineCollection(segments, norm=plt.Normalize(1, cmap.N + 1), cmap=cmap)
        lc_comp.set_array(gear)
        lc_comp.set_linewidth(4)

        plt.gca().add_collection(lc_comp)
        plt.axis('equal')
        plt.tick_params(labelleft=False, left=False, labelbottom=False, bottom=False)

        plt.suptitle(
            f"Fastest Lap Gear Shift Visualization\n"
            f"{lap['Driver']} - {ff1session.event['EventName']} {session.upper()} {year}",
            color='white'
        )

        cbar = plt.colorbar(mappable=lc_comp, label='Gear', boundaries=np.arange(1, 10))
        cbar.set_ticks(np.arange(1.5, 9.5))
        cbar.set_ticklabels(np.arange(1, 9))

        plt.gcf().set_facecolor(background_color)

        plt.savefig('./images/gear_map.png', facecolor=background_color)

        await ctx.followup.send(file=discord.File('./images/gear_map.png'))
        plt.close()

    @bot.tree.command(name='driver-compare', description="Compare two drivers' telemetry")
    async def compare_drivers(self, ctx, year: int, event: str, session: str,
                              driver1: str, driver2: str, lap: int = None):
        await ctx.response.defer(thinking=True, ephemeral=False)
        plt.rcParams['axes.facecolor'] = background_color
        driver1 = driver1.upper()
        driver2 = driver2.upper()
        event = event.title()
        session = session.upper()
        ff1session = fastf1.get_session(year, event, session)
        ff1session.load()

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

        print(driver1_lap)
        print(driver2_lap)

        driver1_tel = driver1_lap.get_car_data().add_distance()
        driver2_tel = driver2_lap.get_car_data().add_distance()

        delta_time, ref_tel, compare_tel = utils.delta_time(driver1_lap, driver2_lap)

        driver1_color = plotting.driver_color(driver1)
        driver2_color = plotting.driver_color(driver2)

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

        twin = ax2.twinx()
        twin.plot(ref_tel['Distance'], delta_time, '--', color='white')
        twin.set_ylabel("<-- " + driver2 + " ahead | " + driver1 + " ahead -->", color='white')
        twin.tick_params(axis='both', colors='white')

        leg2 = ax2.legend()
        for text in leg2.get_texts():
            text.set_color('white')

        title = f"{'Fastest' if lap is None else f'L{lap}'} Lap Comparison \n "
        title += f"{ff1session.event['EventName']} {ff1session.event.year} {session}"
        plt.suptitle(title, color='white', y=0.95)

        plt.gcf().set_facecolor(background_color)

        plt.savefig('./images/driver-comparison.png', facecolor=background_color)

        await ctx.followup.send(file=discord.File('./images/driver-comparison.png'))

        plt.close()
