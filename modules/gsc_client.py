"""
Google Search Console API Client
Handles authentication and data fetching from GSC API
"""
import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from modules.utils import get_token_path, get_credentials_path, generate_monthly_ranges

logger = logging.getLogger(__name__)

# GSC API scopes
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

# API limits
MAX_ROWS_PER_REQUEST = 25000
MAX_REQUESTS_PER_MINUTE = 1000  # Safety margin below 1200 QPM
REQUEST_DELAY_SECONDS = 60 / MAX_REQUESTS_PER_MINUTE


def get_credentials() -> Credentials:
    """
    Get valid user credentials from storage or OAuth flow.
    
    Returns:
        Credentials object for GSC API
        
    Raises:
        FileNotFoundError: If credentials file not found
        RuntimeError: If OAuth flow fails
    """
    creds_file = get_credentials_path()
    token_file = get_token_path()
    
    creds = None
    
    # Load existing token
    if token_file.exists():
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
                logger.info("Loaded credentials from token file")
        except Exception as e:
            logger.warning(f"Error loading token: {e}")
            creds = None
    
    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        # Try to refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Token expired, attempting refresh...")
                creds.refresh(Request())
                logger.info("Token refreshed successfully")
                
                # Save refreshed token
                token_data = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                with open(token_file, 'w') as f:
                    json.dump(token_data, f)
            except Exception as e:
                logger.warning(f"Error refreshing token: {e}")
                creds = None
        
        # If still no valid credentials, run OAuth flow
        if not creds or not creds.valid:
            if not creds_file.exists():
                raise FileNotFoundError(
                    f"Credentials file not found at {creds_file}. "
                    "Please ensure gsc_credentials.json exists in the project root."
                )
            
            logger.info("Starting OAuth flow...")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_file),
                SCOPES
            )
            
            creds = flow.run_local_server(port=8080, open_browser=True)
            logger.info("OAuth flow completed successfully")
        
        # Save credentials for next run (if we got new ones)
        if creds and creds.valid:
            try:
                token_data = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                with open(token_file, 'w') as f:
                    json.dump(token_data, f)
                logger.info("Credentials saved to token file")
            except Exception as e:
                logger.warning(f"Error saving token: {e}")
    
    return creds


def get_gsc_service():
    """
    Build and return GSC API service.
    
    This function works in both Streamlit and non-Streamlit contexts.
    In Streamlit, the service is cached in session state to avoid rebuilding.
    """
    # Try to use cached version if in Streamlit
    try:
        import streamlit as st
        # Check if service is already in session state
        if 'gsc_service' in st.session_state and st.session_state.gsc_service is not None:
            return st.session_state.gsc_service
        
        # Build new service
        creds = get_credentials()
        service = build('searchconsole', 'v1', credentials=creds)
        
        # Cache in session state
        st.session_state.gsc_service = service
        return service
    except (ImportError, RuntimeError, AttributeError):
        # Not in Streamlit context, use direct approach
        creds = get_credentials()
        service = build('searchconsole', 'v1', credentials=creds)
        return service


def list_sites(service) -> List[str]:
    """
    List all available GSC properties.
    
    Args:
        service: GSC API service object
        
    Returns:
        List of site URLs
    """
    try:
        sites = service.sites().list().execute()
        return [site['siteUrl'] for site in sites.get('siteEntry', [])]
    except Exception as e:
        logger.error(f"Error listing sites: {e}")
        raise


