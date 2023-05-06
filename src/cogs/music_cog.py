import discord
from discord.ext import commands
from youtube_dl import YoutubeDL
from re import match

bot = commands.Bot(command_prefix="~", intents=discord.Intents.all())


# noinspection PyShadowingNames
class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # all the music related stuff
        self.is_playing = False
        self.is_paused = False

        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}

        self.vc = None

    def search_yt(self, item):
        # Check if the input is a YouTube URL
        def is_youtube_url(item):
            url_regex = (
                r'(?:https?://)?(?:www\.|m\.)?'
                r'(?:youtube\.com|youtu.be)/'
                r'(?:(?:watch)|(?:embed))?(?:(?=\\S*[?&]v=)|\/)([a-zA-Z0-9_-]{11})+')
            return match(url_regex, item) is not None

        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            if is_youtube_url(item):
                info = ydl.extract_info(item, download=False)
            else:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            # get the first url
            m_url = self.music_queue[0][0]['source']

            # remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    # infinite loop checking
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            # try to connect to voice channel if you are not already connected
            if self.vc is None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                # in case we fail to connect
                if self.vc is None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            # remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    @bot.tree.command(name="play", description="Plays a selected song from youtube")
    async def play(self, ctx, search: str):
        await ctx.response.defer(thinking=True)

        try:
            voice_channel = ctx.user.voice.channel
        except AttributeError:
            # you need to be connected so that the bot knows where to go
            await ctx.followup.send("Connect to a voice channel!")
            return

        if self.is_paused:
            self.vc.resume()

        else:
            song = self.search_yt(search)
            if isinstance(song, bool):
                await ctx.followup.send(
                    "Could not download the song. Incorrect format, try again. "
                    "Make sure not to use links from playlists or livestreams!")
            else:
                await ctx.followup.send("Song added to the queue")
                self.music_queue.append([song, voice_channel])

                if not self.is_playing:
                    await self.play_music(ctx)

    @bot.tree.command(name="pause", description="Pauses the current song being played")
    async def pause(self, ctx):
        await ctx.response.defer(thinking=True, ephemeral=True)
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
        await ctx.followup.send("Music paused!", ephemeral=True)

    @bot.tree.command(name="resume", description="Resumes playback of the current song")
    async def resume(self, ctx):
        await ctx.response.defer(thinking=True, ephemeral=True)
        if self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()
            await ctx.followup.send("Music resumed!", ephemeral=True)

    @bot.tree.command(name="skip", description="Skips the current song")
    async def skip(self, ctx):
        await ctx.response.defer(thinking=True)
        if self.vc is not None and self.vc:
            self.vc.stop()
            # try to play next in the queue if it exists
            await self.play_music(ctx)
        await ctx.followup.send("Song skipped!")

    @bot.tree.command(name="queue", description="Displays the current songs in queue")
    async def queue(self, ctx):
        await ctx.response.defer(thinking=True)
        retval = ""
        for i in range(0, len(self.music_queue)):
            # display a max of 5 songs in the current queue
            if i > 4:
                break
            retval += self.music_queue[i][0]['title'] + "\n"

        if retval != "":
            await ctx.followup.send(retval)
        else:
            await ctx.followup.send("No music in queue!")

    @bot.tree.command(name="clear", description="Stops playback and clears the queue")
    async def clear(self, ctx):
        await ctx.response.defer(thinking=True)
        if self.vc is not None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.followup.send("Music queue cleared!")

    @bot.tree.command(name="leave", description="Kick KC from VC")
    async def dc(self, ctx):
        await ctx.response.defer(thinking=True, ephemeral=True)
        self.is_playing = False
        self.is_paused = False

        try:
            await self.vc.disconnect()
            await ctx.followup.send("Left the voice channel!")
        except AttributeError:
            await ctx.followup.send("I'm not in a voice channel! (Try /tts-kick)")
