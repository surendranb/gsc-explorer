"""
Utility functions for GSC Explorer
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """Get the data directory, creating it if needed."""
    data_dir = get_project_root() / 'data'
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_config_dir() -> Path:
    """Get the config directory."""
    return get_project_root() / 'config'


def get_token_path() -> Path:
    """Get the path to token.json."""
    return get_project_root() / 'token.json'


def get_credentials_path() -> Path:
    """Get the path to gsc_credentials.json."""
    return get_project_root() / 'gsc_credentials.json'


def get_config_path() -> Path:
    """Get the path to config.json."""
    return get_config_dir() / 'config.json'


def get_db_path() -> Path:
    """Get the path to keywords database."""
    return get_data_dir() / 'keywords.db'


def load_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to config.json."""
    config_path = get_config_path()
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def is_first_run() -> bool:
    """
    Check if this is the first time running the app.
    
    Returns True if:
    - Token doesn't exist, OR
    - Database doesn't exist, OR
    - Database exists but has no keywords
    """
    token_exists = get_token_path().exists()
    db_exists = get_db_path().exists()
    
    if not token_exists or not db_exists:
        return True
    
    # Check if database has keywords
    try:
        import sqlite3
        conn = sqlite3.connect(get_db_path())
        # Check if table exists first
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keywords'")
        if not cursor.fetchone():
            conn.close()
            return True
        
        cursor = conn.execute("SELECT COUNT(*) FROM keywords")
        keyword_count = cursor.fetchone()[0]
        conn.close()
        
        return keyword_count == 0
    except Exception:
        # If table doesn't exist or error, treat as first run
        return True


def generate_monthly_ranges(start_date_str: str = '2024-10-01') -> list:
    """
    Generate list of (month_start, month_end) tuples from start_date to now.
    
    Args:
        start_date_str: Start date in YYYY-MM-DD format
    
    Returns:
        List of tuples: [(start_date, end_date), ...]
    """
    from datetime import datetime, timedelta
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.now()
    
    months = []
    current = start_date.replace(day=1)  # Start of first month
    
    while current <= end_date:
        # Calculate end of month
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1, day=1)
        else:
            next_month = current.replace(month=current.month + 1, day=1)
        
        month_end = next_month - timedelta(days=1)
        
        # Don't go beyond today
        if month_end > end_date:
            month_end = end_date
        
        months.append((
            current.strftime('%Y-%m-%d'),
            month_end.strftime('%Y-%m-%d')
        ))
        
        current = next_month
    
    return months

