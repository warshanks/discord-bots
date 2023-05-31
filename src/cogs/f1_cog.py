"""
This module imports various libraries and packages for the purpose of analyzing Formula 1 data,
creating and managing Discord bot commands, and generating visualizations. The imported libraries
and packages include:

- os: to create directories.
- random: to generate random numbers.
- datetime: to work with date and time objects.
- asyncio: to work with asynchronous operations.
- discord: to interact with the Discord API.
- fastf1: to analyze Formula 1 data.
- matplotlib: to create visualizations.
- numpy: to handle numerical computations.
- pandas: to work with data manipulation and analysis.
- pytz: to handle timezone conversions.
- discord.ext.commands: to create and manage Discord bot commands.
- icalendar: to parse and generate iCalendar files.
"""

from os import makedirs
import random
from datetime import datetime
import asyncio
import discord
import fastf1
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytz
from discord.ext import commands
from fastf1 import plotting, utils
from fastf1.ergast import Ergast
from icalendar import Calendar
from matplotlib import cm
from matplotlib.collections import LineCollection

bot = commands.Bot(command_prefix="~", intents=discord.Intents.all())

makedirs('./images', exist_ok=True)
makedirs('./csv_output', exist_ok=True)
fastf1.Cache.enable_cache('../fastf1_cache/Data')

background_color = (0.212, 0.224, 0.243)  # Set the background color for the plots

emoji_dict = {
    'Red Bull': '<:team_redbull:1104918421235306566>',
    'Mercedes': '<:team_mercedes:1104918388876251276>',
    'Ferrari': '<:team_ferrari:1104918385126539335>',
    'McLaren': '<:team_mclaren:1104918387869622302>',
    'Alpine F1 Team': '<:team_alpine:1104918382974877801>',
    'AlphaTauri': '<:team_alphatauri:1104918382102446120>',
    'Alfa Romeo': '<:team_alfaromeo:1104918380621873262>',
    'Haas F1 Team': '<:team_haas:1104918386300944384>',
    'Williams': '<:team_williams:1104918392202342472>',
    'Aston Martin': '<:team_astonmartin:1104918384212181032>',
}


def is_weekend(date):
    """
    Determine if the given date falls on a weekend.

    Args:
        date (datetime.date): The date to be checked.

    Returns:
        bool: True if the date falls on a weekend, False otherwise.
    """
    return date.weekday() >= 4


async def read_calendar_data(file_path):
    """
    Read calendar data from a file asynchronously.

    Args:
        file_path (str): The path of the calendar file to be read.

    Returns:
        str: The calendar data as a string.
    """
    with open(file_path, "r", encoding="utf-8") as calendar_file:
        calendar_data = calendar_file.read()
    await asyncio.sleep(0)  # Yield control back to the event loop
    return calendar_data


async def parse_calendar_data(calendar_data):
    """
    Parse calendar data asynchronously and create a Calendar object.

    Args:
        calendar_data (str): The calendar data as a string.

    Returns:
        Calendar: The parsed Calendar object.
    """
    calendar = Calendar.from_ical(calendar_data)
    await asyncio.sleep(0)  # Yield control back to the event loop
    return calendar


async def extract_events(calendar):
    """
    Extract events asynchronously from a Calendar object and sort them by start time.

    Args:
        calendar (Calendar): A Calendar object.

    Returns:
        list: A sorted list of tuples containing event start time, end time, and name.
    """
    events = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            event_start = component.get('dtstart').dt
            event_end = component.get('dtend').dt
            event_name = component.get('summary')

            if event_start.tzinfo:
                event_start = event_start.astimezone(pytz.utc)

            events.append((event_start, event_end, event_name))
    events.sort(key=lambda x: x[0])
    await asyncio.sleep(0)  # Yield control back to the event loop
    return events


async def filter_and_format_events(events, now, timezone):
    """
    Filter the list of events to only include weekend events that haven't started yet,
    and format the event information as a string.

    Args:
        events (list): A list of tuples containing event start time, end time, and name.
        now (datetime): The current datetime in UTC.
        timezone (timezone): A timezone object representing the desired output timezone.

    Returns:
        str: A formatted string containing filtered event information.
    """
    output = ""
    for event_start, event_end, event_name in events:
        if event_start > now and is_weekend(event_start):
            event_start_cst = event_start.astimezone(timezone)
            event_end_cst = event_end.astimezone(timezone)

            event_output = f"{event_name}: {event_start_cst.strftime('%m-%d %I:%M %p')} - " \
                           f"{event_end_cst.strftime('%I:%M %p')}"

            output += event_output + "\n"

            if str(event_name).endswith("- Race") or "FEATURE" in str(event_name):
                break

    output += "\n*All times are in Central Standard Time (CST)*"

    await asyncio.sleep(0)  # Yield control back to the event loop
    return output


