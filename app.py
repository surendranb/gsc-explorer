"""
GSC Explorer - Main Application
A simple tool for exploring Google Search Console keyword-page performance data
"""
import logging
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

from modules.utils import (
    is_first_run,
    get_db_path,
    load_config,
    get_config_path
)
from modules.setup import run_setup_flow
from modules.gsc_client import (
    get_gsc_service,
    fetch_keyword_page_data,
    pivot_to_monthly_columns
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="GSC Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data
def load_keywords_from_db(domain: str = None):
    """Load keywords from database, optionally filtered by domain."""
    db_path = get_db_path()
    
    if not db_path.exists():
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        
        if domain:
            query = "SELECT DISTINCT keyword FROM keywords WHERE domain = ? ORDER BY keyword"
            df = pd.read_sql_query(query, conn, params=(domain,))
        else:
            query = "SELECT DISTINCT keyword FROM keywords ORDER BY keyword"
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        return df['keyword'].tolist()
    except Exception as e:
        logger.error(f"Error loading keywords: {e}")
        return []


def filter_keywords(keywords, search_term):
    """Filter keywords based on search term."""
    if not search_term:
        return keywords
    search_lower = search_term.lower()
    return [kw for kw in keywords if search_lower in kw.lower()]


def display_filtered_results(result_df):
    """Display results table with keyword, page, and metric filters."""
    st.markdown("---")
    st.header("Results")
    
    # Extract unique keywords, pages, and metrics for filters
    unique_keywords = sorted(result_df['Keyword'].unique().tolist())
    unique_pages = sorted(result_df['Page'].unique().tolist())
    unique_metrics = sorted(result_df['Metric'].unique().tolist())
    
    # Add filters in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_keyword = st.selectbox(
            "🔍 Filter by Keyword",
            options=["All"] + unique_keywords,
            index=0,
            key="filter_keyword"
        )
    
    with col2:
        selected_pages = st.multiselect(
            "🔍 Filter by Page",
            options=unique_pages,
            default=[],
            key="filter_page"
        )
    
    with col3:
        selected_metric = st.selectbox(
            "🔍 Filter by Metric",
            options=["All"] + unique_metrics,
            index=0,
            key="filter_metric"
        )
    
    # Apply filters
    filtered_df = result_df.copy()
    
    if selected_keyword != "All":
        filtered_df = filtered_df[filtered_df['Keyword'] == selected_keyword]
    
    if selected_pages:
        filtered_df = filtered_df[filtered_df['Page'].isin(selected_pages)]
    
    if selected_metric != "All":
        filtered_df = filtered_df[filtered_df['Metric'] == selected_metric]
    
    # Show filter info
    if selected_keyword != "All" or selected_pages or selected_metric != "All":
        st.info(f"Showing {len(filtered_df)} of {len(result_df)} rows")
    
    # Add TOTAL column (sum of all monthly columns for each row)
    if len(filtered_df) > 0:
        monthly_cols = [col for col in filtered_df.columns if col not in ['Keyword', 'Page', 'Metric']]
        filtered_df['TOTAL'] = filtered_df[monthly_cols].sum(axis=1)
        
        # Reorder columns: Keyword, Page, Metric, monthly columns, TOTAL
        display_df = filtered_df[['Keyword', 'Page', 'Metric'] + monthly_cols + ['TOTAL']]
    else:
        display_df = filtered_df
    
    # Display table with built-in download
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600
    )