def fetch_keywords_with_pagination(
    service,
    site_url: str,
    start_date: str,
    end_date: str,
    min_impressions: int = 0,
    min_clicks: Optional[int] = None,
    keyword_pattern: Optional[str] = None,
    progress_callback: Optional[callable] = None
) -> List[str]:
    """
    Fetch keywords from GSC API with pagination support.
    
    Handles 25K row limit by paginating through results.
    Throttles requests to stay within rate limits.
    
    Args:
        service: GSC API service object
        site_url: GSC property URL
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        min_impressions: Minimum impressions filter
        min_clicks: Minimum clicks filter (optional)
        keyword_pattern: Keyword pattern filter (optional)
        progress_callback: Optional callback(current_count, total_estimated)
        
    Returns:
        List of unique keywords
    """
    all_keywords = []
    keyword_metrics = {}  # Track impressions/clicks per keyword
    start_row = 0
    batch_number = 0
    
    # Fetch all keywords (API doesn't support metric filtering)
    while True:
        batch_number += 1
        logger.info(f"Fetching batch {batch_number}, start_row={start_row}")
        
        try:
            request_body = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': ['query'],
                'rowLimit': MAX_ROWS_PER_REQUEST,
                'startRow': start_row
            }
            
            response = service.searchanalytics().query(
                siteUrl=site_url,
                body=request_body
            ).execute()
            
            if 'rows' not in response:
                break
            
            # Collect keywords and their metrics
            for row in response['rows']:
                keyword = row['keys'][0]
                impressions = row.get('impressions', 0)
                clicks = row.get('clicks', 0)
                
                # Aggregate metrics per keyword (sum across all rows)
                if keyword not in keyword_metrics:
                    keyword_metrics[keyword] = {'impressions': 0, 'clicks': 0}
                keyword_metrics[keyword]['impressions'] += impressions
                keyword_metrics[keyword]['clicks'] += clicks
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(len(keyword_metrics), None)
            
            # Check if we got fewer rows than requested (last page)
            if len(response['rows']) < MAX_ROWS_PER_REQUEST:
                break
            
            # Throttle to respect rate limits
            time.sleep(REQUEST_DELAY_SECONDS)
            
            # Move to next batch
            start_row += MAX_ROWS_PER_REQUEST
            
        except HttpError as e:
            if e.resp.status == 429:  # Quota exceeded
                logger.warning("Rate limit exceeded, waiting...")
                time.sleep(60)  # Wait 1 minute
                continue
            else:
                logger.error(f"API error: {e}")
                raise
        except Exception as e:
            logger.error(f"Error fetching keywords: {e}")
            raise
    
    # Apply filters in code (API doesn't support metric filtering)
    for keyword, metrics in keyword_metrics.items():
        if min_impressions > 0 and metrics['impressions'] < min_impressions:
            continue
        if min_clicks is not None and min_clicks > 0 and metrics['clicks'] < min_clicks:
            continue
        all_keywords.append(keyword)
    
    # Apply keyword pattern filter if provided
    if keyword_pattern:
        import re
        pattern = re.compile(keyword_pattern, re.IGNORECASE)
        all_keywords = [kw for kw in all_keywords if pattern.search(kw)]
    
    return all_keywords


