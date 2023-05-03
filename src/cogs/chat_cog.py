import openai
import discord
from discord.ext import commands
from config import *

# Set OpenAI API key and organization
openai.api_key = openai_token
openai.organization = openai_org

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


async def generate_response(message, conversation_log):
    previous_messages = [msg async for msg in message.channel.history(limit=10)]
    previous_messages.reverse()

    for previous_message in previous_messages:
        # Ignore any message that starts with '!'
        if not previous_message.content.startswith('!'):
            # Determine the role based on whether the
            # author of the message is a bot or not
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
        return str(e)

    # Return the response content
    try:
        return response['choices'][0]['message']['content']
    except discord.errors.HTTPException:
        return "I have too much to say, please try again."


# noinspection PyShadowingNames
class ChatCog(commands.Cog):
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
                message.channel.id not in channel_ids or
                message.content.startswith('!')):
            return

        # Create a log of the user's message and the bot's response
        async with message.channel.typing():
            conversation_log = [{'role': 'system', 'content':
                                 'You are a friendly secretary named KC. '
                                 'Only respond to the latest message.'}]

            response_content = await generate_response(message, conversation_log)
            await message.reply(response_content)

    # Hype emojipasta command
    @bot.tree.command(name='hype', description='Generate hype emojipasta')
    async def hype(self, ctx, about: str):
        # Defer the response to let the user know that the bot is working on the request
        # noinspection PyUnresolvedReferences
        await ctx.response.defer(thinking=True, ephemeral=False)
        conversation_log = [{'role': 'system', 'content': 'Generate really hype emojipasta about'},
                            {'role': 'user', 'content': about}]
        # Print information about the user, guild and channel where the command was invoked
        print(ctx.user, ctx.guild, ctx.channel, about)
        try:
            # Generate a response using OpenAI API from the prompt provided by the user
            response = await openai.ChatCompletion.acreate(
                model='gpt-3.5-turbo',
                messages=conversation_log,
                frequency_penalty=2.0,
                max_tokens=1024,
            )
            await ctx.followup.send(response['choices'][0]['message']['content'])
        except discord.errors.HTTPException:
            await ctx.followup.send("I have too much to say, please try again.")


# noinspection PyShadowingNames
class LilithCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Event handler for when the bot receives a message
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself,
        # or from channels other than the designated one,
        # or that start with '!'
        if (message.author.bot or
                message.author.system or
                message.channel.id != lilith_channel or
                message.content.startswith('!')):
            return

        # Create a log of the user's message and the bot's response
        async with message.channel.typing():
            conversation_log = [{'role': 'system', 'content':
                                'Roleplay as Lilith, daughter of Hatred, from the Diablo universe.'}]

            response_content = await generate_response(message, conversation_log)
            await message.reply(response_content)
