import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os

import discord
from discord.ext import commands
from cogs.halo_watcher import HaloWatcher
from utils import match_cache
from utils import scraper
import config
from utils import graph_generator

@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.fetch_user.return_value = AsyncMock(spec=discord.User)
    bot.fetch_user.return_value.create_dm.return_value = AsyncMock(spec=discord.DMChannel)
    return bot

@pytest.fixture(autouse=True)
def mock_os_remove():
    with patch('os.remove') as mock_remove:
        yield mock_remove

@pytest.fixture(autouse=True)
def mock_graph_generator():
    with patch('graph_generator.generate_csr_trend_plot', return_value='csr_plot.png') as mock_csr:
        with patch('graph_generator.generate_kd_plot', return_value='kd_plot.png') as mock_kd:
            with patch('graph_generator.generate_kd_ratio_plot', return_value='kd_ratio_plot.png') as mock_kd_ratio:
                yield mock_csr, mock_kd, mock_kd_ratio

@pytest.mark.asyncio
async def test_report_command(mock_bot, mock_os_remove, mock_graph_generator):
    # Ensure the database has some data for the report
    # For this test, we'll rely on previous tests populating the DB or a manual run.
    # In a real scenario, you might use a fixture to insert test data.
    
    # Mock match_cache.get_recent_match_data to return some data
    with patch('match_cache.get_recent_match_data') as mock_get_recent_match_data:
        mock_get_recent_match_data.return_value = [
            # Sample match data (simplified)
            {"match_id": "match1", "start_time": "2023-01-01T10:00:00Z", "post_csr": 1500, "kills": 10, "deaths": 5},
            {"match_id": "match2", "start_time": "2023-01-01T11:00:00Z", "post_csr": 1510, "kills": 12, "deaths": 6},
        ]

        cog = HaloWatcher(mock_bot)
        ctx = AsyncMock(spec=commands.Context)
        ctx.send = AsyncMock()

        await cog.report(ctx)

        # Assert that ctx.send was called with the initial message
        ctx.send.assert_called_once_with("Generating after-action report...")

        # Assert that get_recent_match_data was called
        mock_get_recent_match_data.assert_called_once_with(count=20)

        # Assert that graph generation functions were called
        mock_graph_generator[0].assert_called_once() # generate_csr_trend_plot
        mock_graph_generator[1].assert_called_once() # generate_kd_plot
        mock_graph_generator[2].assert_called_once() # generate_kd_ratio_plot

        # Assert that DM was sent with files
        dm_channel = mock_bot.fetch_user.return_value.create_dm.return_value
        assert dm_channel.send.call_count == 3 # One for each plot
        dm_channel.send.assert_any_call(file=discord.File('csr_plot.png'))
        dm_channel.send.assert_any_call(file=discord.File('kd_plot.png'))
        dm_channel.send.assert_any_call(file=discord.File('kd_ratio_plot.png'))

        # Assert that os.remove was called for each plot file
        assert mock_os_remove.call_count == 3
        mock_os_remove.assert_any_call('csr_plot.png')
        mock_os_remove.assert_any_call('kd_plot.png')
        mock_os_remove.assert_any_call('kd_ratio_plot.png')

        # Assert final message was sent
        ctx.send.assert_called_with("After-action report sent!")

@pytest.mark.asyncio
async def test_report_command_no_data(mock_bot):
    with patch('match_cache.get_recent_match_data', return_value=[]) as mock_get_recent_match_data:
        cog = HaloWatcher(mock_bot)
        ctx = AsyncMock(spec=commands.Context)
        ctx.send = AsyncMock()

        await cog.report(ctx)

        ctx.send.assert_called_once_with("Generating after-action report...")
        ctx.send.assert_called_with("Could not generate report: No match data found.")
        mock_get_recent_match_data.assert_called_once_with(count=20)