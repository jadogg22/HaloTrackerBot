"""Handles caching and retrieval of Halo Infinite match data in a SQLite database."""
import sqlite3
from datetime import datetime, timedelta

DB_FILE = "/app/data/matches_cache.db"

def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database.

    Returns:
        sqlite3.Connection: A database connection object with row_factory set to sqlite3.Row.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database by creating necessary tables if they don't already exist.
    Tables created: matches, stats, team_mmrs, maps, Modes.
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            start_time TEXT,
            end_time TEXT,
            duration INTEGER,
            outcome TEXT,
            rank INTEGER,
            playlist_id TEXT,
            map_variant TEXT,
            map_version INTEGER,
            ugc_variant TEXT,
            teams_enabled BOOLEAN,
            team_scoring BOOLEAN
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            match_id TEXT PRIMARY KEY,
            pre_csr REAL,
            post_csr REAL,
            kills INTEGER,
            deaths INTEGER,
            kills_expected REAL,
            deaths_expected REAL,
            team_mmr REAL,
            FOREIGN KEY(match_id) REFERENCES matches(match_id)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS team_mmrs (
            match_id TEXT,
            team_id TEXT,
            mmr REAL,
            PRIMARY KEY (match_id, team_id),
            FOREIGN KEY(match_id) REFERENCES matches(match_id)
        )""")
        # Maps table
        c.execute("""
        CREATE TABLE IF NOT EXISTS maps (
            AssetId UNIQUEIDENTIFIER NOT NULL,
            VersionId UNIQUEIDENTIFIER NOT NULL,
            PublicName TEXT NULL,
            Description TEXT NULL,
            PRIMARY KEY (AssetId, VersionId)
        );""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS Modes (
                AssetId UNIQUEIDENTIFIER NOT NULL,
                VersionId UNIQUEIDENTIFIER NOT NULL,
                PublicName TEXT NULL,
                Description TEXT NULL,
                PRIMARY KEY (AssetId, VersionId)
        );
        """)
        conn.commit()

def _save_match_info(cursor, match):
    """
    Saves core match information into the 'matches' table.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        match (dict): Dictionary containing match information.
    """
    info = match["MatchInfo"]
    outcome = match.get("Outcome", None)
    rank = match.get("Rank", None)

    cursor.execute("""
    INSERT OR REPLACE INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        match["MatchId"],
        info.get("StartTime"),
        info.get("EndTime"),
        info.get("Duration"),
        outcome,
        rank,
        info['Playlist']['AssetId'],
        info['MapVariant']['AssetId'],
        info['MapVariant'].get('VersionId'),
        info['UgcGameVariant']['AssetId'],
        info.get('TeamsEnabled'),
        info.get('TeamScoringEnabled')
    ))

