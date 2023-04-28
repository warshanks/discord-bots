import datetime
import io
import os

import openai
import discord
from discord.ext import commands
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

from config import *

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Set OpenAI API key and organization
openai.api_key = openai_token
openai.organization = openai_org

os.environ['STABILITY_HOST'] = stability_host
os.environ['STABILITY_API_KEY'] = stability_token

# Set up our connection to the API.
stability_api = client.StabilityInference(
    key=stability_token,  # API Key reference.
    verbose=True,  # Print debug messages.
    engine="stable-diffusion-xl-beta-v2-2-2"
)


# noinspection PyShadowingNames
class ImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Define a slash command that sends a prompt for image generation to OpenAI
    @bot.tree.command(name='dall-e',
                      description="Generate an image from a prompt using "
                                  "OpenAI's Dall-e model")
    async def generate_image_dalle(self, ctx, img_prompt: str):
        # Defer the response to let the user know that the bot is working on the request
        await ctx.response.defer(thinking=True, ephemeral=False)
        # Print information about the user, guild and channel where the command was invoked
        print(ctx.user, ctx.guild, ctx.channel, img_prompt)
        try:
            # Generate an image using OpenAI API from the prompt provided by the user
            response = await openai.Image.acreate(
                prompt=img_prompt,
                size='1024x1024',
                n=1
            )
            img_url = response['data'][0]['url']
            # Send the generated image URL back to the user
            await ctx.followup.send(f'{img_url}\n"{img_prompt}" '
                                    f'by KC & {ctx.user} '
                                    f'c. {datetime.datetime.now().year}')
        except Exception as e:
            await ctx.followup.send(e)

    # Define a slash command that sends a prompt for image generation to Stability.AI
    @bot.tree.command(name='stable',
                      description="Generate an image from a prompt using "
                                  "Stability.AI's Stable Diffusion model")
    async def generate_image_stable(self, ctx, img_prompt: str, img_seed: int = None,
                                    img_steps: int = 30, cfg_mod: float = 8.0,
                                    img_width: int = 512, img_height: int = 512):
        # Defer the response while the bot processes the image generation request
        await ctx.response.defer(thinking=True, ephemeral=False)

        # Set up the initial image generation parameters using the provided arguments
        answers = stability_api.generate(
            prompt=img_prompt,
            seed=img_seed,
            steps=img_steps,
            cfg_scale=cfg_mod,
            width=img_width,
            height=img_height,
            samples=1,
            sampler=generation.SAMPLER_K_DPMPP_2M
        )

        # If the adult content classifier is not triggered, send the generated images
        try:
            # Iterate through the answers from the image generation API
            for resp in answers:
                # Iterate through the artifacts in each answer
                for artifact in resp.artifacts:
                    # If the artifact's finish_reason is FILTER,
                    # the API's safety filters have been activated
                    if artifact.finish_reason == generation.FILTER:
                        ctx.followup.send(
                            "Your request activated the API's safety filters "
                            "and could not be processed. "
                            "Please modify the prompt and try again.")
                    # If the artifact's type is an image, send the generated image
                    if artifact.type == generation.ARTIFACT_IMAGE:
                        # Convert the binary artifact into an in-memory binary stream
                        img = io.BytesIO(artifact.binary)
                        img.seek(0)  # Set the stream position to the beginning
                        # Send the generated image as a follow-up message in the chat
                        await ctx.followup.send(content=f'"{img_prompt}" by KC & {ctx.user} '
                                                        f'c.{datetime.datetime.now().year}\n'
                                                        f'Seed: {artifact.seed}',
                                                file=discord.File(fp=img,
                                                                  filename=str(artifact.seed)
                                                                  + ".png"))
        # Catch any exceptions and send an ephemeral message with the error
        except Exception as e:
            await ctx.followup.send(e, ephemeral=True)
