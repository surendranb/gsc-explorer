"""
First-run setup module
Handles authentication, property selection, and keyword import
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import streamlit as st
from modules.gsc_client import (
    get_gsc_service,
    list_sites,
    fetch_keywords_with_pagination
)
from modules.utils import (
    get_db_path,
    get_config_path,
    save_config,
    load_config
)

logger = logging.getLogger(__name__)


def init_database():
    """Initialize the keywords database."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if table exists and has domain column
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keywords'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # Check if domain column exists
        cursor.execute("PRAGMA table_info(keywords)")
        columns = [col[1] for col in cursor.fetchall()]
        has_domain = 'domain' in columns
        
        if not has_domain:
            # Migrate: add domain column to existing table
            try:
                conn.execute("ALTER TABLE keywords ADD COLUMN domain TEXT DEFAULT ''")
                conn.commit()
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not add domain column: {e}")
    else:
        # Create new table with domain column
        conn.execute("""
            CREATE TABLE keywords (
                keyword TEXT,
                domain TEXT,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                import_criteria TEXT,
                PRIMARY KEY (keyword, domain)
            )
        """)
        conn.commit()
    
    conn.close()


def save_keywords(keywords: List[str], domain: str, import_criteria: Dict[str, Any]):
    """Save keywords to database."""
    init_database()
    
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    
    criteria_json = str(import_criteria)
    
    for keyword in keywords:
        conn.execute("""
            INSERT OR REPLACE INTO keywords (keyword, domain, imported_at, import_criteria)
            VALUES (?, ?, ?, ?)
        """, (keyword, domain, datetime.now(), criteria_json))
    
    conn.commit()
    conn.close()


def check_credentials_file() -> bool:
    """Check if credentials file exists."""
    from modules.utils import get_credentials_path
    return get_credentials_path().exists()


def show_step_progress(current_step: int):
    """Display step progress indicator."""
    steps = [
        ("Setup Credentials", "Get your Google OAuth credentials file"),
        ("Authenticate", "Connect your Google account"),
        ("Select Property", "Choose your GSC property"),
        ("Import Keywords", "Fetch keywords from GSC")
    ]
    
    # Create columns for steps
    cols = st.columns(4)
    for idx, (step_name, step_desc) in enumerate(steps, 1):
        with cols[idx - 1]:
            if idx < current_step:
                # Completed step
                st.markdown(f"✅ **Step {idx}**")
                st.markdown(f"*{step_name}*")
            elif idx == current_step:
                # Current step
                st.markdown(f"🔄 **Step {idx}**")
                st.markdown(f"**{step_name}**")
            else:
                # Future step
                st.markdown(f"⏳ **Step {idx}**")
                st.markdown(f"*{step_name}*")
    
    st.markdown("---")


def run_setup_flow():
    """Run the first-run setup flow."""
    st.title("🚀 Welcome to GSC Explorer")
    st.markdown("Let's get you set up in 4 simple steps:")
    
    # Initialize setup step (start at 1, not 0)
    # Only set to 1 if not already set (allows jumping to Step 4 for imports)
    if 'setup_step' not in st.session_state:
        st.session_state.setup_step = 1
    # If setup_step is None or invalid, reset to 1
    elif st.session_state.setup_step not in [1, 2, 3, 4]:
        st.session_state.setup_step = 1
    
    # Don't show setup flow if setup is already complete (unless explicitly going to Step 4)
    if st.session_state.get('setup_complete') is True and st.session_state.setup_step != 4:
        # Setup is complete, redirect to main app
        st.info("✅ Setup already complete! Redirecting to main app...")
        st.rerun()
        return
    
    # Show step progress
    show_step_progress(st.session_state.setup_step)
    
    # Route to appropriate step
    if st.session_state.setup_step == 1:
        step1_credentials_setup()
    elif st.session_state.setup_step == 2:
        step2_authentication()
    elif st.session_state.setup_step == 3:
        step3_property_selection()
    elif st.session_state.setup_step == 4:
        step4_keyword_import()


