# src/data_analysis.py
def analyze_data(data):
    """Analyzes the data and returns summary statistics."""
    summary_stats = data.describe()
    return summary_stats
