import pytest
import asyncio
import os
import json
from utils import scraper
from utils import match_cache
from utils import graph_generator
import config
import sqlite3

@pytest.mark.asyncio
async def test_full_flow():
    # 1. Fetch the last 20 matches
    print("Fetching last 20 matches...")
    matches = scraper.get_match_list(config.SPARTAN_TOKEN, count=20)
    assert matches is not None
    assert "Results" in matches
    print(f"Found {matches['Count']} matches")

    # 2. Process each match
    for i, match in enumerate(matches["Results"]):
        print(f"\n--- Processing Match {i+1} ---")
        match_id = match["MatchId"]

        # Fetch stats
        stats = scraper.get_match_stats(match_id, config.SPARTAN_TOKEN)
        if stats is None:
            print("Skipping match without stats")
            continue

        # Save match data
        match_cache.save_match_data(match, stats)

        # Fetch map and mode data
        map_variant = match["MatchInfo"]["MapVariant"]
        map_asset_id = map_variant["AssetId"]
        map_version_id = map_variant["VersionId"]
        map_data = match_cache.get_asset_from_db("maps", map_asset_id, map_version_id)
        if not map_data:
            map_data = scraper.fetch_ugc_asset(config.SPARTAN_TOKEN, "Maps", map_asset_id, map_version_id)
            if map_data:
                with match_cache.get_db_connection() as conn:
                    match_cache.upsert_asset(conn.cursor(), "maps", map_asset_id, map_version_id, map_data.get("PublicName"), map_data.get("Description"))
                    conn.commit()

        ugc_game_variant = match["MatchInfo"]["UgcGameVariant"]
        mode_asset_id = ugc_game_variant["AssetId"]
        mode_version_id = ugc_game_variant["VersionId"]
        mode_data = match_cache.get_asset_from_db("Modes", mode_asset_id, mode_version_id)
        if not mode_data:
            mode_data = scraper.fetch_ugc_asset(config.SPARTAN_TOKEN, "UgcGameVariants", mode_asset_id, mode_version_id)
            if mode_data:
                with match_cache.get_db_connection() as conn:
                    match_cache.upsert_asset(conn.cursor(), "Modes", mode_asset_id, mode_version_id, mode_data.get("PublicName"), mode_data.get("Description"))
                    conn.commit()

        # Print summary
        summary = scraper.format_match_summary(match, stats, mode_data, map_data)
        print(summary)

    # 3. Generate graphs
    print("\n--- Generating Graphs ---")
    recent_matches_raw = match_cache.get_recent_match_data(count=20)
    recent_matches = [dict(row) for row in recent_matches_raw]
    
    csr_plot_path = graph_generator.generate_csr_trend_plot(recent_matches)
    kd_plot_path = graph_generator.generate_kd_plot(recent_matches)
    kd_ratio_plot_path = graph_generator.generate_kd_ratio_plot(recent_matches)

    print(f"CSR Trend Plot: {csr_plot_path}")
    print(f"K/D Plot: {kd_plot_path}")
    print(f"K/D Ratio Plot: {kd_ratio_plot_path}")

    # Optional: Clean up the generated plots
    if csr_plot_path:
        os.remove(csr_plot_path)
    if kd_plot_path:
        os.remove(kd_plot_path)
    if kd_ratio_plot_path:
        os.remove(kd_ratio_plot_path)