def main_app():
    """Main application interface."""
    st.title("📊 GSC Explorer")
    st.markdown("Select keywords to fetch page-level performance data from Google Search Console")
    
    # Load config
    config = load_config()
    site_url = config.get('site_url', '')
    
    # Show database info and import option
    with st.expander("ℹ️ Database Info & Settings", expanded=False):
        db_path = get_db_path()
        st.write(f"**Database Path:** `{db_path}`")
        st.write(f"**Exists:** {db_path.exists()}")
        if db_path.exists():
            st.write(f"**Size:** {db_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        st.markdown("---")
        st.markdown("### Import More Keywords")
        st.markdown("Need to import more keywords or update your keyword list?")
        if st.button("📥 Import Keywords", use_container_width=True):
            # Go to Step 4 of setup flow
            st.session_state.setup_step = 4
            st.session_state.setup_complete = None  # Allow going back to setup
            st.rerun()
    
    # Load keywords for the selected domain
    with st.spinner("Loading keywords from database..."):
        all_keywords = load_keywords_from_db(domain=site_url)
    
    if not all_keywords:
        st.error("No keywords found in database.")
        st.info(
            f"Database path: `{get_db_path()}`\n\n"
            "Please ensure:\n"
            "- You've completed the setup flow\n"
            "- Keywords have been imported\n"
            "- The database file exists"
        )
        return
    
    # Sidebar for keyword selection
    with st.sidebar:
        st.header("Keyword Selection")
        
        # Search bar
        search_term = st.text_input("🔍 Search keywords", placeholder="Type to filter...")
        
        # Filter keywords
        filtered_keywords = filter_keywords(all_keywords, search_term)
        
        st.markdown(f"**{len(filtered_keywords)}** keywords found")
        
        if len(filtered_keywords) == 0:
            st.info("No keywords match your search.")
        else:
            # Select all checkbox
            select_all = st.checkbox("Select All", key="select_all")
            
            # Initialize session state for selected keywords
            if 'selected_keywords' not in st.session_state:
                st.session_state.selected_keywords = set()
            
            # Handle select all
            if select_all:
                st.session_state.selected_keywords = set(filtered_keywords)
            elif not select_all and len(st.session_state.selected_keywords) == len(filtered_keywords):
                if all(kw in st.session_state.selected_keywords for kw in filtered_keywords):
                    st.session_state.selected_keywords = set()
            
            # Keyword checkboxes (scrollable, limit to 500 for performance)
            st.markdown("---")
            st.markdown("**Select keywords:**")
            
            display_keywords = filtered_keywords[:500]
            if len(filtered_keywords) > 500:
                st.warning(f"Showing first 500 of {len(filtered_keywords)} keywords. Use search to narrow down.")
            
            for keyword in display_keywords:
                is_selected = keyword in st.session_state.selected_keywords
                if st.checkbox(keyword, value=is_selected, key=f"kw_{keyword}"):
                    st.session_state.selected_keywords.add(keyword)
                else:
                    st.session_state.selected_keywords.discard(keyword)
            
            # Show selected count
            selected_count = len(st.session_state.selected_keywords)
            st.markdown("---")
            st.markdown(f"**{selected_count}** keyword(s) selected")
            
            # Site URL input
            st.markdown("---")
            st.markdown("**GSC Configuration:**")
            site_url_input = st.text_input(
                "Site URL",
                value=site_url,
                placeholder="e.g., sc-domain:example.com or https://example.com",
                help="Your Google Search Console property URL"
            )
            
            # Fetch button
            fetch_button = st.button(
                "🚀 Fetch Data",
                type="primary",
                disabled=selected_count == 0 or not site_url_input,
                use_container_width=True
            )
    
    # Main area - Results
    if fetch_button and st.session_state.selected_keywords and site_url_input:
        selected_keywords_list = list(st.session_state.selected_keywords)
        
        st.header("Results")
        st.info(f"Fetching data for {len(selected_keywords_list)} keyword(s)...")
        
        # Initialize GSC service
        try:
            with st.spinner("Authenticating with Google Search Console..."):
                service = get_gsc_service()
        except FileNotFoundError as e:
            st.error("❌ Credentials file not found.")
            st.info("""
            Please complete the setup flow first:
            1. Ensure `gsc_credentials.json` is in the project root
            2. Complete the authentication steps
            """)
            if st.button("Go to Setup"):
                st.session_state.setup_complete = None
                st.rerun()
            return
        except RuntimeError as e:
            error_msg = str(e)
            st.error("❌ Authentication failed")
            st.markdown(f"**Error:** {error_msg}")
            if 'redirect_uri' in error_msg.lower():
                st.info("""
                **Redirect URI Configuration Issue:**
                Please check your Google Cloud Console OAuth settings.
                """)
            else:
                st.info("""
                **Troubleshooting:**
                - Your token may have expired. Try re-authenticating.
                - Check your internet connection.
                - Ensure port 8090 is not blocked.
                """)
            if st.button("Re-authenticate"):
                # Clear token to force re-auth
                from modules.utils import get_token_path
                token_path = get_token_path()
                if token_path.exists():
                    token_path.unlink()
                st.session_state.gsc_service = None
                st.rerun()
            return
        except Exception as e:
            st.error(f"❌ Authentication failed: {e}")
            logger.error(f"Authentication error in main app: {e}", exc_info=True)
            st.info("Please try re-authenticating or check your credentials.")
            if st.button("Re-authenticate"):
                # Clear token to force re-auth
                from modules.utils import get_token_path
                token_path = get_token_path()
                if token_path.exists():
                    token_path.unlink()
                st.session_state.gsc_service = None
                st.rerun()
            return
        
        # Get date range from config
        date_range = config.get('date_range', {})
        start_date = date_range.get('start', '2024-10-01')
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_results = []
        
        # Fetch data for each keyword
        total_keywords = len(selected_keywords_list)
        for idx, keyword in enumerate(selected_keywords_list):
            status_text.text(f"Fetching data for: {keyword} ({idx + 1}/{total_keywords})")
            
            try:
                # Fetch data
                df = fetch_keyword_page_data(
                    service,
                    site_url_input,
                    keyword,
                    start_date=start_date,
                    progress_callback=lambda curr, total: progress_bar.progress(
                        (idx + (curr / total if total else 0)) / total_keywords
                    ) if total else None
                )
                
                if not df.empty:
                    all_results.append(df)
                
            except Exception as e:
                st.warning(f"Error fetching data for '{keyword}': {e}")
                logger.error(f"Error fetching data for {keyword}: {e}", exc_info=True)
                continue
            
            # Update progress
            progress_bar.progress((idx + 1) / total_keywords)
        
        # Combine all results
        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
            
            # Pivot to monthly columns
            status_text.text("Processing data...")
            result_df = pivot_to_monthly_columns(combined_df)
            
            # Display results
            status_text.empty()
            progress_bar.empty()
            
            st.success(f"✅ Data fetched successfully! {len(result_df)} rows found.")
            
            # Store in session state for download
            st.session_state.result_df = result_df
            
            # Add filters
            display_filtered_results(result_df)
            
        else:
            status_text.empty()
            progress_bar.empty()
            st.warning("No data found for selected keywords.")
    
    elif 'result_df' in st.session_state:
        # Show previous results if available
        display_filtered_results(st.session_state.result_df)


def main():
    """Main entry point."""
    # Priority 1: If setup is explicitly marked complete, go to main app
    if st.session_state.get('setup_complete') is True:
        # Setup is complete - show main app
        # Clear any lingering setup_step to prevent accidental setup flow
        if 'setup_step' in st.session_state:
            del st.session_state.setup_step
        main_app()
        return
    
    # Priority 2: Check if user explicitly wants to go to setup (e.g., to import more keywords)
    if st.session_state.get('setup_step') == 4:
        # User clicked "Import Keywords" - go to Step 4
        run_setup_flow()
        return
    
    # Priority 3: Check if this is a first run (no token, no database, or empty database)
    if is_first_run():
        # First run - show setup flow
        run_setup_flow()
        return
    
    # Priority 4: Default to main app (shouldn't normally reach here, but safe fallback)
    if 'setup_step' in st.session_state:
        del st.session_state.setup_step
    main_app()


if __name__ == "__main__":
    main()