def step1_credentials_setup():
    """Step 1: Setup credentials file."""
    st.header("Step 1: Setup Credentials")
    st.markdown("First, we need your Google OAuth credentials to access Google Search Console.")
    
    from modules.utils import get_credentials_path
    
    creds_path = get_credentials_path()
    
    # Check if file exists
    if creds_path.exists():
        st.success(f"✅ Credentials file found at `{creds_path}`")
        if st.button("Continue to Step 2 →", type="primary"):
            st.session_state.setup_step = 2
            st.rerun()
        return
    
    # Show instructions
    st.info("📋 **You need to create a Google OAuth client and download the credentials file.**")
    
    st.markdown("### How to get your credentials:")
    
    st.markdown("""
    1. **Go to Google Cloud Console**
       - Open [Google Cloud Console](https://console.cloud.google.com/)
       - Sign in with your Google account
    
    2. **Create or select a project**
       - Click the project dropdown at the top
       - Click "New Project" or select an existing project
    
    3. **Enable the Search Console API**
       - Go to [API Library](https://console.cloud.google.com/apis/library)
       - Search for "Google Search Console API"
       - Click on it and press "Enable"
    
    4. **Create OAuth credentials**
       - Go to [Credentials page](https://console.cloud.google.com/apis/credentials)
       - Click "Create Credentials" → "OAuth client ID"
       - If prompted, configure OAuth consent screen first:
         - User Type: External
         - App name: GSC Explorer
         - Add your email as test user
         - Save and continue
       - **Application type: Web application**
       - Name: GSC Explorer
       - Click "Create"
       - **After creating**, click on the OAuth client to edit it
       - Scroll to "Authorized redirect URIs"
       - Click "+ ADD URI"
       - Add exactly: `http://localhost:8080/` (must include the trailing slash)
       - Click "SAVE"
       - **Important**: The URI must match EXACTLY - including the trailing slash `/`
    
    5. **Download the credentials**
       - Click the download icon (⬇️) next to your OAuth client
       - Save the file as `gsc_credentials.json`
       - Place it in this directory: `""" + str(creds_path.parent) + "`")
    
    st.markdown("---")
    
    st.markdown(f"**Expected file location:** `{creds_path}`")
    
    # Check again button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Check Again", type="primary"):
            st.rerun()
    
    st.markdown("---")
    st.markdown("💡 **Tip**: Once you've placed the file, click 'Check Again' above.")


def step2_authentication():
    """Step 2: Authenticate with Google."""
    st.header("Step 2: Authenticate with Google")
    st.markdown("Connect your Google account to access Google Search Console data.")
    
    # Verify credentials file still exists
    if not check_credentials_file():
        st.warning("⚠️ Credentials file not found. Please complete Step 1 first.")
        if st.button("← Back to Step 1"):
            st.session_state.setup_step = 1
            st.rerun()
        return
    
    # Check if already authenticated
    if 'gsc_service' in st.session_state and st.session_state.gsc_service is not None:
        st.success("✅ Already authenticated!")
        if st.button("Continue to Step 3 →", type="primary"):
            st.session_state.setup_step = 3
            st.rerun()
        return
    
    # Show info about OAuth flow
    st.info("""
    **What to expect:**
    - Click the button below to start authentication
    - A browser window will open automatically
    - Sign in with your Google account
    - Grant permissions to access Google Search Console
    - The browser will redirect and you'll see a success message
    - Return here to continue
    """)
    
    if st.button("🔐 Authenticate with Google", type="primary"):
        try:
            # Show warning about browser
            st.warning("⚠️ A browser window will open. Please complete the authentication there, then return here.")
            
            with st.spinner("Starting authentication... This may take a moment."):
                # This will open a browser and wait for OAuth callback
                service = get_gsc_service()
                
                # Store service in session state
                st.session_state.gsc_service = service
                
                # Verify the service works by trying to list sites
                try:
                    test_sites = list_sites(service)
                    if test_sites:
                        st.success(f"✅ Authentication successful! Found {len(test_sites)} GSC property/properties.")
                        st.session_state.setup_step = 3
                        st.rerun()
                    else:
                        st.warning("Authentication succeeded but no GSC properties found. Please ensure you have access to at least one property.")
                except Exception as e:
                    st.error(f"Authentication succeeded but couldn't access GSC: {e}")
                    logger.error(f"Error verifying GSC access: {e}", exc_info=True)
                    
        except FileNotFoundError as e:
            st.error("❌ Credentials file not found.")
            st.info("Please go back to Step 1 and ensure `gsc_credentials.json` is in the correct location.")
            if st.button("← Back to Step 1", key="back_to_step1_error"):
                st.session_state.setup_step = 1
                st.rerun()
        except RuntimeError as e:
            error_msg = str(e)
            st.error(f"❌ Authentication failed")
            st.markdown(f"**Error details:**\n```\n{error_msg}\n```")
            
            # Provide helpful guidance
            if 'redirect_uri' in error_msg.lower():
                st.info("""
                **This is a redirect URI configuration issue.**
                
                Please check your Google Cloud Console OAuth settings and ensure the redirect URIs are configured correctly.
                """)
            else:
                st.info("""
                **Troubleshooting tips:**
                - Make sure you have an active internet connection
                - Check that your credentials file is valid
                - Try closing any existing browser windows and try again
                - Ensure port 8090 is not blocked by a firewall
                """)
        except Exception as e:
            st.error(f"❌ Authentication failed: {e}")
            logger.error(f"Authentication error: {e}", exc_info=True)
            st.info("""
            **Troubleshooting tips:**
            - Make sure you have an active internet connection
            - Check that your credentials file is valid
            - Try closing any existing browser windows and try again
            - Ensure port 8090 is not blocked by a firewall
            """)


