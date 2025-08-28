import pytest
import os
import pandas as pd
from datetime import datetime, timedelta
from utils.graph_generator import generate_csr_trend_plot, generate_kd_plot, generate_kd_ratio_plot, PLOT_DIR

@pytest.fixture(scope="module")
def sample_data():
    # Generate some sample data for testing
    data = []
    base_time = datetime.now() - timedelta(days=10)
    for i in range(10):
        data.append({
            "match_id": f"match_{i}",
            "start_time": base_time + timedelta(days=i),
            "post_csr": 1500 + i * 10 + (i % 2) * 5 - (i % 3) * 3,
            "kills": 10 + i,
            "deaths": 5 + (i % 5),
            "pre_csr": 1490 + i * 10 + (i % 2) * 5 - (i % 3) * 3,
            "kills_expected": 9.5 + i,
            "deaths_expected": 4.5 + (i % 5),
            "team_mmr": 1600 + i * 8
        })
    return data

@pytest.fixture(autouse=True)
def cleanup_plots():
    # Clean up any existing plots before and after tests
    if os.path.exists(PLOT_DIR):
        for f in os.listdir(PLOT_DIR):
            os.remove(os.path.join(PLOT_DIR, f))
    yield
    if os.path.exists(PLOT_DIR):
        for f in os.listdir(PLOT_DIR):
            os.remove(os.path.join(PLOT_DIR, f))

def test_generate_csr_trend_plot(sample_data):
    filepath = generate_csr_trend_plot(sample_data, filename="test_csr_trend.png")
    assert filepath is not None
    assert os.path.exists(filepath)
    # You can manually open the file to preview it
    # import subprocess
    # subprocess.run(["open", filepath]) # For macOS

def test_generate_kd_plot(sample_data):
    filepath = generate_kd_plot(sample_data, filename="test_kd_plot.png")
    assert filepath is not None
    assert os.path.exists(filepath)

def test_generate_kd_ratio_plot(sample_data):
    filepath = generate_kd_ratio_plot(sample_data, filename="test_kd_ratio_plot.png")
    assert filepath is not None
    assert os.path.exists(filepath)