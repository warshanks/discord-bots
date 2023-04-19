import discord
import openai
from elevenlabslib import *
from elevenlabslib.helpers import *
from discord import FFmpegOpusAudio
from discord.ext import commands
from config import *

# Set OpenAI API key and organization
openai.api_key = openai_token
openai.organization = openai_org

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

tts_user = ElevenLabsUser(elevenlabs_token)

premadeVoice: ElevenLabsVoice = tts_user.get_voices_by_name("Rachel")[0]


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

            previous_messages = [message async for message in message.channel.history(limit=10)]
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
                response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=conversation_log,
                    max_tokens=1024,
                    frequency_penalty=2.0
                )
            except Exception as e:
                await message.reply(e)

            tts_response = premadeVoice.generate_audio_bytes(response['choices'][0]['message']['content'])
            save_bytes_to_path("output.mp3", tts_response)

            # Send the generated text response as a reply
            await message.reply(response['choices'][0]['message']['content'])

            # Save the synthesized audio to a file
            with open("output.mp3", "wb") as out:
                out.write(tts_response)
                print('Audio content written to file "output.mp3"')
                tts_output = await FFmpegOpusAudio.from_probe("output.mp3")

            # Play the synthesized audio in the voice channel
            vc.play(tts_output)

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