async def list_upcoming_events(ctx, cal_path):
    """
    List the upcoming events from the specified calendar file, filtered and formatted.

    Args:
        ctx (context): The command context from the Discord bot.
        cal_path (str): The path to the calendar file.

    Returns:
        None
    """
    await ctx.response.defer(thinking=True, ephemeral=False)

    calendar_data = await read_calendar_data(cal_path)
    calendar = await parse_calendar_data(calendar_data)
    now = datetime.now(pytz.utc)
    cst = pytz.timezone('America/Chicago')

    events = await extract_events(calendar)
    output = await filter_and_format_events(events, now, cst)
    # Send the output to the user
    await ctx.followup.send(output)


async def event_creator(ctx, event_name, event_start_cst, event_end_cst):
    """
    Create a scheduled event on the Discord server with the given details.

    Args:
        ctx (context): The command context from the Discord bot.
        event_name (str): The name of the event.
        event_start_cst (datetime): The start time of the event in Central Standard Time.
        event_end_cst (datetime): The end time of the event in Central Standard Time.

    Returns:
        None
    """
    # Get the current event loop to run synchronous tasks in an asynchronous manner
    loop = asyncio.get_event_loop()

    # Define a synchronous function for reading the image file
    def read_image_sync():
        """
        Read images for events synchronously.
        """
        # Open the image file in binary mode for reading
        with open('./images/red-bull-miami-crop.jpg', mode='rb') as file:
            # Read the contents of the file and return the bytes
            return file.read()

    # Run the synchronous function (read_image_sync) in a non-blocking manner using the event loop
    # This ensures that the file reading doesn't block other tasks running in the event loop
    image_bytes = await loop.run_in_executor(None, read_image_sync)

    # Create a scheduled event on the Discord server using the create_scheduled_event method
    await discord.Guild.create_scheduled_event(
        self=ctx.guild,  # The guild (server) where the event is being created
        name=event_name,  # The name of the event
        image=image_bytes,  # The image to use for the event (in bytes)
        channel=ctx.channel,  # The channel where the event is being created
        start_time=event_start_cst,  # The start time of the event (in Central Standard Time)
        end_time=event_end_cst  # The end time of the event (in Central Standard Time)
    )


async def get_driver_lap(driver, ff1year, ctx):
    """
    Get the fastest lap of a specified driver, or the fastest lap overall
    if no driver is specified.

    Args:
        driver (str): The driver's name or abbreviation (case-insensitive)
                      or None for the overall fastest lap.
        ff1year (fastf1.Year): The FastF1 Year object containing Formula 1 data
                               for the desired year.
        ctx (context): The command context from the Discord bot.

    Returns:
        tuple: A tuple containing the driver's name or abbreviation (str)
               and the fastest lap (fastf1.Lap) object.
    """
    # If the driver is not specified, get the fastest lap and the driver who set it
    if driver is None:
        driver_lap = ff1year.laps.pick_fastest()
        driver = driver_lap['Driver']
    # If the driver is specified, get the fastest lap for that driver
    elif driver is not None:
        driver = driver.upper()
        driver_lap = ff1year.laps.pick_driver(driver).pick_fastest()
    # If there's an unexpected case, send an error message and return None values
    else:
        await ctx.followup.send("Something went wrong, try again.")
        return None, None

    # Return the driver and their fastest lap
    return driver, driver_lap


