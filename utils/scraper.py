"""Handles all interactions with the Halo Waypoint API for fetching match and asset data."""
import requests
import json
from datetime import datetime
import config
import logging
import isodate

PLAYER_XUID = config.PLAYER_XUID


class InvalidTokenError(Exception):
    """Custom exception for invalid API tokens."""
    pass


def halo_request(url, token):
    """
    Makes a GET request to the Halo Waypoint API.

    Args:
        url (str): The URL to make the request to.
        token (str): The Spartan API token for authentication.

    Returns:
        dict or None: The JSON response from the API, or None if an error occurred.

    Raises:
        InvalidTokenError: If the API token is invalid (HTTP 401).
    """
    headers = {
        "accept": "application/json",
        "x-343-authorization-spartan": token,
        "user-agent": "python-requests",
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            status = e.response.status_code
            logging.error(f"[HTTPError] {status} for {url}")
            logging.error(f"Response content: {e.response.text}")
            if status == 401:
                raise InvalidTokenError("Invalid API token")
        else:
            logging.error(f"[HTTPError] Unknown error for {url}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"[RequestException] {e} for {url}")
        return None
    except Exception as e:
        logging.error(f"[Error] {e} for {url}")
    return None

def get_match_list(token, count=5):
    """
    Fetches a list of recent matches for the configured player.

    Args:
        token (str): The Spartan API token.
        count (int): The number of matches to retrieve.

    Returns:
        dict or None: A dictionary containing the match list, or None if an error occurred.
    """
    url = f"https://halostats.svc.halowaypoint.com/hi/players/xuid({PLAYER_XUID})/matches?count={count}&type=All"
    return halo_request(url, token)


def fetch_ugc_asset(token: str, asset_type: str, asset_id: str, version_id: str) -> dict:
    """
    Fetches UGC (User Generated Content) asset data (e.g., maps, game variants).

    Args:
        token (str): The Spartan API token.
        asset_type (str): The type of asset (e.g., "Maps", "UgcGameVariants").
        asset_id (str): The unique ID of the asset.
        version_id (str): The version ID of the asset.

    Returns:
        dict: A dictionary containing the asset data.
    """
    url = f"https://discovery-infiniteugc.svc.halowaypoint.com/hi/{asset_type}/{asset_id}/versions/{version_id}"
    
    headers = {
        "343-clearance": "ff0701e7-732d-476a-bded-2ff50cf7320e",  # keep this as-is for now
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US",
        "cache-control": "no-cache",
        "origin": "https://www.halowaypoint.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://www.halowaypoint.com/",
        "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
         "x-343-authorization-spartan": token,
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"❌ Failed to fetch {asset_type} asset {asset_id}: {e}")
        return {}


def get_new_matches(old_match_id: str, token: str) -> list[dict]:
    """
    Fetches new matches that are more recent than a given old match ID.

    Args:
        old_match_id (str): The ID of the last known match.
        token (str): The Spartan API token.

    Returns:
        list[dict]: A list of new match dictionaries.
    """
    try:
        response = get_match_list(token, count=5)
    except InvalidTokenError:
        logging.error("API token is invalid. Please update your token.")
        return []

    logging.debug("Fetched match list:")
    logging.debug(json.dumps(response, indent=2))
    if response is None or "Results" not in response:
        logging.warning("⚠️ Could not fetch match list or no matches found")
        return []

    # create an array of match info
    matches = response["Results"]

    # extract just the match IDs
    match_ids = [match["MatchId"] for match in matches]

    # if old match exists, grab its StartTime
    if old_match_id in match_ids:
        old_match = next(m for m in matches if m["MatchId"] == old_match_id)
        old_start_time = old_match["MatchInfo"]["StartTime"]

        # filter matches that are newer than the old one
        new_matches = [
            m for m in matches
            if m["MatchInfo"]["StartTime"] > old_start_time
        ]
        return new_matches
    
    # if old match isn't in the recent 5, just return them all
    return matches

def get_match_stats(match_id, token):
    """
    Fetches detailed statistics for a specific match.

    Args:
        match_id (str): The ID of the match.
        token (str): The Spartan API token.

    Returns:
        dict or None: A dictionary containing match statistics, or None if not found or an error occurred.
    """
    url = f"https://skill.svc.halowaypoint.com/hi/matches/{match_id}/skill?players=xuid({PLAYER_XUID})"
    response = halo_request(url, token)
    if response and "Value" in response and response["Value"] and "Result" in response["Value"][0] and "RankRecap" in response["Value"][0]["Result"]:
        return response
    return None

def format_time(iso):
    """
    Formats an ISO 8601 timestamp string into a more readable format.

    Args:
        iso (str): The ISO 8601 timestamp string.

    Returns:
        str: Formatted datetime string or the original string if parsing fails.
    """
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        # Example: Aug 26, 2025 09:00 PM
        return dt.strftime("%b %d, %Y %I:%M %p")
    except:
        return iso

def parse_duration(iso_duration):
    """
    Parses an ISO 8601 duration string into total seconds.

    Args:
        iso_duration (str): The ISO 8601 duration string (e.g., "PT8M33.6347133S").

    Returns:
        float: The total duration in seconds.
    """
    return isodate.parse_duration(iso_duration).total_seconds()

def format_duration(seconds):
    """
    Formats a duration in seconds into a human-readable string (e.g., "8m 33s").

    Args:
        seconds (float): The duration in seconds.

    Returns:
        str: Formatted duration string.
    """
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}m {int(seconds)}s"

def outcome_str(code):
    """
    Converts a numerical outcome code into a descriptive string.

    Args:
        code (int): The outcome code (1: Tie, 2: Win, 3: Loss).

    Returns:
        str: The descriptive outcome string.
    """
    return {1: "Tie", 2: "Win", 3: "Loss"}.get(code, f"Unknown({code})")



def format_match_summary(match, stats, mode_data, map_data) -> str:
    """
    Build a nicely formatted text summary of a match + stats.
    Returns a single string.
    """
    lines = []

    match_id = match["MatchId"]
    info = match["MatchInfo"]

    start = format_time(info["StartTime"])
    end = format_time(info["EndTime"])
    duration_seconds = parse_duration(info.get("Duration", "PT0S"))

    outcome = match.get("Outcome", "N/A")
    rank = match.get("Rank", "N/A")

    lines.append(f"🎮 **Match Summary**")
    lines.append(f"Match ID: `{match_id}`")
    lines.append(f"🕒 Start: {start}   End: {end}   Duration: {format_duration(duration_seconds)}")
    lines.append(f"🏆 Outcome: {outcome_str(outcome)}   📈 Rank: {rank}")
    lines.append("")

    # Playlist / Map info
    if map_data:
        lines.append(f"🗺️ Map: {map_data.get('name', 'Unknown')}")
    else:
        lines.append(f"🗺️ Map: {info['MapVariant']['AssetId']} (v{info['MapVariant']['VersionId']})")

    if mode_data:
        lines.append(f"⚙️ Mode: {mode_data.get('name', 'Unknown')}")
        lines.append(f'    "{mode_data.get("description", "No description available.")}"')
    else:
        lines.append(f"⚙️ Mode: {info['UgcGameVariant']['AssetId']}")
    lines.append("")

    if not stats or "Value" not in stats or not stats["Value"]:
        lines.append("⚠️ No stats available for this match")
        return "\n".join(lines)

    result = stats["Value"][0]["Result"]

    # CSR recap
    rank_recap = result.get("RankRecap", {})
    pre = rank_recap.get("PreMatchCsr", {}).get("Value")
    post = rank_recap.get("PostMatchCsr", {}).get("Value")
    if pre is not None and post is not None:
        delta = post - pre
        lines.append(f"📊 CSR: {pre} → {post} ({delta:+})")

    # Team MMR
    team_mmr = result.get("TeamMmr")
    if team_mmr:
        lines.append(f"🤝 Your Team MMR: {team_mmr:.2f}")

    team_mmrs = result.get("TeamMmrs", {})
    if team_mmrs:
        lines.append("Team MMRs:")
        for tid, mmr in team_mmrs.items():
            lines.append(f"  • Team {tid}: {mmr:.2f}")

    # Kills / Deaths
    perf = result.get("StatPerformances", {})
    kills = perf.get("Kills", {}).get("Count")
    deaths = perf.get("Deaths", {}).get("Count")
    kills_exp = perf.get("Kills", {}).get("Expected")
    deaths_exp = perf.get("Deaths", {}).get("Expected")

    if kills is not None:
        lines.append(f"🔫 Kills: {kills} (expected {kills_exp:.2f})")
    if deaths is not None:
        lines.append(f"💀 Deaths: {deaths} (expected {deaths_exp:.2f})")

    return "\n".join(lines)