def step3_property_selection():
    """Step 3: Select GSC property."""
    st.header("Step 3: Select GSC Property")
    st.markdown("Choose which Google Search Console property you want to analyze.")
    
    # Get service - try session state first, then get fresh one
    service = None
    if 'gsc_service' in st.session_state and st.session_state.gsc_service is not None:
        service = st.session_state.gsc_service
    else:
        try:
            with st.spinner("Re-authenticating..."):
                service = get_gsc_service()
                st.session_state.gsc_service = service
        except Exception as e:
            st.error(f"Could not authenticate: {e}")
            st.info("Please go back to Step 2 and try authenticating again.")
            if st.button("← Back to Step 2"):
                st.session_state.setup_step = 2
                st.rerun()
            return
    
    try:
        with st.spinner("Loading properties..."):
            sites = list_sites(service)
        
        if not sites:
            st.warning("No properties found. Please ensure you have access to at least one GSC property.")
            return
        
        # Get previously selected site from session state or config
        previous_site = st.session_state.get('selected_site') or load_config().get('site_url')
        
        # Find index of previously selected site, or default to 0
        default_index = 0
        if previous_site and previous_site in sites:
            default_index = sites.index(previous_site)
        
        selected_site = st.selectbox(
            "Select a property:",
            options=sites,
            index=default_index
        )
        
        st.session_state.selected_site = selected_site
        
        # Show which site is selected
        st.info(f"Selected: **{selected_site}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back"):
                st.session_state.setup_step = 2
                st.rerun()
        
        with col2:
            if st.button("Continue to Step 4 →", type="primary"):
                # Save site URL to config
                config = load_config()
                config['site_url'] = selected_site
                save_config(config)
                
                st.session_state.setup_step = 4
                st.rerun()
    
    except Exception as e:
        st.error(f"Error loading properties: {e}")
        logger.error(f"Error in property selection: {e}", exc_info=True)
        st.info("If this persists, try going back to Step 2 and re-authenticating.")


