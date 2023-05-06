"""
This module imports the necessary libraries for a Discord bot that interacts
with the OpenAI API to generate responses using the GPT-4 model. The bot can
process messages in specific channels and reply with generated content.

Libraries:
    - re: Used for regular expressions to split text and match patterns.
    - openai: Provides an interface to interact with the OpenAI API.
    - discord: A library for creating Discord bots and interacting with the Discord API.
    - discord.ext.commands: Provides a framework for creating commands for the Discord bot.
    - config: A custom module that contains configuration settings, such as API tokens,
              organization ID, and channel IDs for the Discord bot.
"""

import re
import openai
import discord
from discord.ext import commands
from config import openai_token, openai_org, channel_ids, gpt4_channel, lilith_channel


# Set OpenAI API key and organization
openai.api_key = openai_token
openai.organization = openai_org

bot = commands.Bot(command_prefix="~", intents=discord.Intents.all())


# Define an asynchronous function to generate a response
async def generate_response(message, conversation_log, openai_model):
    # Get the last 10 messages from the channel and reverse the order
    previous_messages = [msg async for msg in message.channel.history(limit=10)]
    previous_messages.reverse()

    # Iterate through the previous messages
    for previous_message in previous_messages:
        # Ignore any message that starts with '!'
        if not previous_message.content.startswith('!'):
            # Determine the role based on whether the
            # author of the message is a bot or not.
            # This lets the AI know which of the previous messages it sent
            # and which were sent by the user.
            role = 'assistant' if previous_message.author.bot else 'user'

            # Add log item to conversation_log
            conversation_log.append({
                'role': role,
                'content': previous_message.content
            })

    # Send the conversation log to OpenAI to generate a response
    try:
        response = await openai.ChatCompletion.acreate(
            model=openai_model,
            messages=conversation_log,
            max_tokens=1024,
        )
    except Exception as e:
        return e

    # Return the response content
    return response['choices'][0]['message']['content']


# Define an asynchronous function to send the response in sections
async def send_sectioned_response(message, response_content, max_length=2000):
    # Split the response_content into
    # sentences using regular expression
    # The regex pattern looks for sentence-ending punctuation
    # followed by a whitespace character
    sentences = re.split(r'(?<=[.!?])\s+', response_content)

    # Initialize an empty section
    section = ""

    # Iterate through the sentences
    for sentence in sentences:
        # If the current section plus the next sentence exceeds the max_length,
        # send the current section as a message and clear the section
        if len(section) + len(sentence) + 1 > max_length:
            await message.reply(section.strip())
            section = ""

        # Add the sentence to the section
        section += " " + sentence

    # If there's any content left in the section, send it as a message
    if section:
        await message.reply(section.strip())


# Define an asynchronous function to handle the conversation as KC
# noinspection PyShadowingNames
async def kc_conversation(message, openai_model):
    try:
        # Create a log of the user's message and the bot's response
        # send the typing animation while the bot is thinking
        async with message.channel.typing():
            conversation_log = [{'role': 'system',
                                 'content':
                                 'You are a friendly secretary named KC. '}]

            response_content = await generate_response(
                message,
                conversation_log,
                openai_model)
            await send_sectioned_response(message, response_content)
    except Exception as e:
        await message.reply(f"Error: {e} @Shanks#1955")


# noinspection PyShadowingNames
class GPT4Cog(commands.Cog):
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
                message.channel.id != gpt4_channel or
                message.content.startswith('!')):
            return

        # set the model to use
        openai_model = 'gpt-4'

        # Generate a response as KC
        await kc_conversation(message, openai_model)


# noinspection PyShadowingNames
class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Event handler for when a message is sent in a channel
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

        # set the model to use
        openai_model = 'gpt-3.5-turbo'

        # Generate a response as KC
        await kc_conversation(message, openai_model)

    # Hype emojipasta command
    @bot.tree.command(name='hype', description='Generate hype emojipasta')
    async def hype(self, ctx, about: str):
        # Defer the response to let the user know that the bot is working on the request
        await ctx.response.defer(thinking=True, ephemeral=False)
        conversation_log = [{'role': 'system', 'content': 'Generate really hype emojipasta about'},
                            {'role': 'user', 'content': about}]
        # Print information about the user, guild and channel where the command was invoked
        openai_model = 'gpt-3.5-turbo'
        try:
            # Generate a response using OpenAI API from the prompt provided by the user
            response = await openai.ChatCompletion.acreate(
                model=openai_model,
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
        openai_model = 'gpt-3.5-turbo'
        try:
            # Create a log of the user's message and the bot's response
            async with message.channel.typing():
                conversation_log = [{'role': 'system',
                                     'content':
                                     'Roleplay as Lilith, daughter of Hatred, '
                                     'from the Diablo universe.'}]

                response_content = await generate_response(message, conversation_log, openai_model)
                await message.reply(response_content)
        except Exception as e:
            await message.reply(f"Error: {e}")
