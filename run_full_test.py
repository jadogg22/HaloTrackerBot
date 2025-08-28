import os
import sys
import asyncio
from utils import match_cache
from utils import graph_generator
import config
import logging

# Configure logging for this script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MockUser:
    def __init__(self, user_id):
        self.id = user_id

class MockDMChannel:
    async def send(self, content=None, file=None):
        if content:
            logging.info(f"Mock Discord DM (text): {content}")
        if file:
            logging.info(f"Mock Discord DM (file): {file.filename} from {file.fp.name}")
            # In a real scenario, you might want to copy the file to a temp location
            # or just log its existence. For this test, logging the path is enough.

class MockBot:
    async def fetch_user(self, user_id):
        logging.info(f"Mock bot fetching user {user_id}")
        return MockUser(user_id)

    async def create_dm(self):
        logging.info("Mock bot creating DM channel")
        return MockDMChannel()

async def run_full_test():
    logging.info("Starting full test simulation...")

    # Ensure the database is initialized
    match_cache.init_db()

    # Mock the bot and user for simulating Discord interactions
    mock_bot = MockBot()
    mock_user = await mock_bot.fetch_user(config.USER_ID)
    mock_dm = await mock_user.create_dm()

    # Get recent match data (simulating the !report command's data fetching)
    recent_matches_raw = match_cache.get_recent_match_data(count=20)
    
    if not recent_matches_raw:
        logging.warning("No recent match data found in the database. Please ensure you have run the bot and it has scraped some matches.")
        logging.info("Test finished (no data).")
        return

    # Convert sqlite3.Row objects to dictionaries for graph_generator
    recent_matches = []
    for row in recent_matches_raw:
        match_dict = dict(row)
        # Ensure 'start_time' is a string for graph_generator's pd.to_datetime
        if isinstance(match_dict.get('start_time'), bytes):
            match_dict['start_time'] = match_dict['start_time'].decode('utf-8')
        recent_matches.append(match_dict)

    logging.info(f"Fetched {len(recent_matches)} recent matches for graph generation.")

    # Generate and "send" graphs
    generated_files = []

    # Generate CSR trend plot
    csr_plot_path = graph_generator.generate_csr_trend_plot(recent_matches, filename="simulated_csr_trend.png")
    if csr_plot_path:
        generated_files.append(csr_plot_path)
        await mock_dm.send(file=discord.File(csr_plot_path, filename="simulated_csr_trend.png"))
        logging.info(f"Simulated sending CSR trend plot: {csr_plot_path}")
    else:
        logging.warning("CSR trend plot not generated.")

    # Generate K/D plot
    kd_plot_path = graph_generator.generate_kd_plot(recent_matches, filename="simulated_kd_plot.png")
    if kd_plot_path:
        generated_files.append(kd_plot_path)
        await mock_dm.send(file=discord.File(kd_plot_path, filename="simulated_kd_plot.png"))
        logging.info(f"Simulated sending K/D plot: {kd_plot_path}")
    else:
        logging.warning("K/D plot not generated.")

    # Generate K/D Ratio plot
    kd_ratio_plot_path = graph_generator.generate_kd_ratio_plot(recent_matches, filename="simulated_kd_ratio_plot.png")
    if kd_ratio_plot_path:
        generated_files.append(kd_ratio_plot_path)
        await mock_dm.send(file=discord.File(kd_ratio_plot_path, filename="simulated_kd_ratio_plot.png"))
        logging.info(f"Simulated sending K/D Ratio plot: {kd_ratio_plot_path}")
    else:
        logging.warning("K/D Ratio plot not generated.")

    logging.info("Full test simulation complete.")
    logging.info("Generated plot files (check the 'plots' directory):")
    for f in generated_files:
        logging.info(f"- {f}")
    
    # Clean up generated plot files
    for f in generated_files:
        try:
            os.remove(f)
            logging.info(f"Cleaned up: {f}")
        except OSError as e:
            logging.error(f"Error cleaning up file {f}: {e}")

if __name__ == '__main__':
    # Add the project root to the Python path to ensure imports work
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Need to import discord for discord.File, even if mocked
    try:
        import discord
    except ImportError:
        logging.error("discord.py not found. Please install it: pip install discord.py")
        sys.exit(1)

    asyncio.run(run_full_test())
