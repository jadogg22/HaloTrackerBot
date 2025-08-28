"""Main entry point for the Discord bot."""
import discord
from discord.ext import commands
import os
import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name}')

async def load_cogs():
    """
    Loads the functions I have written for the bot from the cogs directory.

    There is only one file for now but this is the discord recommended way to do it
    I guess. May further refactor the code and split it into multiple files later.
    """
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with bot:
        await load_cogs()
        await bot.start(config.DISCORD_TOKEN)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
