import pytest
import asyncio
import sqlite3
import os
from utils.scraper import get_match_list, get_match_stats
from utils.match_cache import DB_FILE, init_db, save_match_data, Get_Latest_Match
import config

@pytest.fixture(scope="module")
def db_connection():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_db()
    conn = sqlite3.connect(DB_FILE)
    yield conn
    conn.close()

@pytest.mark.asyncio
async def test_scrape_and_store_last_5_matches(db_connection):
    # Get latest match in DB (if any)
    db_latest_match = Get_Latest_Match()
    assert db_latest_match is None # Should be empty after db_connection fixture

    # Scrape last 5 matches
    matches = get_match_list(config.SPARTAN_TOKEN, count=5)
    assert matches is not None
    assert "Results" in matches
    assert len(matches["Results"]) > 0

    new_matches_added = []
    for match in matches.get("Results", []):
        match_id = match["MatchId"]

        # Check DB for this match
        c = db_connection.cursor()
        c.execute("SELECT 1 FROM matches WHERE match_id = ?", (match_id,))
        exists = c.fetchone()

        if not exists:
            stats = get_match_stats(match_id, config.SPARTAN_TOKEN)
            if stats is not None:
                assert "Value" in stats
                assert len(stats["Value"]) > 0
                assert "Result" in stats["Value"][0]
                save_match_data(match, stats)
                new_matches_added.append(match_id)

    assert len(new_matches_added) > 0 # At least one new match should be added

    # Verify latest match in DB
    latest_in_db = Get_Latest_Match()
    assert latest_in_db is not None
    assert latest_in_db["MatchId"] in [m["MatchId"] for m in matches["Results"]]