def _save_stats(cursor, match_id, stats):
    """
    Saves match statistics into the 'stats' table.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        match_id (str): The ID of the match.
        stats (dict): Dictionary containing match statistics.
    """
    result = stats["Value"][0]["Result"] if stats and "Value" in stats else {}
    rank_recap = result.get("RankRecap", {})
    pre = rank_recap.get("PreMatchCsr", {}).get("Value")
    post = rank_recap.get("PostMatchCsr", {}).get("Value")

    perf = result.get("StatPerformances", {})
    kills = perf.get("Kills", {}).get("Count")
    deaths = perf.get("Deaths", {}).get("Count")
    kills_exp = perf.get("Kills", {}).get("Expected")
    deaths_exp = perf.get("Deaths", {}).get("Expected")
    team_mmr = result.get("TeamMmr")

    cursor.execute("""
    INSERT OR REPLACE INTO stats VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (match_id, pre, post, kills, deaths, kills_exp, deaths_exp, team_mmr))

def _save_team_mmrs(cursor, match_id, stats):
    """
    Saves team MMRs for a match into the 'team_mmrs' table.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        match_id (str): The ID of the match.
        stats (dict): Dictionary containing match statistics.
    """
    cursor.execute("DELETE FROM team_mmrs WHERE match_id = ?", (match_id,))
    for tid, mmr in stats["Value"][0]["Result"].get("TeamMmrs", {}).items():
        cursor.execute("INSERT INTO team_mmrs VALUES (?, ?, ?)", (match_id, tid, mmr))

def save_match_data(match, stats):
    """
    Saves comprehensive match data (info, stats, team MMRs) to the database.

    Args:
        match (dict): Dictionary containing core match information.
        stats (dict): Dictionary containing match statistics.
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        _save_match_info(c, match)
        _save_stats(c, match["MatchId"], stats)
        _save_team_mmrs(c, match["MatchId"], stats)
        conn.commit()

def Get_Latest_Match():
    """
    Retrieves the latest match recorded in the database based on start time.

    Returns:
        dict or None: A dictionary containing the latest match's ID and start time,
                      or None if no matches are found.
    """
    with get_db_connection() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM matches ORDER BY start_time DESC LIMIT 1")
        row = c.fetchone()

        if row:
            return {
                "MatchId": row["match_id"],
                "MatchInfo": {"StartTime": row["start_time"]}
            }
        return None

def get_asset_from_db(table_name, asset_id, version_id):
    """
    Retrieves asset (map or mode) data from the database.

    Args:
        table_name (str): The name of the table to query ('maps' or 'Modes').
        asset_id (str): The AssetId of the asset.
        version_id (str): The VersionId of the asset.

    Returns:
        dict or None: A dictionary containing the asset's public name and description,
                      or None if the asset is not found.
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(f"SELECT PublicName, Description FROM {table_name} WHERE AssetId = ? AND VersionId = ?", (asset_id, version_id))
        result = c.fetchone()
        if result:
            return {"name": result[0], "description": result[1]}
        return None

def get_recent_match_data(count=10, session_only=False):
    """
    Retrieves recent match data from the database.

    Args:
        count (int): The maximum number of recent matches to retrieve if not session_only.
        session_only (bool): If True, retrieves matches belonging to the current playing session.
                             A session is defined by matches with no more than a 2-hour gap.
k
    Returns:
        list[sqlite3.Row]: A list of sqlite3.Row objects, each representing a match.
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        if session_only:
            c.execute("""
                SELECT
                    m.match_id,
                    m.start_time,
                    m.end_time,
                    m.duration,
                    m.outcome,
                    s.pre_csr,
                    s.post_csr,
                    s.kills,
                    s.deaths,
                    s.kills_expected,
                    s.deaths_expected,
                    s.team_mmr
                FROM matches m
                JOIN stats s ON m.match_id = s.match_id
                ORDER BY m.start_time DESC
            """)
            all_matches = c.fetchall()
            if not all_matches:
                return []

            session_matches = []
            # Start with the latest match's start time for comparison
            last_match_time = datetime.fromisoformat(all_matches[0]["start_time"].replace("Z", "+00:00"))

            for match in all_matches:
                current_match_time = datetime.fromisoformat(match["start_time"].replace("Z", "+00:00"))
                if last_match_time - current_match_time > timedelta(hours=2):
                    break
                session_matches.append(match)
                last_match_time = current_match_time
            
            return session_matches[::-1]
        else:
            c.execute("""
                SELECT
                    m.match_id,
                    m.start_time,
                    m.end_time,
                    m.duration,
                    m.outcome,
                    s.pre_csr,
                    s.post_csr,
                    s.kills,
                    s.deaths,
                    s.kills_expected,
                    s.deaths_expected,
                    s.team_mmr
                FROM matches m
                JOIN stats s ON m.match_id = s.match_id
                ORDER BY m.start_time DESC
                LIMIT ?
            """, (count,))
            rows = c.fetchall()
            return rows

def upsert_asset(cursor, table_name, asset_id, version_id, public_name, description):
    """
    Inserts or updates asset (map or mode) data in the database.

    Args:
        cursor (sqlite3.Cursor): The database cursor object.
        table_name (str): The name of the table to update ('maps' or 'Modes').
        asset_id (str): The AssetId of the asset.
        version_id (str): The VersionId of the asset.
        public_name (str): The public name of the asset.
        description (str): The description of the asset.
    """
    cursor.execute(f"""
        INSERT OR REPLACE INTO {table_name} (AssetId, VersionId, PublicName, Description)
        VALUES (?, ?, ?, ?);
    """, (asset_id, version_id, public_name, description))
