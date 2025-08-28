"""Generates various statistical plots for Halo Infinite match data."""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
from datetime import datetime
import logging

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set a consistent style and palette for all plots
sns.set_style("whitegrid") # Changed style
sns.set_palette("deep") # Changed palette

# Ensure a temporary directory for plots exists
PLOT_DIR = "./plots"
os.makedirs(PLOT_DIR, exist_ok=True)

def generate_csr_trend_plot(data: list[dict], filename="csr_trend.png") -> str:
    """
    Generates a line plot showing CSR trend over matches.

    Args:
        data (list[dict]): A list of dictionaries, each representing a match with CSR data.
        filename (str): The name of the file to save the plot as.

    Returns:
        str or None: The filepath of the saved plot, or None if no valid data is provided.
    """
    if not data:
        logging.warning("No data provided for CSR trend plot.")
        return None

    df = pd.DataFrame(data)
    # Ensure 'post_csr' column exists, fill with NaN if not
    if 'post_csr' not in df.columns:
        df['post_csr'] = pd.NA
    # Filter out matches where CSR is not available or didn't change
    df = df[df['post_csr'].notna()]
    if df.empty:
        logging.warning("No valid CSR data after filtering for CSR trend plot.")
        return None

    plt.figure(figsize=(12, 7), facecolor='#f5f5f5') # Added facecolor
    sns.lineplot(x=df.index, y='post_csr', data=df, marker='o', linewidth=3) # Increased linewidth
    plt.title('CSR Trend Over Matches', fontsize=18) # Increased fontsize
    plt.xlabel('Match Number', fontsize=14) # Increased fontsize
    plt.ylabel('Post-Match CSR', fontsize=14) # Increased fontsize
    plt.grid(True, linestyle=':', alpha=0.6) # Refined grid
    plt.tight_layout()

    filepath = os.path.join(PLOT_DIR, filename)
    plt.savefig(filepath)
    plt.close()
    logging.info(f"Generated CSR trend plot: {filepath}")
    return filepath

def generate_kd_plot(data: list[dict], filename="kd_plot.png") -> str:
    """
    Generates a line plot showing Kills, Deaths, and Expected Performance over matches.

    Args:
        data (list[dict]): A list of dictionaries, each representing a match with K/D data.
        filename (str): The name of the file to save the plot as.

    Returns:
        str or None: The filepath of the saved plot, or None if no valid data is provided.
    """
    if not data:
        logging.warning("No data provided for K/D plot.")
        return None

    df = pd.DataFrame(data)
    plt.figure(figsize=(12, 7), facecolor='#f5f5f5') # Added facecolor
    sns.lineplot(x=df.index, y='kills', data=df, marker='o', label='Kills', linewidth=3, color='red')
    sns.lineplot(x=df.index, y='kills_expected', data=df, marker='o', linestyle='--', label='Expected Kills', alpha=0.7, linewidth=1.5, color='red') # Added marker
    sns.lineplot(x=df.index, y='deaths', data=df, marker='o', label='Deaths', linewidth=3, color='blue')
    sns.lineplot(x=df.index, y='deaths_expected', data=df, marker='o', linestyle='--', label='Expected Deaths', alpha=0.7, linewidth=1.5, color='blue') # Added marker
    
    plt.title('Kills, Deaths, and Expected Performance Over Matches', fontsize=18) # Increased fontsize
    plt.xlabel('Match Number', fontsize=14) # Increased fontsize
    plt.ylabel('Count', fontsize=14) # Increased fontsize
    plt.legend(loc='best', fontsize=12) # Increased fontsize
    plt.grid(True, linestyle=':', alpha=0.6) # Refined grid
    plt.tight_layout()

    filepath = os.path.join(PLOT_DIR, filename)
    plt.savefig(filepath)
    plt.close()
    logging.info(f"Generated K/D plot: {filepath}")
    return filepath

def generate_kd_ratio_plot(data: list[dict], filename="kd_ratio_plot.png") -> str:
    """
    Generates a line plot showing K/D Ratio over matches.

    Args:
        data (list[dict]): A list of dictionaries, each representing a match with K/D data.
        filename (str): The name of the file to save the plot as.

    Returns:
        str or None: The filepath of the saved plot, or None if no valid data is provided.
    """
    if not data:
        logging.warning("No data provided for K/D Ratio plot.")
        return None

    df = pd.DataFrame(data)
    df['kd_ratio'] = df['kills'] / df['deaths'].replace(0, 1) # Avoid division by zero

    plt.figure(figsize=(12, 7), facecolor='#f5f5f5') # Added facecolor
    sns.lineplot(x=df.index, y='kd_ratio', data=df, marker='o', linewidth=3) # Increased linewidth
    plt.title('K/D Ratio Over Matches', fontsize=18) # Increased fontsize
    plt.xlabel('Match Number', fontsize=14) # Increased fontsize
    plt.ylabel('K/D Ratio', fontsize=14) # Increased fontsize
    plt.grid(True, linestyle=':', alpha=0.6) # Refined grid
    plt.tight_layout()

    filepath = os.path.join(PLOT_DIR, filename)
    plt.savefig(filepath)
    plt.close()
    logging.info(f"Generated K/D Ratio plot: {filepath}")
    return filepath