def fetch_keyword_page_data(
    service,
    site_url: str,
    keyword: str,
    start_date: str = '2024-10-01',
    progress_callback: Optional[callable] = None
) -> pd.DataFrame:
    """
    Fetch page-level data for a specific keyword, aggregated monthly.
    
    For each month, makes one API call and aggregates daily data to monthly.
    Returns exactly 1 row per month per keyword+page combination.
    
    Args:
        service: GSC API service object
        site_url: Site URL (e.g., 'sc-domain:example.com')
        keyword: Search query keyword
        start_date: Start date in YYYY-MM-DD format
        progress_callback: Optional callback(current_month, total_months)
        
    Returns:
        DataFrame with columns: query, page, year_month, clicks, impressions, position, ctr
        (One row per month per page)
    """
    monthly_ranges = generate_monthly_ranges(start_date)
    all_data = []
    total_months = len(monthly_ranges)
    
    for idx, (month_start, month_end) in enumerate(monthly_ranges, 1):
        if progress_callback:
            progress_callback(idx, total_months)
        
        try:
            request = {
                'startDate': month_start,
                'endDate': month_end,
                'dimensions': ['query', 'page', 'date'],
                'dimensionFilterGroups': [{
                    'filters': [{
                        'dimension': 'query',
                        'expression': keyword,
                        'operator': 'equals'
                    }]
                }],
                'rowLimit': MAX_ROWS_PER_REQUEST
            }
            
            response = service.searchanalytics().query(
                siteUrl=site_url,
                body=request
            ).execute()
            
            if 'rows' in response:
                # Group by page and aggregate to monthly
                page_data = {}
                
                for row in response['rows']:
                    # Extract dimensions
                    query = row['keys'][0]  # query
                    page = row['keys'][1]  # page
                    date = row['keys'][2]  # date (daily)
                    
                    # Initialize page if not seen
                    if page not in page_data:
                        page_data[page] = {
                            'clicks': 0,
                            'impressions': 0,
                            'position_sum': 0,
                            'ctr_sum': 0
                        }
                    
                    # Aggregate: sum clicks/impressions, accumulate position/ctr for averaging
                    page_data[page]['clicks'] += row['clicks']
                    page_data[page]['impressions'] += row['impressions']
                    page_data[page]['position_sum'] += row['position'] * row['impressions']  # Weighted average
                    page_data[page]['ctr_sum'] += row['ctr'] * row['impressions']  # Weighted average
                
                # Create monthly aggregated rows (1 per page per month)
                year_month = datetime.strptime(month_start, '%Y-%m-%d').strftime('%Y-%m')
                
                for page, data in page_data.items():
                    # Calculate weighted averages
                    if data['impressions'] > 0:
                        avg_position = data['position_sum'] / data['impressions']
                        avg_ctr = data['ctr_sum'] / data['impressions']
                    else:
                        avg_position = 0
                        avg_ctr = 0
                    
                    all_data.append({
                        'query': keyword,
                        'page': page,
                        'year_month': year_month,
                        'clicks': data['clicks'],
                        'impressions': data['impressions'],
                        'position': avg_position,
                        'ctr': avg_ctr
                    })
            
            # Throttle to respect rate limits
            time.sleep(REQUEST_DELAY_SECONDS)
        
        except HttpError as e:
            if e.resp.status == 429:  # Quota exceeded
                logger.warning(f"Rate limit exceeded for {month_start}, waiting...")
                time.sleep(60)  # Wait 1 minute
                continue
            else:
                logger.error(f"API error for {month_start}: {e}")
                continue
        except Exception as e:
            logger.error(f"Error fetching data for {month_start} to {month_end}: {e}")
            continue
    
    if not all_data:
        return pd.DataFrame(columns=['query', 'page', 'year_month', 'clicks', 'impressions', 'position', 'ctr'])
    
    df = pd.DataFrame(all_data)
    return df


def pivot_to_monthly_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot the data to have monthly columns.
    
    Input format:
        query | page | year_month | clicks | impressions | position | ctr
    
    Output format:
        Keyword | Page | Metric | 2024-10 | 2024-11 | 2024-12 | ...
    """
    if df.empty:
        return pd.DataFrame()
    
    # Convert year_month to string format (YYYY-MM)
    df['month'] = df['year_month'].astype(str)
    
    # Melt metrics
    metrics = ['clicks', 'impressions', 'position', 'ctr']
    melted = df.melt(
        id_vars=['query', 'page', 'month'],
        value_vars=metrics,
        var_name='metric',
        value_name='value'
    )
    
    # Pivot to get months as columns
    pivoted = melted.pivot_table(
        index=['query', 'page', 'metric'],
        columns='month',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Rename columns
    pivoted.columns.name = None
    pivoted = pivoted.rename(columns={
        'query': 'Keyword',
        'page': 'Page',
        'metric': 'Metric'
    })
    
    # Sort columns: Keyword, Page, Metric, then monthly columns
    month_cols = sorted([c for c in pivoted.columns if c not in ['Keyword', 'Page', 'Metric']])
    pivoted = pivoted[['Keyword', 'Page', 'Metric'] + month_cols]
    
    return pivoted

