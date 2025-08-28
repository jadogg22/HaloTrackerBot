# Halo Match Tracker Discord Bot

This is a Discord bot that tracks your Halo Infinite match history and provides summaries of your performance.

## Features

-   Monitors your Halo Infinite activity and automatically starts tracking when you're playing.
-   Provides a summary of your last match, including your K/D ratio, CSR, and team MMR.
-   Stores your match history in a local SQLite database.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```
2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure the bot:**
    -   Open the `config.py` file.
    -   Set your `DISCORD_TOKEN` environment variable (your Discord bot token).
    -   Set your `GUILD_ID` (your Discord server ID) and `USER_ID` (your Discord user ID).
    -   Set your `SPARTAN_TOKEN` environment variable. You can get this from the Halo Waypoint website. The bot will guide you if the token expires.

## Usage

To run the bot, execute the `main.py` file:

```bash
python main.py
```

The bot will then be online and will start tracking your Halo Infinite activity.