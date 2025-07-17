import datetime
import os


def extract_year_month(file_path: str):
    """extract year and month from file's last modified timestamp."""

    timestamp = os.path.getmtime(file_path)
    dt = datetime.datetime.fromtimestamp(timestamp)
    return str(dt.year), f"{dt.month:02d}"  # e.g., "2025", "06"