def step4_keyword_import():
    """Step 4: Import keywords."""
    st.header("Step 4: Import Keywords")
    st.markdown("Configure how you want to import keywords from Google Search Console.")
    
    # Get service - try session state first, then get fresh one
    service = None
    if 'gsc_service' in st.session_state and st.session_state.gsc_service is not None:
        service = st.session_state.gsc_service
    else:
        try:
            with st.spinner("Re-authenticating..."):
                service = get_gsc_service()
                st.session_state.gsc_service = service
        except Exception as e:
            st.error(f"Could not authenticate: {e}")
            st.info("Please go back to Step 2 and try authenticating again.")
            if st.button("← Back to Step 2"):
                st.session_state.setup_step = 2
                st.rerun()
            return
    
    # Get selected site - prioritize session state, fallback to config
    if 'selected_site' not in st.session_state:
        # Try to get from config
        config = load_config()
        if config.get('site_url'):
            st.session_state.selected_site = config['site_url']
        else:
            st.error("Please complete property selection first.")
            st.session_state.setup_step = 3
            if st.button("← Back to Step 3"):
                st.rerun()
            return
    
    # Display which site will be used
    site_to_use = st.session_state.selected_site
    st.info(f"📌 **Importing keywords for:** `{site_to_use}`")
    st.markdown("---")
    
    # Date range selection
    st.subheader("Date Range")
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "From:",
            value=datetime.now() - timedelta(days=16*30),  # ~16 months ago
            max_value=datetime.now()
        )
    
    with col2:
        end_date = st.date_input(
            "To:",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    # Filters
    st.subheader("Filters")
    min_impressions = st.number_input(
        "Minimum Impressions per month:",
        min_value=0,
        value=50,
        help="Only import keywords with at least this many impressions"
    )
    
    min_clicks = st.number_input(
        "Minimum Clicks per month (optional):",
        min_value=0,
        value=0,
        help="Optional: Only import keywords with at least this many clicks"
    )
    
    keyword_pattern = st.text_input(
        "Keyword Pattern (optional):",
        value="",
        help="Optional: Regex pattern to filter keywords (e.g., 'data.*governance')"
    )
    
    if keyword_pattern == "":
        keyword_pattern = None
    
    # Estimate
    st.markdown("---")
    st.info("💡 **Tip**: Larger date ranges and lower thresholds will import more keywords and take longer.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.setup_step = 3
            st.rerun()
    
    with col2:
        if st.button("🚀 Start Import", type="primary"):
            import_keywords(
                service,
                st.session_state.selected_site,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                min_impressions,
                min_clicks if min_clicks > 0 else None,
                keyword_pattern
            )


def import_keywords(
    service,
    site_url: str,
    start_date: str,
    end_date: str,
    min_impressions: int,
    min_clicks: Optional[int],
    keyword_pattern: Optional[str]
):
    """Import keywords with progress display."""
    progress_container = st.container()
    status_container = st.container()
    
    keywords_imported = []
    
    def progress_callback(current_count, total_estimated):
        with progress_container:
            if total_estimated:
                progress = current_count / total_estimated
                st.progress(progress)
            else:
                st.progress(0.5)  # Indeterminate progress
    
    try:
        with status_container:
            st.info("Fetching keywords from Google Search Console...")
        
        keywords = fetch_keywords_with_pagination(
            service,
            site_url,
            start_date,
            end_date,
            min_impressions=min_impressions,
            min_clicks=min_clicks,
            keyword_pattern=keyword_pattern,
            progress_callback=progress_callback
        )
        
        with status_container:
            st.info(f"Found {len(keywords)} keywords. Saving to database...")
        
        # Save keywords
        import_criteria = {
            'start_date': start_date,
            'end_date': end_date,
            'min_impressions': min_impressions,
            'min_clicks': min_clicks,
            'keyword_pattern': keyword_pattern
        }
        
        save_keywords(keywords, site_url, import_criteria)
        
        # Update config
        config = load_config()
        config['import_filters'] = import_criteria
        config['date_range'] = {
            'start': start_date,
            'end': end_date
        }
        save_config(config)
        
        # Show success
        progress_container.empty()
        status_container.empty()
        
        st.success(f"✅ Successfully imported {len(keywords)} keywords!")
        
        st.markdown("---")
        st.markdown("### Import Summary")
        st.write(f"- **Total keywords**: {len(keywords)}")
        st.write(f"- **Date range**: {start_date} to {end_date}")
        st.write(f"- **Minimum impressions**: {min_impressions}")
        if min_clicks:
            st.write(f"- **Minimum clicks**: {min_clicks}")
        if keyword_pattern:
            st.write(f"- **Keyword pattern**: {keyword_pattern}")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Import More Keywords", use_container_width=True):
                # Stay in Step 4 to import more
                st.session_state.setup_step = 4
                st.rerun()
        with col2:
            if st.button("Continue to App →", type="primary", use_container_width=True):
                # Mark setup as complete and go to main app
                st.session_state.setup_complete = True
                st.session_state.setup_step = None  # Clear setup step
                st.rerun()
    
    except Exception as e:
        progress_container.empty()
        status_container.empty()
        st.error(f"Import failed: {e}")
        logger.error(f"Error importing keywords: {e}", exc_info=True)
        st.info("Please try again or adjust your filters.")