def prepare_gear_map_data(tel):
    """
    Prepare gear map data from telemetry data for visualization.

    Args:
        tel (DataFrame): Telemetry data for a lap.

    Returns:
        Tuple: A tuple containing the segments (numpy array) and gear data (numpy array).
    """
    x_axis = np.array(tel['X'].values)
    y_axis = np.array(tel['Y'].values)
    points = np.array([x_axis, y_axis]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    gear = tel['nGear'].to_numpy().astype(float)

    return segments, gear


def load_session(year: int, event: str, session: str):
    """
    Load a racing session using the Fast-F1 library.

    Args:
        year (int): The year of the racing session.
        event (str): The name of the racing event.
        session (str): The type of session (e.g., 'FP1', 'FP2', 'FP3', 'Q', 'R').

    Returns:
        Session: The loaded racing session.
    """
    ff1session = fastf1.get_session(year, event, session)
    ff1session.load()
    return ff1session


# noinspection PyShadowingNames
def create_gear_map_plot(segments, gear, lap, ff1session, year, session):
    """
    Create a gear map plot for a given set of segments and gear data.

    Args:
        segments (numpy array): The segments data for the gear map.
        gear (numpy array): The gear data for the gear map.
        lap (Series): The lap data for the fastest lap in the session.
        ff1session (Session): The Fast-F1 session object.
        year (int): The year of the racing session.
        session (str): The type of session (e.g., 'FP1', 'FP2', 'FP3', 'Q', 'R').

    Returns:
        Figure: The created gear map plot as a matplotlib Figure object.
    """
    # Set the plot background color
    plt.rcParams['axes.facecolor'] = background_color

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

    return plt.gcf()


def get_lap_data(ff1session, driver1: str, driver2: str, lap: int = None):
    """
    Retrieve the lap data for the specified drivers, either the fastest lap or a specific lap.

    Args:
        ff1session (Session): A Fast-F1 session object containing the required event data.
        driver1 (str): The code of the first driver to compare.
        driver2 (str): The code of the second driver to compare.
        lap (int, optional): The lap number to retrieve data for. If None, the fastest lap is used.

    Returns:
        Tuple[Lap, Lap]: A tuple containing the lap data for both drivers.
    """
    try:
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
            raise ValueError("Lap number must be greater than 0")

    except Exception as error_message:
        raise error_message

    return driver1_lap, driver2_lap


def create_comparison_plot(driver1, driver2, driver1_tel, driver2_tel,
                           driver1_color, driver2_color, delta_time,
                           ref_tel, ff1session, session, lap=None):
    """
    Create a telemetry comparison plot for two drivers.

    Args:
        driver1 (str): The name of the first driver.
        driver2 (str): The name of the second driver.
        driver1_tel (DataFrame): The telemetry data of the first driver.
        driver2_tel (DataFrame): The telemetry data of the second driver.
        driver1_color (str): The color associated with the first driver.
        driver2_color (str): The color associated with the second driver.
        delta_time (Series): The time difference between the drivers.
        ref_tel (DataFrame): The reference telemetry data for calculating the time difference.
        ff1session (Session): The loaded racing session.
        session (str): The type of session (e.g., 'FP1', 'FP2', 'FP3', 'Q', 'R').
        lap (int, optional): The lap number to compare.
        If not specified, the drivers' fastest laps will be compared.

    Returns:
        Figure: The created telemetry comparison plot.
    """
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
    ax2.plot(driver1_tel['Distance'], driver1_tel['Speed'],
             color=driver1_color, label=driver1)
    ax2.plot(driver1_tel['Distance'], driver1_tel['DRS'], '--',
             color=driver1_color, label=driver1 + " DRS")

    ax2.plot(driver2_tel['Distance'], driver2_tel['Speed'],
             color=driver2_color, label=driver2)
    ax2.plot(driver2_tel['Distance'], driver2_tel['DRS'], '--',
             color=driver2_color, label=driver2 + " DRS")

    ax2.set_xlabel('Distance in m', color='white')
    ax2.set_ylabel('Speed in km/h\nDRS (>10 = Active)', color='white')
    ax2.tick_params(axis='both', colors='white')

    # Create a twin axis for the time difference plot
    twin = ax2.twinx()
    twin.plot(ref_tel['Distance'], delta_time, '--', color='white')
    twin.set_ylabel("<-- " + driver2 + " ahead | " + driver1 + " ahead -->", color='white')
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

    return fig


# noinspection PyShadowingNames
async def save_and_send_plot(plt, file_name: str, ctx):
    """
    Save the current plot as an image file and send it as a Discord attachment.

    Args:
        plt (Figure): The current plot.
        ctx (Context): The context of the command message.
        file_name (str): The name of the file to save the plot as.

    Returns:
        None
    """
    plt.savefig(file_name, facecolor=background_color)
    await ctx.followup.send(file=discord.File(file_name))


def setup_year_vs_year_plot(driver1_tel, driver1_color, driver1, year1,
                            driver2_tel, driver2_color, driver2, year2):
    """
    Set up the plot for the year_vs_year comparison.

    Args:
        driver1_tel (DataFrame): Telemetry data for driver1.
        driver1_color (str): Color associated with driver1.
        driver1 (str): Driver1's name.
        year1 (int): The first year to compare.
        driver2_tel (DataFrame): Telemetry data for driver2.
        driver2_color (str): Color associated with driver2.
        driver2 (str): Driver2's name.
        year2 (int): The second year to compare.

    Returns:
        Tuple[Figure, Axes, Axes]: The figure, main axis, and twin axis for the plot.
    """

    fig, ax = plt.subplots()

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

    ax.set_xlabel('Distance in m', color='white')
    ax.set_ylabel('Speed in km/h', color='white')
    ax.tick_params(axis='both', colors='white')

    twin = ax.twinx()
    twin.set_ylabel("<-- " + driver2 + str(year2) + " ahead | "
                    + driver1 + str(year1) + " ahead -->",
                    color='white')
    twin.tick_params(axis='both', colors='white')

    return fig, ax, twin


def get_drivers_standings(year: int = None):
    """
    Get the current driver standings from Ergast.

    Args:
        year (int): The year to get the standings for. Defaults to the current year.
    """
    if year is None:
        year = datetime.now().year
    ergast = Ergast()
    standings = ergast.get_driver_standings(season=year)
    return standings.content[0]


def get_constructor_standings(year: int = None):
    """
    Get the current constructor standings from Ergast.

    Args:
        year (int): The year to get the standings for. Defaults to the current year.
    """
    if year is None:
        year = datetime.now().year
    ergast = Ergast()
    standings = ergast.get_constructor_standings(season=year)
    return standings.content[0]


def format_driver_standings(standings):
    """
    Format the standings into a string.

    Args:
        standings (DataFrame): The standings to format.

    Returns:
        str: The formatted standings.
    """
    output = ""
    previous_points = None
    for index, row in standings.iterrows():
        position = row["position"]
        driver_name = f"{row['givenName']} {row['familyName']}"
        constructor = row["constructorNames"][0]
        constructor_emoji = emoji_dict.get(constructor, "")
        points = row["points"]
        wins = row["wins"]

        line = f"{position}. {driver_name} - {constructor_emoji} {constructor} - {points} points"
        if wins > 0:
            line += f", {wins} wins"
        if previous_points is not None:
            delta_points = previous_points - points
            line += f", [-{delta_points}]"
        output += line + "\n"
        previous_points = points

    return output


def format_constructors_standings(standings):
    """
    Format the standings into a string.

    Args:
        standings (DataFrame): The standings to format.

    Returns:
        str: The formatted standings.
    """
    output = ""
    previous_points = None
    for index, row in standings.iterrows():
        position = row["position"]
        constructor = row["constructorName"]
        constructor_emoji = emoji_dict.get(constructor, "")
        points = row["points"]
        wins = row["wins"]

        line = f"{position}. {constructor_emoji} {constructor} - {points} points"
        if wins > 0:
            line += f", {wins} wins"
        if previous_points is not None:
            delta_points = previous_points - points
            line += f", [-{delta_points}]"
        output += line + "\n"
        previous_points = points

    return output


def calculate_max_points_for_remaining_season():
    """
    Calculate the maximum number of points a driver can get for the rest of the season.

    Returns:
        int: The maximum number of points a driver can get for the rest of the season.
    """
    points_for_sprint = 8 + 25 + 1  # Winning the sprint, race and fastest lap
    points_for_conventional = 25 + 1  # Winning the race and fastest lap

    events = fastf1.events.get_events_remaining(backend='ergast')
    # Count how many sprints and conventional races are left
    sprint_events = len(events.loc[events["EventFormat"] == "sprint"])
    conventional_events = len(events.loc[events["EventFormat"] == "conventional"])

    # Calculate points for each
    sprint_points = sprint_events * points_for_sprint
    conventional_points = conventional_events * points_for_conventional

    return sprint_points + conventional_points


def calculate_who_can_win(driver_standings, max_points):
    """
    Calculate who can win the championship.
    This is done by calculating the maximum number of
    points a driver can get for the rest of the season.
    If the driver with the most points has more points than
    the current leader, then the driver can win the championship.

    Args:
        driver_standings (DataFrame): The current driver standings.
        max_points (int): The maximum number of points a driver can get for the rest of the season.

    Returns:
        str: A string containing the driver's position,
             name, current points, theoretical max points,
             and whether the driver can win the championship or not.
    """
    leader_points = int(driver_standings.loc[0]['points'])

    output = ''

    for i, _ in enumerate(driver_standings.iterrows()):
        driver = driver_standings.loc[i]
        driver_max_points = int(driver["points"]) + max_points
        can_win = 'No' if driver_max_points < leader_points else 'Yes'

        constructor = driver["constructorNames"][0]
        constructor_emoji = emoji_dict.get(constructor, "")

        output += (f"{driver['position']}: {constructor_emoji} {driver['givenName'] + ' ' + driver['familyName']}, "
                   f"Current points: {driver['points']}, "
                   f"Max possible: {driver_max_points}, "
                   f"Can win: {can_win}\n")

    return output


# noinspection PyShadowingNames
class EventsCog(commands.Cog):
    """
    A Discord bot cog for creating and managing events on a Discord server.
    """

    def __init__(self, bot):
        self.bot = bot

    @bot.tree.command(name='create-events', description='Create events for the upcoming weekend')
    async def create_events(self, ctx):
        """
        Create events for the upcoming weekend on the Discord server.

        Args:
            ctx (context): The command context from the Discord bot.
        """
        # Defer the response to indicate that the command is working
        await ctx.response.defer(thinking=True, ephemeral=True)
        if ctx.user.id != 141333182367793162:
            await ctx.followup.send('You do not have permission to use this command')
            return

        # Read the calendar data from the file
        calendar_data = await read_calendar_data("./calendar/23_calendar.ics")

        # Parse the calendar data
        calendar = await parse_calendar_data(calendar_data)

        # Extract the events from the calendar
        events = await extract_events(calendar)

        # Get the current time
        now = datetime.now(pytz.utc)

        # Get the timezone for the events
        timezone = pytz.timezone("US/Central")

        try:
            # Create a Discord event for each event in the calendar
            for event_start, event_end, event_name in events:
                if event_start > now and is_weekend(event_start):
                    event_start_cst = event_start.astimezone(timezone)
                    event_end_cst = event_end.astimezone(timezone)

                    await event_creator(ctx, event_name, event_start_cst, event_end_cst)
                    if str(event_name).endswith("- Race"):
                        break

            await ctx.followup.send('Events created successfully')
        except Exception as error_message:
            await ctx.followup.send(error_message)


# noinspection PyShadowingNames
class CacheCog(commands.Cog):
    """
    A Discord cog that provides functionality to cache data for a given event weekend.
    """

    def __init__(self, bot):
        self.bot = bot

    @bot.tree.command(name='cache', description='Cache data for a given event weekend')
    async def cache(self, ctx, year: int, event: str):
        """
        Caches data for a given event weekend.

        Parameters:
        -----------
        year : int
            The year of the event weekend to cache data for.
        event : str
            The name of the event weekend to cache data for.

        Raises:
        -------
        Exception:
            If there is an error while caching data for a session.
        """

        # Defer the response to indicate that the command is working
        await ctx.response.defer(thinking=True, ephemeral=True)

        # Check if the user has permission to use this command
        if ctx.user.id != 141333182367793162:
            await ctx.followup.send('You do not have permission to use this command')
            return

        # List of all sessions
        session_list = ["FP1", "FP2", "FP3", "Q", "SS", "SQ", "S", "R"]
        cached = ''
        not_cached = ''
        event = event.title()

        # Loop through all sessions
        for session in session_list:
            # Get session data for the specified event and current session
            try:
                ff1_session = fastf1.get_session(year, event, session)
                ff1_session.load()
                cached += session + ' '
            except Exception as error_message:
                not_cached = session + ' '
                ctx.response.send_message(error_message)
                continue

        # Send a success message after all sessions have been loaded
        if not_cached == '':
            await ctx.followup.send(f"Data for {event} {cached} cached successfully")
        else:
            await ctx.followup.send(f""
                                    f"Data for {event} {cached} cached successfully\n"
                                    f"Data for {event} {not_cached} not cached"
                                    )


# noinspection PyShadowingNames
class F1Cog(commands.Cog):
    """
    A Discord bot cog for providing Formula 1 data to a Discord server.

    Attributes:
    -----------
    bot : commands.Bot
        The Discord bot.

    Methods:
    --------
    generate_gear_map(self, ctx, year: int, event: str, session: str = 'Q')
        Generate a gear map visualization for the fastest lap of a specified racing session.

    compare_drivers(self, ctx,
                    year: int, event: str, session: str,
                    driver1: str, driver2: str, lap: int = None)
        Compare two drivers in a given session.
        A lap can be specified, otherwise the fastest lap is used.

    year_vs_year(self, ctx,
                 year1: int, year2: int, event: str, session: str,
                 driver1: str = None, driver2: str = None)
        Compare year over year differences for a given session.
        A driver can be specified, otherwise the fastest
        driver is used.

    data_dump(self, ctx, year: int, event: str, session: str, driver: str)
        Dump data for a given session to a CSV file.

    generate_strategy(self, ctx)
        Generates a meme "Ferrari certified strategy" that
        randomly picks between 1 and 5 tires, and assigns
        random distances for each tire to travel.
        If the total distance traveled is less than 300km, then
        the user is instructed to retire the car.

    next(self, ctx)
        Get the sessions and times for the
        upcoming F1 race weekend by reading
        from an ical calendar.

    next_f2(self, ctx)
        Get the sessions and times for the
        upcoming F2 race weekend by reading
        from an ical calendar.
    """

    def __init__(self, bot):
        self.bot = bot

    @bot.tree.command(name='gear-map',
                      description="Generate a gear map for a given session")
    async def generate_gear_map(self, ctx, year: int, event: str, session: str = 'Q'):
        """
        Generate a gear map visualization for the fastest lap of a specified racing session.
        The gear map illustrates gear shifts during the lap on a 2D plot. The plot is then
        sent as an image file to the user.

        Args:
            ctx (context): The command context provided by the Discord bot framework.
            year (int): The year of the racing session.
            event (str): The name of the racing event.
            session (str, optional): The type of session
                                     (e.g., 'FP1', 'FP2', 'FP3', 'Q', 'R'). Defaults to 'Q'.
        """
        await ctx.response.defer(thinking=True, ephemeral=False)

        try:
            ff1session = fastf1.get_session(year, event, session)
            ff1session.load()
        except Exception as error_message:
            await ctx.followup.send(error_message)
            return

        lap = ff1session.laps.pick_fastest()
        tel = lap.get_telemetry()

        segments, gear = prepare_gear_map_data(tel)
        gear_map_fig = create_gear_map_plot(
            segments,
            gear,
            lap,
            ff1session,
            year,
            session
        )

        # Save the plot as an image file
        gear_map_fig.savefig('./images/gear_map.png', facecolor=background_color)

        # Send the image file in the follow-up message
        await ctx.followup.send(file=discord.File('./images/gear_map.png'))

        # Close the plot to free up resources
        plt.close(gear_map_fig)

    @bot.tree.command(name='driver-compare',
                      description="Compare two drivers' telemetry")
    async def compare_drivers(self, ctx,
                              year: int, event: str, session: str,
                              driver1: str, driver2: str,
                              lap: int = None):
        """
        Compare the telemetry data of two drivers during a specified racing session.
        This function generates a plot comparing the drivers'
        RPM, speed, and DRS for either their fastest lap or a
        specific lap. The plot is then sent as an image file to the user.

        Args:
            ctx (context): The command context provided by the Discord bot framework.
            year (int): The year of the racing session.
            event (str): The name of the racing event.
            session (str): The type of session (e.g., 'FP1', 'FP2', 'FP3', 'Q', 'R').
            driver1 (str): The first driver's short name (e.g., 'HAM', 'VER').
            driver2 (str): The second driver's short name (e.g., 'HAM', 'VER').
            lap (int, optional): The lap number to compare.
                                 If not specified, the drivers' fastest laps will be compared.
        """
        await ctx.response.defer(thinking=True, ephemeral=False)
        plt.rcParams['axes.facecolor'] = background_color

        driver1 = driver1.upper()
        driver2 = driver2.upper()
        event = event.title()
        session = session.upper()

        try:
            ff1session = load_session(year, event, session)
        except Exception as error_message:
            await ctx.followup.send(error_message)
            return

        try:
            driver1_lap, driver2_lap = get_lap_data(ff1session, driver1, driver2, lap)
        except Exception as error_message:
            await ctx.followup.send(error_message)
            return

        driver1_tel = driver1_lap.get_car_data().add_distance()
        driver2_tel = driver2_lap.get_car_data().add_distance()

        delta_time, ref_tel, compare_tel = utils.delta_time(driver1_lap, driver2_lap)
        driver1_color = plotting.driver_color(driver1)
        driver2_color = plotting.driver_color(driver2)

        fig = create_comparison_plot(
            driver1,
            driver2,
            driver1_tel,
            driver2_tel,
            driver1_color,
            driver2_color,
            delta_time,
            ref_tel,
            ff1session,
            session,
            lap
        )

        await save_and_send_plot(fig, './images/driver_comparison.png', ctx)

        plt.close(fig)

    @bot.tree.command(name="year-vs-year",
                      description="Generate a comparison of two years")
    async def year_vs_year(self, ctx, year1: int, year2: int, event: str, session: str,
                           driver1: str = None, driver2: str = None):
        """
        Asynchronously generates a plot comparing the fastest laps
        of two drivers from two different years in a
        specified F1 event and session.

        Args:
            ctx: The context in which the command was called.
            year1: The first year to be compared.
            year2: The second year to be compared.
            event: The name of the event (e.g., "Monaco").
            session: The name of the session (e.g., "RACE").
            driver1: The first driver's name/code (default: None).
            driver2: The second driver's name/code (default: None).

        Returns:
            None
        """
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
        except Exception as error_message:
            await ctx.followup.send(error_message)
            return

        # Get the driver1 and their fastest lap
        driver1, driver1_lap = await get_driver_lap(driver1, ff1year1, ctx)
        # If an error occurred, exit the function
        if driver1 is None:
            return

        # Get the driver2 and their fastest lap
        driver2, driver2_lap = await get_driver_lap(driver2, ff1year2, ctx)
        # If an error occurred, exit the function
        if driver2 is None:
            return

        # Get car data and add distance
        driver1_tel = driver1_lap.get_car_data().add_distance()
        driver2_tel = driver2_lap.get_car_data().add_distance()

        # Setup delta time comparisons
        delta_time, ref_tel, compare_tel = utils.delta_time(driver1_lap, driver2_lap)

        # Set driver colors
        driver1_color = plotting.driver_color(driver1)
        driver2_color = plotting.driver_color(driver2)

        # Setup plot using the extracted function
        fig, ax, twin = setup_year_vs_year_plot(driver1_tel, driver1_color, driver1, year1,
                                                driver2_tel, driver2_color, driver2, year2)

        # Plot the time difference delta
        twin.plot(ref_tel['Distance'], delta_time, '--', color='white', label="Delta")

        leg1 = ax.legend()
        for text in leg1.get_texts():
            text.set_color('white')

        # Set the figure background color
        plt.gcf().set_facecolor(background_color)

        # Plot subtitle with session information
        plt.suptitle(f"Year vs Year Comparison \n "
                     f"{ff1year1.event['EventName']} {year1} {year2} {session}", color='white')

        await save_and_send_plot(plt, './images/year_vs_year.png', ctx)

        plt.close()

    @bot.tree.command(name="data-dump",
                      description="Generate a .CSV data dump of a given session")
    async def data_dump(self, ctx, year: int, event: str, session: str, driver: str):
        """
        Generate a .CSV data dump of a given session for a specified driver.
        The function retrieves session data, processes it, and exports it as a .CSV file.

        Args:
            ctx (context): The command context from the Discord bot.
            year (int): The year of the racing session.
            event (str): The name of the racing event.
            session (str): The type of session (e.g., 'FP1', 'FP2', 'FP3', 'Q', 'R').
            driver (str): The three-letter driver name for whom the data is to be exported.
        """
        await ctx.response.defer(thinking=True, ephemeral=False)

        # Normalize the event, session, and driver inputs
        event = event.title()
        session = session.upper()
        driver = driver.upper()

        # Load the specified session data and handle possible errors
        try:
            ff1session = fastf1.get_session(year, event, session)
            ff1session.load(telemetry=False)
        except Exception as error_message:
            await ctx.followup.send(error_message)
            return

        # Retrieve lap data for the specified driver
        laps = ff1session.laps.pick_driver(driver)
        laps = laps.reset_index(drop=True)

        # Retrieve weather data for the specified driver
        weather_data = ff1session.laps.pick_driver(driver).get_weather_data()
        weather_data = weather_data.reset_index(drop=True)

        # Combine lap and weather data into a single dataframe
        joined = pd.concat([laps, weather_data.loc[:, ~(weather_data.columns == 'Time')]], axis=1)

        # Export the combined data as a .CSV file
        joined.to_csv("./csv_output/dump.csv")

        # Send the .CSV file to the user
        await ctx.followup.send(file=discord.File("./csv_output/dump.csv"))

    # Define the "generate_strategy" command handler
    @bot.tree.command(name="strat",
                      description="Generate a racing strategy")
    async def generate_strategy(self, ctx):
        """
        This method generates a "racing strategy"
        by randomly selecting tire types and distances.
        It then formats and sends the strategy as a message to the user.

        Args:
        ctx (context): The command context provided by the Discord bot framework.

        Raises:
        UnboundLocalError: When an error occurs while creating the tire_str.
        NameError: When an error occurs while sending the racing strategy message.
        """
        await ctx.response.defer(thinking=True, ephemeral=False)
        # Initialize the tire types and randomly select the number of tires to be used
        tire_types = ['Soft', 'Medium', 'Hard']
        num_tires = random.randint(1, 5)
        selected_tires = random.choices(tire_types, k=num_tires)

        # Set the maximum distance and generate random distances for each tire
        max_distance_km = 300
        total_distance_km = 0
        distances_km = []
        for _ in range(num_tires):
            remaining_distance = max_distance_km - total_distance_km
            distance = random.randint(1, remaining_distance)
            distances_km.append(distance)
            total_distance_km += distance

        tire_str = ""

        # Create a formatted string for the racing strategy, handling possible errors
        try:
            tire_str = "\n".join(
                [f"Tire {i + 1}: {t} - Distance: {d} km"
                 for i, (t, d) in enumerate(zip(selected_tires, distances_km))])
        except UnboundLocalError:
            pass

        # Send the racing strategy as a message,
        # handling possible errors and checking for total distance
        try:
            if total_distance_km < max_distance_km:
                await ctx.followup.send(
                    tire_str + ", then retire. \nStrategy certified by Scuderia Ferrari 🐎")
            else:
                await ctx.followup.send(
                    tire_str + "\nStrategy certified by Scuderia Ferrari 🐎"
                )
        except UnboundLocalError:
            await ctx.followup.send("We are checking...")
        except NameError:
            await ctx.followup.send("We are checking...")

    @bot.tree.command(name="next",
                      description="List upcoming F1 events")
    async def next(self, ctx):
        """
        List the upcoming Formula 1 events by
        sending a message to the user with the event details.
        This method reads the calendar data from a file and
        delegates the event listing to the 'list_upcoming_events' function.

        Args:
            ctx (context): The command context from the Discord bot.
        """
        cal_path = "./calendar/23_calendar.ics"
        await list_upcoming_events(ctx, cal_path)

    @bot.tree.command(name="next-f2",
                      description="List upcoming F2 events")
    async def next_f2(self, ctx):
        """
        List the upcoming Formula 2 events by
        sending a message to the user with the event details.
        This method reads the calendar data from a file and
        delegates the event listing to the 'list_upcoming_events' function.

        Args:
            ctx (context): The command context from the Discord bot.
        """
        cal_path = "./calendar/f2-calendar_q_sprint_feature.ics"
        await list_upcoming_events(ctx, cal_path)

    @bot.tree.command(name="wdc-standings",
                      description="List the WDC standings")
    async def wdc_standings(self, ctx):
        """
        List the current World Drivers' Championship standings
        by sending a message to the user with the standings.
        This method retrieves the current drivers' standings and
        delegates the listing to the 'list_standings' function.

        Args:
            ctx (context): The command context from the Discord bot.
        """
        await ctx.response.defer(thinking=True, ephemeral=False)
        year = datetime.now().year
        # Get the current drivers standings
        driver_standings = get_drivers_standings(year)

        # Print the standings
        formatted_standings = format_driver_standings(driver_standings)
        await ctx.followup.send(formatted_standings)

    @bot.tree.command(name="wcc-standings",
                      description="List the WCC standings")
    async def wcc_standings(self, ctx):
        """
        List the current World Constructors' Championship standings
        by sending a message to the user with the standings.
        This method retrieves the current constructors' standings and
        delegates the listing to the 'list_standings' function.

        Args:
            ctx (context): The command context from the Discord bot.
        """
        await ctx.response.defer(thinking=True, ephemeral=False)
        year = datetime.now().year
        # Get the current constructors standings
        constructor_standings = get_constructor_standings(year)

        # Print the standings
        formatted_standings = format_constructors_standings(constructor_standings)
        await ctx.followup.send(formatted_standings)

    @bot.tree.command(name="can-win-wdc",
                      description="List drivers who can still win the WDC")
    async def can_win_wdc(self, ctx):
        """
        List the drivers who can still win the World Drivers' Championship.
        This method retrieves the current drivers' standings and
        delegates the calculation to the 'calculate_who_can_win' function.

        Args:
            ctx (context): The command context from the Discord bot.
        """
        await ctx.response.defer(thinking=True, ephemeral=False)
        year = datetime.now().year
        # Get the current drivers standings
        driver_standings = get_drivers_standings(year)

        # Get the maximum amount of points
        points = calculate_max_points_for_remaining_season()

        # Print which drivers can still win
        try:
            await ctx.followup.send(calculate_who_can_win(driver_standings, points))
        except Exception as error_message:
            await ctx.followup.send(error_message)
