
import os
import pytest
from utils.graph_generator import generate_csr_trend_plot, generate_kd_plot, generate_kd_ratio_plot

@pytest.fixture
def sample_data():
    return [
        {'start_time': '2024-01-01T12:00:00', 'post_csr': 1500, 'kills': 10, 'deaths': 5},
        {'start_time': '2024-01-01T13:00:00', 'post_csr': 1520, 'kills': 12, 'deaths': 8},
        {'start_time': '2024-01-01T14:00:00', 'post_csr': 1510, 'kills': 8, 'deaths': 10},
    ]

def test_generate_csr_trend_plot(sample_data):
    filename = "test_csr_trend.png"
    filepath = generate_csr_trend_plot(sample_data, filename)
    assert os.path.exists(filepath)
    assert filepath.endswith(filename)
    os.remove(filepath)

def test_generate_kd_plot(sample_data):
    filename = "test_kd_plot.png"
    filepath = generate_kd_plot(sample_data, filename)
    assert os.path.exists(filepath)
    assert filepath.endswith(filename)
    os.remove(filepath)

def test_generate_kd_ratio_plot(sample_data):
    filename = "test_kd_ratio_plot.png"
    filepath = generate_kd_ratio_plot(sample_data, filename)
    assert os.path.exists(filepath)
    assert filepath.endswith(filename)
    os.remove(filepath)

def test_generate_csr_trend_plot_no_data():
    filepath = generate_csr_trend_plot([])
    assert filepath is None

def test_generate_kd_plot_no_data():
    filepath = generate_kd_plot([])
    assert filepath is None

def test_generate_kd_ratio_plot_no_data():
    filepath = generate_kd_ratio_plot([])
    assert filepath is None
