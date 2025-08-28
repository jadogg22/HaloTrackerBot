import discord
from discord.ext import commands
import asyncio
from utils import match_cache
from utils import scraper
import config
import sqlite3
import logging
from utils import graph_generator
import os
from datetime import datetime

class HaloWatcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.was_playing = False
        self.scraper_task = None
        self.spartan_token = config.SPARTAN_TOKEN
        

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f'Logged in as {self.bot.user.name}')
        guild = self.bot.get_guild(config.GUILD_ID)
        if guild:
            logging.info(f"✅ Connected to guild: {guild.name} ({guild.id})")
            try:
                member = await guild.fetch_member(config.USER_ID)
                logging.info(f"✅ Found user: {member.name} ({member.id})")
                activities = member.activities or []
                is_playing_halo = "Halo Infinite" in [a.name for a in activities]
                if is_playing_halo:
                    await self.handle_halo_started(member)
            except discord.NotFound:
                logging.error(f"❌ User with ID {config.USER_ID} not found in guild.")
        match_cache.init_db()
        await self.send_startup_dm()
        await self._check_db_vs_server_matches()

    async def _check_db_vs_server_matches(self):
        logging.info("Checking local DB against server for latest match...")
        db_latest_match = match_cache.Get_Latest_Match()
        
        # Fetch latest match from server
        server_matches = scraper.get_match_list(config.SPARTAN_TOKEN, count=3)
        logging.info("Fetched match list from server:")
        server_latest_match = None
        if server_matches and "Results" in server_matches and server_matches["Results"]:
            server_latest_match = server_matches["Results"][0]

        user = await self.bot.fetch_user(config.USER_ID)
        dm = await user.create_dm()

        if not db_latest_match and not server_latest_match:
            logging.info("No matches found in local DB or on server.")
            await dm.send("ℹ️ No matches found in your local database or on the Halo Waypoint server yet.")
        elif not db_latest_match and server_latest_match:
            logging.warning("Local DB is empty, but matches exist on server.")
            await dm.send("⚠️ Your local match database is empty, but recent matches were found on the server. The bot will start scraping new matches.")
        elif db_latest_match and not server_latest_match:
            logging.warning("No recent matches found on server, but local DB has data.")
            await dm.send("ℹ️ No recent matches found on the Halo Waypoint server, but your local database contains data.")
        elif db_latest_match["MatchId"] == server_latest_match["MatchId"]:
            logging.info("Local DB is up-to-date with the latest server match.")
            await dm.send("✅ Your local match database is up-to-date with the latest match on the server.")
        else:
            # Compare by start time to see if DB is truly behind or just a different latest match
            db_start_time = datetime.fromisoformat(db_latest_match["MatchInfo"]["StartTime"].replace("Z", "+00:00"))
            server_start_time = datetime.fromisoformat(server_latest_match["MatchInfo"]["StartTime"].replace("Z", "+00:00"))

            if server_start_time > db_start_time:
                logging.warning("Local DB is behind the latest server match.")
                await dm.send("🔄 Your local match database is behind the latest match on the server. The bot will catch up.")
            else:
                logging.info("Local DB has a more recent match than the latest found on server (possibly due to API caching or delays).")
                await dm.send("✅ Your local match database appears to be up-to-date or even more recent than the latest match currently reported by the server.")

    async def send_startup_dm(self):
        try:
            user = await self.bot.fetch_user(config.USER_ID)
            dm = await user.create_dm()
            await dm.send("Hi! Bot is online and watching your Halo activity 👋")
            logging.info("📬 Sent startup DM to user")
        except Exception as e:
            logging.error(f"❌ Failed to send startup DM: {e}")

    async def start_scraper(self):
        if self.scraper_task is None or self.scraper_task.done():
            self.scraper_task = asyncio.create_task(self.check_new_games_loop())
            logging.info("🟢 Started background scraper task.")

    async def stop_scraper(self):
        if self.scraper_task and not self.scraper_task.done():
            self.scraper_task.cancel()
            self.scraper_task = None
            logging.info("🛑 Stopped background scraper task.")

    async def handle_halo_started(self, member):
        self.was_playing = True
        logging.info(f"📢 {member.name} started playing Halo Infinite!")
        await self.start_scraper()

    async def handle_halo_stopped(self, member):
        self.was_playing = False
        logging.info(f"📢 {member.name} stopped playing Halo Infinite.")
        await self.stop_scraper()

        # Generate and send graphs
        recent_matches = match_cache.get_recent_match_data(count=10) # Get last 10 matches
        if recent_matches:
            user = await self.bot.fetch_user(config.USER_ID)
            dm = await user.create_dm()

            # Generate CSR trend plot
            csr_plot_path = graph_generator.generate_csr_trend_plot(recent_matches)
            if csr_plot_path:
                await dm.send(file=discord.File(csr_plot_path))
                os.remove(csr_plot_path) # Clean up the plot file

            # Generate K/D plot
            kd_plot_path = graph_generator.generate_kd_plot(recent_matches)
            if kd_plot_path:
                await dm.send(file=discord.File(kd_plot_path))
                os.remove(kd_plot_path) # Clean up the plot file

            # Generate K/D Ratio plot
            kd_ratio_plot_path = graph_generator.generate_kd_ratio_plot(recent_matches)
            if kd_ratio_plot_path:
                await dm.send(file=discord.File(kd_ratio_plot_path))
                os.remove(kd_ratio_plot_path) # Clean up the plot file

            logging.info("Sent match summary graphs to user.")

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        if after.id != config.USER_ID:
            return

        activities = after.activities or []
        is_playing_halo = "Halo Infinite" in [a.name for a in activities]

        if is_playing_halo and not self.was_playing:
            await self.handle_halo_started(after)
        elif not is_playing_halo and self.was_playing:
            await self.handle_halo_stopped(after)

    async def send_match_summary_report(self, match, stats, mode_data, map_data):
        try:
            user = await self.bot.fetch_user(config.USER_ID)
            dm = await user.create_dm()
            summary = scraper.format_match_summary(match, stats, mode_data, map_data)
            await dm.send(summary)
            logging.info("Sent Summary DM to user")
        except Exception as e:
            logging.error(f"❌ Failed to send summary DM: {e}")

    async def _handle_invalid_token(self):
        logging.error("❌ Invalid Spartan token detected. Stopping scraper and requesting new token.")
        await self.stop_scraper()

        user = await self.bot.fetch_user(config.USER_ID)
        dm = await user.create_dm()
        await dm.send(
            "Your Spartan token has expired or is invalid. Please set the SPARTAN_TOKEN "
            "environment variable with a new token and restart the bot. "
            "You can get a new token by going to https://www.halowaypoint.com/en-us/profile/settings, "
            "logging in, opening your browser's developer tools (F12), going to the Network tab, "
            "refresh the page, finding a request to `https://halostats.svc.halowaypoint.com/hi/players/xuid(...)`, "
            "and copying the `x-343-authorization-spartan` header value."
        )

        def check(message):
            return message.author.id == config.USER_ID and isinstance(message.channel, discord.DMChannel)

        try:
            await dm.send("Please restart the bot after setting the new token.")
        except Exception as e:
            logging.error(f"❌ Error sending restart message: {e}")

    async def _get_or_fetch_asset_data(self, asset_type, asset_id, version_id):
        asset_data = match_cache.get_asset_from_db(asset_type, asset_id, version_id)
        if not asset_data:
            asset_data = scraper.fetch_ugc_asset(self.spartan_token, asset_type, asset_id, version_id)
            if asset_data:
                conn = sqlite3.connect(match_cache.DB_FILE)
                cursor = conn.cursor()
                match_cache.upsert_asset(cursor, asset_type, asset_id, version_id, asset_data.get("PublicName"), asset_data.get("Description"))
                conn.commit()
                conn.close()
        return asset_data

    async def _process_new_match(self, match):


        stats = scraper.get_match_stats(match["MatchId"], self.spartan_token)
        if stats is False: # Invalid token
            await self._handle_invalid_token()
            return
        if stats:
            match_cache.save_match_data(match, stats)

            # Get game mode info
            ugc_game_variant = match["MatchInfo"]["UgcGameVariant"]
            mode_asset_id = ugc_game_variant["AssetId"]
            mode_version_id = ugc_game_variant["VersionId"]
            mode_data = await self._get_or_fetch_asset_data("Modes", mode_asset_id, mode_version_id)

            # Get map info
            map_variant = match["MatchInfo"]["MapVariant"]
            map_asset_id = map_variant["AssetId"]
            map_version_id = map_variant["VersionId"]
            map_data = await self._get_or_fetch_asset_data("maps", map_asset_id, map_version_id)

            await self.send_match_summary_report(match, stats, mode_data, map_data)

    async def check_new_games_loop(self):
        while True:
            await self.check_for_new_matches()
            await asyncio.sleep(60)

    async def check_for_new_matches(self):
        """
        Checks the api for any new matches since the last known match in the database.

        first checks database and sees what the latest match we know about is.
        Then scrapes the api for any new match since that match. If any are found,
        it processes them one by one, saving to the database and sending a summary DM for each.
        """
        db_latest_match = match_cache.Get_Latest_Match()
        if db_latest_match:
            logging.info(f"🗄️ Latest match in DB: {db_latest_match['MatchId']} from {db_latest_match['MatchInfo']['StartTime']}")
        else:
            logging.info("🗄️ No matches in DB yet.")

        new_matches = scraper.get_new_matches(db_latest_match['MatchId'] if db_latest_match else "", self.spartan_token)

        if new_matches is False: # Invalid token
            await self._handle_invalid_token()
            return

        if new_matches:
            logging.info(f"✅ Found {len(new_matches)} new match(es). Processing...")
            for match in new_matches:
                await self._process_new_match(match)
                db_latest_match = match
        else:
            logging.info("ℹ️ No new matches found.")

    @commands.command()
    async def refresh(self, ctx):
        """
        Manually triggers a check for new Halo Infinite matches.

        this function is called once the user sends the !refresh command in Discord.
        We then just make the necessary calls to check for new matches and send summaries if found.
        """
        await ctx.send("Manually refreshing match data...")
        await self.check_for_new_matches()
        await ctx.send("Refresh complete.")

    @commands.command()
    async def report(self, ctx):
        """
        Manually generates and sends the after-action report graphs to the user.

        This function is called once the user sends the !report command in Discord.
        It then calcculates and generates the graphs based on recent match data and sends them via DM.
        """
        await ctx.send("Generating report...")
        recent_matches_raw = match_cache.get_recent_match_data(session_only=True)
        
        if len(recent_matches_raw) < 3:
            await ctx.send("⚠️ Your current session has fewer than 3 matches. Generating report for the last 20 matches instead.")
            recent_matches_raw = match_cache.get_recent_match_data(count=20)

        if recent_matches_raw:
            recent_matches = [dict(row) for row in recent_matches_raw]
            user = await self.bot.fetch_user(config.USER_ID)
            dm = await user.create_dm()

            # Generate CSR trend plot
            csr_plot_path = graph_generator.generate_csr_trend_plot(recent_matches)
            if csr_plot_path:
                await dm.send(file=discord.File(csr_plot_path))
                os.remove(csr_plot_path) # Clean up the plot file

            # Generate K/D plot
            kd_plot_path = graph_generator.generate_kd_plot(recent_matches)
            if kd_plot_path:
                await dm.send(file=discord.File(kd_plot_path))
                os.remove(kd_plot_path) # Clean up the plot file

            # Generate K/D Ratio plot
            kd_ratio_plot_path = graph_generator.generate_kd_ratio_plot(recent_matches)
            if kd_ratio_plot_path:
                await dm.send(file=discord.File(kd_ratio_plot_path))
                os.remove(kd_ratio_plot_path) # Clean up the plot file

            logging.info("Sent after-action report graphs to user.")
            await ctx.send("Report sent!")
        else:
            await ctx.send("Could not generate report: No match data found.")
            logging.warning("Could not generate after-action report: No match data found.")

async def setup(bot):
    await bot.add_cog(HaloWatcher(bot))
