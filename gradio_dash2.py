import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

from data_analysis import load_data as da_load_data, compute_category_summary, compute_ship_summary

# Path to your CSVs
DIRECTORY = "/Users/nirugidla/PycharmProjects/UMICHIGAN_code/dashboards"

def load_data():
    # Delegate to data_analysis.py
    return da_load_data(DIRECTORY)