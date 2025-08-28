import discord
import os
import asyncio
import datetime
import logging

# Assuming these are in the same directory or accessible via PYTHONPATH
import config
from utils import graph_generator
from utils import scraper # Added import for scraper

# Configure logging for this script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Discord client with intents
intents = discord.Intents.default()
intents.message_content = True # Required for message content
intents.presences = True # Required for presence updates (if needed, though not directly used in this mock)
intents.members = True # Required for fetching members (if needed)
bot = discord.Client(intents=intents)

# Dummy data for single match summary
dummy_match = {
    "MatchId": "mock_match_12345",
    "MatchInfo": {
        "StartTime": "2025-08-26T20:00:00Z",
        "EndTime": "2025-08-26T20:15:00Z",
        "Duration": 900,
        "Playlist": {"AssetId": "mock_playlist_id"},
        "MapVariant": {"AssetId": "mock_map_variant_id", "VersionId": "mock_map_version_id"},
        "UgcGameVariant": {"AssetId": "mock_ugc_game_variant_id", "VersionId": "mock_ugc_game_version_id"}
    },
    "Outcome": 2, # 2 for Win
    "Rank": 1
}

dummy_stats = {
    "Value": [
        {
            "Result": {
                "RankRecap": {
                    "PreMatchCsr": {"Value": 1500},
                    "PostMatchCsr": {"Value": 1515}
                },
                "TeamMmr": 1505.50,
                "TeamMmrs": {
                    "team_a": 1500.00,
                    "team_b": 1510.00
                },
                "StatPerformances": {
                    "Kills": {"Count": 15, "Expected": 12.5},
                    "Deaths": {"Count": 7, "Expected": 8.0}
                }
            }
        }
    ]
}

dummy_mode_data = {"name": "Slayer", "description": "Eliminate the enemy team to score points."}
dummy_map_data = {"name": "Live Fire"}


async def send_mock_single_match_report():
    logging.info("Attempting to send mock single match report...")
    try:
        user = await bot.fetch_user(config.USER_ID)
        dm = await user.create_dm()
        logging.info(f"Opened DM channel with {user.name}")

        summary = scraper.format_match_summary(
            dummy_match,
            dummy_stats,
            dummy_mode_data,
            dummy_map_data
        )
        await dm.send(summary)
        logging.info("Mock single match summary sent to user.")

    except discord.errors.NotFound:
        logging.error(f"User with ID {config.USER_ID} not found. Cannot send DM for single match report.")
    except Exception as e:
        logging.error(f"Failed to send mock single match report: {e}")

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logging.info('Bot is ready. Initiating mock single match report send...')
    # Give Discord a moment to fully connect and cache
    await asyncio.sleep(2)
    await send_mock_single_match_report()
    # After sending the report, we can gracefully shut down the bot
    logging.info("Mock single match report sent. Shutting down bot.")
    await bot.close()

if __name__ == "__main__":
    try:
        bot.run(config.DISCORD_TOKEN)
    except discord.LoginFailure:
        logging.error("Invalid Discord token. Please check your DISCORD_TOKEN in config.py.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
