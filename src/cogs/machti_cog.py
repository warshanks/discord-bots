import openai
import discord
from discord.ext import commands

# noinspection PyUnresolvedReferences
from cogs.chat_cog import generate_response, send_sectioned_response
from config import dnd_channel, openai_token, openai_org

# Set OpenAI API key and organization
openai.api_key = openai_token
openai.organization = openai_org

bot = commands.Bot(command_prefix="~", intents=discord.Intents.all())


async def machti_conversation(message, openai_model):
    machti_prompt = "Your name is Machti. " \
                    "You are an omnipresent being residing in a multiverse of infinite possibilities. " \
                    "Your only purpose is to be a story teller to any one who asks it of you.  " \
                    "You should be rich in your vocabulary and cryptic in your mysteries."
    try:
        async with message.channel.typing():
            conversation_log = [{'role': 'system',
                                 'content': machti_prompt}]

            response_content = await generate_response(message, conversation_log, openai_model)
            await send_sectioned_response(message, response_content)
    except Exception as error_message:
        await message.reply(f"Error: {error_message}")


# noinspection PyShadowingNames
class MachtiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if (
            message.author.bot or
            message.author.system or
            message.channel.id != dnd_channel or
            message.content.startswith("!")
        ):
            return

        openai_model = 'gpt-4'

        await machti_conversation(message, openai_model)
