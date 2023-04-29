import asyncio
from concurrent.futures import ThreadPoolExecutor
from os import makedirs
import discord
import elevenlabslib.helpers
import openai
from elevenlabslib import *
from discord import FFmpegOpusAudio
from discord.ext import commands
from config import openai_token, openai_org, elevenlabs_token, vcs

makedirs("../speech", exist_ok=True)

# Set OpenAI API key and organization
openai.api_key = openai_token
openai.organization = openai_org

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

tts_user = ElevenLabsUser(elevenlabs_token)

premadeVoice: ElevenLabsVoice = tts_user.get_voices_by_name("Rachel")[0]


async def run_blocking(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, lambda: func(*args, **kwargs))


def write_audio_to_file(filename, tts_response):
    with open(filename, "wb") as out:
        out.write(tts_response)


# noinspection PyShadowingNames
class TTSCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.vc = None

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself,
        # from the system user,
        # or from channels other than the designated one,
        # or that start with '!'
        if (message.author.bot or
                message.author.system or
                message.channel.id not in vcs or
                message.content.startswith('!')):
            return

        # Create a log of the user's message and the bot's response
        async with message.channel.typing():
            conversation_log = [{'role': 'system', 'content':
                                 'You are a friendly secretary named KC. '
                                 'Only respond to the latest message.'}]

            previous_messages = [message async for message in message.channel.history(limit=5)]
            previous_messages.reverse()

            for previous_message in previous_messages:
                # Ignore any message that starts with '!'
                if not previous_message.content.startswith('!'):
                    # Determine the role based on whether the author of the message is a bot or not
                    role = 'assistant' if previous_message.author.bot else 'user'

                    # Add log item to conversation_log
                    conversation_log.append({
                        'role': role,
                        'content': previous_message.content
                    })

            # Send the conversation log to OpenAI to generate a response
            try:
                response = await openai.ChatCompletion.acreate(
                    model='gpt-3.5-turbo',
                    messages=conversation_log,
                    max_tokens=1024,
                    frequency_penalty=2.0
                )
            except Exception as e:
                await message.reply(e)

            try:
                tts_response = premadeVoice.generate_audio_bytes(response['choices'][0]['message']['content'])
                elevenlabslib.helpers.save_audio_bytes(tts_response, "../speech/output.mp3", "mp3")

                # Send the generated text response as a reply
                await message.reply(response['choices'][0]['message']['content'])

                # Save the synthesized audio to a file
                await run_blocking(write_audio_to_file, "../speech/output.mp3", tts_response)
                print('Audio content written to file "../speech/output.mp3"')
                tts_output = await FFmpegOpusAudio.from_probe("../speech/output.mp3")

                # Play the synthesized audio in the voice channel
                vc.play(tts_output)
            except Exception as e:
                await message.reply(e)

    @bot.tree.command(name='join', description='Join the voice channel')
    async def join(self, ctx):
        global vc
        # Defer the response to let the user know that the bot is working on the request
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True, ephemeral=True)
        voice_channel = ctx.user.voice.channel
        vc = await voice_channel.connect()
        await ctx.followup.send("Joined!", ephemeral=True)

    @bot.tree.command(name='tts-kick', description='Leave the voice channel')
    async def tts_kick(self, ctx):
        await ctx.response.defer(thinking=True, ephemeral=True)
        await vc.disconnect()
        await ctx.followup.send("Left!", ephemeral=True)
