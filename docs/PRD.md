# Product Requirements Document: GSC Explorer

**Version:** 1.0  
**Date:** November 2024  
**Status:** Draft

---

## 1. Executive Summary

### Problem Statement

Google Search Console (GSC) provides valuable SEO data through its API, but accessing and exploring this data is challenging:

- **GSC Web UI**: Limited filtering, no cross-keyword/page analysis, difficult to spot trends
- **Python Notebooks**: Require coding knowledge, complex setup, intimidating for non-technical users
- **Looker Studio**: Cannot handle the granularity and volume of keyword-page-time data effectively

Users need a simple, accessible tool to explore GSC data without the complexity of notebooks or the limitations of the native UI.

### Solution

GSC Explorer is a lightweight, open-source Streamlit application that provides an intuitive interface for exploring Google Search Console data. It focuses on one thing: making it easy to query, filter, and view keyword-page performance metrics over time.

### Core Hypothesis

> "Users don't need complex analytics or data pipelines. They need a simple way to explore GSC data to identify **monthly trends and patterns**. A focused, easy-to-use tool will solve this better than existing options."

### Core Constraint

> **Monthly Granularity Only**: This tool exclusively displays data at monthly granularity. We solve one problem well: identifying monthly trends. Daily, weekly, or other time periods are out of scope.

---

## 2. User Personas

### Primary Persona: SEO Analyst (Sarah)

- **Role**: SEO analyst at a mid-size company
- **Technical Skill**: Basic Python knowledge, comfortable with spreadsheets
- **Pain Points**: 
  - GSC UI doesn't let her compare multiple keywords easily
  - Wants to see which pages rank for specific keywords over time
  - Finds notebooks intimidating and time-consuming to set up
- **Goals**: Quickly identify trends, export data for further analysis
- **Use Case**: "I want to see which pages got impressions for my top 10 keywords this quarter"

### Secondary Persona: Marketing Manager (Mike)

- **Role**: Marketing manager overseeing SEO
- **Technical Skill**: Limited coding knowledge, Excel power user
- **Pain Points**:
  - Can't easily explore keyword-page relationships
  - Needs to understand performance trends without technical setup
- **Goals**: Self-service data exploration, no dependency on technical team
- **Use Case**: "I want to understand which keywords are driving traffic to which pages"

---

## 3. Product Goals & Objectives

### Primary Goals

1. **Accessibility**: Enable non-technical users to explore GSC data without coding
2. **Simplicity**: Focus on exploration, not analytics or automation
3. **Speed**: Fast setup and data retrieval
4. **Open Source**: Community-driven, transparent, extensible

### Success Metrics

- **Time to First Value**: < 5 minutes from installation to viewing data
- **User Satisfaction**: Users can complete exploration tasks without documentation
- **Adoption**: 100+ GitHub stars in first 3 months
- **Community**: Active issues/PRs from community

### Non-Goals (What We're NOT Building)

- ❌ **Daily, weekly, or any non-monthly granularity** (monthly only)
- ❌ Data warehousing or historical data storage
- ❌ Advanced analytics or ML predictions
- ❌ Automated reporting or alerts
- ❌ Multi-property management
- ❌ Data visualization beyond tables
- ❌ Integration with other tools (except export)

---

## 4. User Flows

### Flow 1: First-Time Setup (First-Run Mode)

```
1. User runs: streamlit run app.py
2. App checks:
   - Is token.json present? → No
   - Is database present? → No
   - Are keywords in database? → No
3. App enters "First-Run Mode"
4. Display welcome screen with setup steps:
   a. Step 0: Setup Credentials (if gsc_credentials.json missing)
      - Check if credentials file exists in project root
      - If missing: Show step-by-step instructions
      - Link to Google Cloud Console
      - Guide user to create OAuth client (Desktop app type)
      - Show expected file location
      - "Check Again" button to verify file placement
   b. Step 1: Authenticate with Google (OAuth flow)
      - Verify credentials file exists
      - Initiate OAuth flow
      - Store token.json
   c. Step 2: Select GSC property
      - List available properties
      - User selects property
      - Store in config.json
   d. Step 3: Import keywords with filters:
      - Date range selection (default: last 16 months)
      - Minimum impressions threshold (default: 50)
      - Option to import all keywords
      - Warning about API limits and estimated time
   d. Confirm import
   e. Handle API limits:
      - Pagination: Fetch in batches of 25K rows (max per request)
      - Rate limiting: Max 1,200 requests/minute (throttle if needed)
      - Date range chunking: Break large ranges into monthly chunks
      - Progress display: Show X of Y keywords imported
      - Error handling: Retry with exponential backoff on quota errors
   f. Store credentials and keywords
5. Transition to main app
```

### Flow 2: Normal Usage (Returning User)

```
1. User runs: streamlit run app.py
2. App checks:
   - Token exists? → Yes
   - Database exists? → Yes
   - Keywords present? → Yes
3. Load main app directly:
   - Load keywords from database
   - Display keyword selector
   - User selects keywords → Fetches data → Views results
```

### Flow 3: Re-authentication (Token Expired)

```
1. User runs app
2. Token expired or invalid
3. App detects error during API call
4. Show re-authentication prompt
5. User re-authenticates
6. Continue with normal flow
```

---

## 5. Features

### MVP Features (v1.0)

#### 5.1 First-Run Setup
- **OAuth Authentication**
  - Google OAuth2 flow
  - Token storage (`token.json`)
  - Automatic token refresh
  
- **GSC Property Selection**
  - List available properties
  - Select property to analyze
  - Store selection in config

- **Keyword Import**
  - Date range picker (default: last 16 months)
  - Filter options:
    - Minimum impressions per month (default: 50)
    - Minimum clicks per month (optional)
    - Keyword pattern matching (optional)
  - **API Limit Handling**:
    - Show estimated import time based on filters
    - Warning if estimated keywords > 100K (may take time)
    - Real-time progress: "Fetching batch X... (Y keywords so far)"
    - Pagination indicator: "Page 1 of ~Z"
    - Rate limit status: "API calls: X/minute"
  - Progress indicator during import with:
    - Current batch number
    - Total keywords fetched so far
    - Estimated time remaining
    - Option to cancel
  - Import summary (X keywords imported, Y batches fetched)
  - Option to re-import/refresh keywords

#### 5.2 Main Application
- **Keyword Selection**
  - Load keywords from database
  - Search/filter keywords
  - Multi-select with checkboxes
  - "Select All" option
  - Display count of selected keywords

- **Data Fetching**
  - Fetch page-level data for selected keywords
  - **Monthly aggregation only** (default: Oct 2024 onwards)
  - One row per month per keyword+page combination
  - Progress indicator
  - Error handling with retry logic

- **Results Display**
  - Table format: Keyword | Page | Metric | Monthly Columns (2024-10, 2024-11, ...) | TOTAL
  - **Monthly granularity only** - each column represents one month
  - Filters:
    - Keyword dropdown (single select)
    - Page multi-select
    - Metric dropdown (single select)
  - Column totals (TOTAL column summing across all months)
  - Built-in download (CSV via Streamlit)
  - Sortable columns

- **Configuration**
  - GSC Site URL display/edit
  - Date range display (read-only, set at import)
  - Option to refresh keywords

### Future Enhancements (Post-MVP)

- Keyword import filters:
  - Country filter
  - Device type filter
  - Position range filter
- Export formats:
  - Excel (.xlsx)
  - JSON
- Performance optimizations:
  - Caching API responses
  - Batch API calls
- UI improvements:
  - Dark mode
  - Column visibility toggle
  - Custom monthly date ranges per query

**Note**: All enhancements maintain monthly granularity. Daily/weekly views are explicitly out of scope.

---

## 6. Technical Requirements

### 6.1 Architecture

```
┌─────────────────────────────────────────┐
│         Streamlit App (UI)              │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────┐ │
│  │ Setup Module │  │ Main App Module │ │
│  │ (First Run)  │  │  (Normal Mode)  │ │
│  └──────────────┘  └─────────────────┘ │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐  │
│  │      GSC API Client Module        │  │
│  │  - Authentication                 │  │
│  │  - Data Fetching                 │  │
│  │  - Aggregation                   │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────┐ │
│  │   Database   │  │  Config/State   │  │
│  │  (SQLite)    │  │  (JSON files)   │  │
│  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────┘
```

### 6.2 Data Storage

- **SQLite Database** (`gsc_analytics.db`)
  - Table: `keywords`
    - `keyword` (TEXT, PRIMARY KEY)
    - `imported_at` (TIMESTAMP)
    - `import_criteria` (TEXT, JSON)
  
- **Configuration Files**
  - `token.json`: OAuth credentials
  - `config.json`: App configuration
    - `site_url`: GSC property URL
    - `date_range`: Import date range
    - `import_filters`: Import criteria used

### 6.3 Dependencies

- `streamlit`: UI framework
- `pandas`: Data manipulation
- `google-api-python-client`: GSC API
- `google-auth`: Authentication
- `sqlite3`: Database (built-in)

### 6.4 API Usage & Limits

- **GSC Search Analytics API**
  - Endpoint: `searchanalytics().query()`
  - Dimensions: `query`, `page`, `date` (daily data from API)
  - Metrics: `clicks`, `impressions`, `position`, `ctr`
  - **Aggregation**: Daily API data is aggregated to monthly totals (sum for clicks/impressions, average for position/ctr)
  - **Constraint**: API returns daily data, but we only display monthly aggregates

- **API Limits**:
  - **Row Limit**: 25,000 rows per request (hard limit)
  - **Rate Limits**: 
    - 1,200 queries per minute (QPM) per site/user
    - 30M queries per day per project (not a concern for our use case)
  - **Strategies to Handle Limits**:
    - **Pagination**: Use `startRow` parameter to fetch in batches of 25K
    - **Rate Throttling**: Limit to ~1,000 requests/minute (safety margin)
    - **Date Range Chunking**: Break large date ranges into monthly chunks
    - **Progressive Loading**: Show progress and allow cancellation
    - **Error Handling**: Exponential backoff on quota errors

### 6.5 Performance Considerations

- **Keyword Import** (First-Run):
  - **Pagination Strategy**:
    - Fetch keywords in batches of 25K rows per request
    - Use `startRow` parameter: 0, 25000, 50000, etc.
    - Continue until API returns < 25K rows (last page)
  - **Rate Limiting**:
    - Throttle to ~1,000 requests/minute (safety margin below 1,200 QPM)
    - Add delays between batches if needed
    - Show "Rate limit: X requests/minute" in UI
  - **Date Range Handling**:
    - For keyword import: Use aggregated query (no date dimension) or monthly chunks
    - Query without date dimension returns all-time aggregated keywords
    - Apply filters (impressions threshold) server-side via API filters
  - **Progress Feedback**:
    - Real-time progress: "Fetched X keywords (estimated Y total)"
    - Estimated time remaining
    - Option to cancel import
  - **Error Handling**:
    - Detect quota exceeded errors (429 status)
    - Exponential backoff: Wait 1s, 2s, 4s, 8s before retry
    - Max retries: 3 attempts per batch
    - User-friendly error messages with guidance
  
- **Data Fetching** (Normal Usage):
  - One API call per keyword per month
  - Monthly aggregation reduces total calls needed
  - Progress indicator for multiple keywords
  - Parallel processing (future enhancement)
  - Caching (future enhancement)

---

## 7. User Interface Design

### 7.1 First-Run Setup Screens

#### Screen 1: Welcome Screen
```
┌─────────────────────────────────────────────────────────────┐
│  GSC Explorer 🚀                                           │
│                                                             │
│  Welcome! Let's get you set up in 3 simple steps:          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✅ Step 1: Authenticate with Google                │   │
│  │    Connect your Google account to access GSC data  │   │
│  │    [Authenticate]                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ⏳ Step 2: Select GSC Property                    │   │
│  │    Choose which Search Console property to analyze │   │
│  │    [Not Started]                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ⏳ Step 3: Import Keywords                         │   │
│  │    Fetch keywords based on your criteria           │   │
│  │    [Not Started]                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Start Setup]                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Screen 2: Authentication Flow
```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Authenticate with Google                           │
│                                                             │
│  Click the button below to authenticate with Google.        │
│  You'll be redirected to Google's sign-in page.             │
│                                                             │
│  [🔐 Authenticate with Google]                              │
│                                                             │
│  ℹ️  This will open a browser window for authentication.    │
│                                                             │
│  Status: ⏳ Waiting for authentication...                   │
│                                                             │
│  [← Back]  [Skip for now]                                  │
└─────────────────────────────────────────────────────────────┘
```

#### Screen 3: Property Selection
```
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Select GSC Property                                │
│                                                             │
│  Select the Google Search Console property you want to      │
│  analyze:                                                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🔍 Search properties...                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Available Properties:                                       │
│                                                             │
│  ☐ sc-domain:example.com                                    │
│  ☐ https://www.example.com                                 │
│  ☐ https://blog.example.com                                │
│  ☐ sc-domain:anothersite.com                               │
│                                                             │
│  Selected: sc-domain:example.com                            │
│                                                             │
│  [← Back]  [Continue →]                                    │
└─────────────────────────────────────────────────────────────┘
```

#### Screen 4: Keyword Import Configuration
```
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Import Keywords                                    │
│                                                             │
│  Configure how you want to import keywords:                 │
│                                                             │
│  Date Range:                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ From: [2024-10-01 ▼]  To: [2025-10-31 ▼]          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Filters:                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Minimum Impressions: [50] per month                │   │
│  │ Minimum Clicks:      [  ] per month (optional)     │   │
│  │ Keyword Pattern:     [  ] (optional)               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Import Options:                                            │
│  ☑ Import all keywords matching criteria                   │
│  ☐ Import top 10,000 keywords only                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ⚠️  Estimated Keywords: ~8,500                      │   │
│  │ ⏱️  Estimated Time: ~2-3 minutes                   │   │
│  │ 📊 API Calls: ~1 batch (within limits)              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [← Back]  [Start Import]                                  │
└─────────────────────────────────────────────────────────────┘
```

#### Screen 5: Import Progress
```
┌─────────────────────────────────────────────────────────────┐
│  Importing Keywords...                                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│  │                   60% Complete                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Current Status:                                            │
│  • Fetching batch 1 of 1...                                 │
│  • Keywords fetched: 5,100 / ~8,500                        │
│  • API calls: 1 / 1                                        │
│  • Rate limit: 1 request/minute (within limits)             │
│                                                             │
│  Estimated time remaining: ~30 seconds                     │
│                                                             │
│  [Cancel Import]                                            │
└─────────────────────────────────────────────────────────────┘
```

#### Screen 6: Import Complete
```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Import Complete!                                         │
│                                                             │
│  Successfully imported 8,547 keywords                       │
│                                                             │
│  Summary:                                                   │
│  • Total keywords: 8,547                                    │
│  • Batches fetched: 1                                       │
│  • Date range: Oct 2024 - Oct 2025                          │
│  • Filter: Min 50 impressions/month                         │
│                                                             │
│  [Continue to App →]                                        │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Main Application Interface

#### Main Screen Layout
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  GSC Explorer 📊                                    [⚙️ Settings] [🔄 Refresh]│
├──────────────────────────┬───────────────────────────────────────────────────┤
│                          │                                                   │
│  KEYWORD SELECTION       │  RESULTS                                          │
│                          │                                                   │
│  🔍 Search keywords...   │  Filters:                                         │
│  ┌─────────────────────┐ │  ┌──────────────┐ ┌──────────────┐ ┌──────────┐ │
│  │ data governance     │ │  │ Keyword: All │ │ Page: [ ]   │ │ Metric:  │ │
│  └─────────────────────┘ │  │              │ │ [Select...] │ │ All ▼   │ │
│                          │  └──────────────┘ └──────────────┘ └──────────┘ │
│  ☑ Select All            │                                                   │
│  ─────────────────────── │  Showing 1,234 of 1,234 rows                     │
│  ☑ active data           │                                                   │
│  ☐ agile data            │  ┌─────────────────────────────────────────────┐ │
│  ☐ data governance       │  │ Keyword │ Page │ Metric │ 2024-10 │ 2024-11 │ │
│  ☐ data mesh             │  ├─────────┼──────┼────────┼─────────┼─────────┤ │
│  ☐ data quality          │  │ data    │ /pg1 │ clicks │   150   │   180   │ │
│  ☐ metadata              │  │ gov     │      │        │         │         │ │
│  ☐ ... (8,542 more)      │  ├─────────┼──────┼────────┼─────────┼─────────┤ │
│                          │  │ data    │ /pg1 │ impres │  5000   │  6000   │ │
│  Selected: 5 keywords    │  │ gov     │      │ sions  │         │         │ │
│                          │  ├─────────┼──────┼────────┼─────────┼─────────┤ │
│  ─────────────────────── │  │ ...     │ ...  │ ...   │   ...   │   ...   │ │
│                          │  └─────────────────────────────────────────────┘ │
│  GSC Configuration:      │                                                   │
│  Site URL:               │  [📥 Download CSV]                                 │
│  sc-domain:example.com   │                                                   │
│                          │                                                   │
│  [🚀 Fetch Data]         │                                                   │
│                          │                                                   │
└──────────────────────────┴───────────────────────────────────────────────────┘
```

#### Sidebar Detail (Keyword Selection)
```
┌─────────────────────────────────────┐
│  KEYWORD SELECTION                  │
│                                     │
│  🔍 Search keywords...              │
│  ┌───────────────────────────────┐ │
│  │ data                          │ │
│  └───────────────────────────────┘ │
│                                     │
│  8,547 keywords found               │
│                                     │
│  ☑ Select All                      │
│  ─────────────────────────────────  │
│                                     │
│  ☑ active data governance          │
│  ☑ agile data governance           │
│  ☑ data catalog                    │
│  ☑ data contract                   │
│  ☑ data governance                 │
│  ☐ data governance framework       │
│  ☐ data governance tools           │
│  ☐ data lineage                    │
│  ☐ data mesh                       │
│  ☐ data quality                    │
│  ... (scrollable)                  │
│                                     │
│  ─────────────────────────────────  │
│  5 keyword(s) selected              │
│                                     │
│  ─────────────────────────────────  │
│  GSC Configuration:                 │
│                                     │
│  Site URL:                          │
│  ┌───────────────────────────────┐ │
│  │ sc-domain:example.com         │ │
│  └───────────────────────────────┘ │
│                                     │
│  [🚀 Fetch Data]                   │
└─────────────────────────────────────┘
```

#### Results Table Detail
```
┌──────────────────────────────────────────────────────────────────────────────┐
│  RESULTS                                                                      │
│                                                                               │
│  Filters:                                                                     │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐        │
│  │ 🔍 Keyword: All ▼ │ │ 🔍 Page: [Select] │ │ 🔍 Metric: All ▼ │        │
│  └────────────────────┘ └────────────────────┘ └────────────────────┘        │
│                                                                               │
│  Showing 1,234 of 1,234 rows                                                  │
│                                                                               │
│  ┌──────────────┬──────────────────────┬──────────┬─────────┬─────────┬────┐│
│  │ Keyword      │ Page                 │ Metric   │ 2024-10 │ 2024-11 │... ││
│  ├──────────────┼──────────────────────┼──────────┼─────────┼─────────┼────┤│
│  │ data         │ /blog/data-gov       │ clicks   │   150   │   180   │... ││
│  │ governance   │                      │          │         │         │    ││
│  ├──────────────┼──────────────────────┼──────────┼─────────┼─────────┼────┤│
│  │ data         │ /blog/data-gov       │ impress  │  5000   │  6000   │... ││
│  │ governance   │                      │ ions     │         │         │    ││
│  ├──────────────┼──────────────────────┼──────────┼─────────┼─────────┼────┤│
│  │ data         │ /blog/data-gov       │ position │   3.2   │   3.0   │... ││
│  │ governance   │                      │          │         │         │    ││
│  ├──────────────┼──────────────────────┼──────────┼─────────┼─────────┼────┤│
│  │ data         │ /blog/data-gov       │ ctr      │  0.03   │  0.03   │... ││
│  │ governance   │                      │          │         │         │    ││
│  ├──────────────┼──────────────────────┼──────────┼─────────┼─────────┼────┤│
│  │ ...          │ ...                  │ ...      │   ...   │   ...   │... ││
│  └──────────────┴──────────────────────┴──────────┴─────────┴─────────┴────┘│
│                                                                               │
│  [📥 Download CSV]  (Built-in Streamlit download button)                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### Fetching Data Progress
```
┌─────────────────────────────────────────────────────────────┐
│  Fetching Data...                                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│  │                   60% Complete                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Fetching data for: data governance (3/5)                  │
│                                                             │
│  Progress:                                                  │
│  • Keywords processed: 3 / 5                               │
│  • API calls: 48 / 80 (16 months × 5 keywords)            │
│  • Estimated time remaining: ~45 seconds                    │
│                                                             │
│  [Cancel]                                                   │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Error States

#### Authentication Error
```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  Authentication Failed                                  │
│                                                             │
│  Unable to authenticate with Google.                        │
│                                                             │
│  Possible reasons:                                          │
│  • Token expired or invalid                                │
│  • Network connectivity issues                             │
│  • Permissions not granted                                 │
│                                                             │
│  [Try Again]  [Help]                                       │
└─────────────────────────────────────────────────────────────┘
```

#### API Quota Exceeded
```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  API Rate Limit Exceeded                               │
│                                                             │
│  You've hit the Google Search Console API rate limit.       │
│                                                             │
│  Current status:                                            │
│  • Rate limit: 1,200 requests/minute                       │
│  • Your usage: ~1,200 requests/minute                      │
│                                                             │
│  What to do:                                               │
│  • Wait a few minutes and try again                        │
│  • Reduce the number of keywords selected                  │
│  • Use more restrictive filters                            │
│                                                             │
│  [Retry]  [Reduce Selection]                               │
└─────────────────────────────────────────────────────────────┘
```

#### No Keywords Found
```
┌─────────────────────────────────────────────────────────────┐
│  ℹ️  No Keywords Found                                      │
│                                                             │
│  No keywords match your current filters.                   │
│                                                             │
│  Try:                                                       │
│  • Adjusting your search term                              │
│  • Clearing filters                                        │
│  • Importing keywords with different criteria               │
│                                                             │
│  [Clear Filters]  [Import Keywords]                        │
└─────────────────────────────────────────────────────────────┘
```

### 7.4 UI Components

#### Filter Bar (Results Page)
```
┌─────────────────────────────────────────────────────────────┐
│  Filters:                                                    │
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │ 🔍 Keyword           │  │ 🔍 Page (Multi-select)       │ │
│  │ ┌──────────────────┐ │  │ ┌──────────────────────────┐ │ │
│  │ │ All            ▼ │ │  │ │ /blog/data-gov          │ │ │
│  │ └──────────────────┘ │  │ │ /docs/data-gov          │ │ │
│  └──────────────────────┘  │ │ /guides/data-gov        │ │ │
│                            │ └──────────────────────────┘ │ │
│  ┌──────────────────────┐  └──────────────────────────────┘ │
│  │ 🔍 Metric            │                                   │
│  │ ┌──────────────────┐ │                                   │
│  │ │ All            ▼ │ │                                   │
│  │ └──────────────────┘ │                                   │
│  └──────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

#### Results Table with TOTAL Column
```
┌──────────┬──────────────┬──────────┬─────────┬─────────┬─────────┬───────┐
│ Keyword  │ Page         │ Metric   │ 2024-10 │ 2024-11 │ 2024-12 │ TOTAL │
├──────────┼──────────────┼──────────┼─────────┼─────────┼─────────┼───────┤
│ data     │ /blog/...    │ clicks   │   150   │   180   │   200   │  530  │
│ governance│              │          │         │         │         │       │
├──────────┼──────────────┼──────────┼─────────┼─────────┼─────────┼───────┤
│ data     │ /blog/...    │ impress  │  5000   │  6000   │  7000   │ 18000 │
│ governance│              │ ions     │         │         │         │       │
└──────────┴──────────────┴──────────┴─────────┴─────────┴─────────┴───────┘
```

---

## 8. User Experience Guidelines

### 8.1 Design Principles

- **Clean, focused interface**: No clutter, focus on core functionality
- **Fast keyword search**: Real-time filtering as user types
- **Clear visual feedback**: Loading states, progress bars, status messages
- **Intuitive filters**: Dropdowns, multi-select with clear labels
- **Export-ready data**: One-click download via Streamlit's built-in functionality

### 8.2 Error Handling UX

- **Token expired**: Clear re-auth prompt with one-click retry
- **API errors**: Retry logic with exponential backoff, user-friendly messages
- **No data**: Helpful guidance on next steps (adjust filters, re-import)
- **Network issues**: Clear error messages with retry options
- **Quota exceeded**: Show current usage, suggest reducing selection, retry option

---

## 9. Open Source Considerations

### 9.1 Repository Structure

```
gsc-explorer/
├── README.md
├── LICENSE (MIT)
├── requirements.txt
├── setup.py (optional)
├── .env.example
├── app.py (main Streamlit app)
├── modules/
│   ├── setup.py (first-run logic)
│   ├── gsc_client.py (API client)
│   └── utils.py (helpers)
├── config/
│   └── config.example.json
└── docs/
    ├── SETUP.md
    ├── CONTRIBUTING.md
    └── API.md
```

### 9.2 Documentation Requirements

- **README.md**: Quick start, features, screenshots
- **SETUP.md**: Detailed setup instructions
- **CONTRIBUTING.md**: Contribution guidelines
- **API.md**: API usage and rate limits
- **TROUBLESHOOTING.md**: Common issues and solutions

### 9.3 Security Considerations

- **Credentials**: Never commit `token.json` or `gsc_credentials.json`
- **`.gitignore`**: Include sensitive files
- **Environment variables**: Support for config via env vars
- **OAuth flow**: Secure, standard Google OAuth2

### 9.4 Community

- **Issues**: Bug reports, feature requests
- **Discussions**: Q&A, use cases
- **PRs**: Welcome contributions
- **Examples**: User-submitted use cases

---

## 10. Success Criteria

### MVP Launch Criteria

- [ ] First-run setup works end-to-end
- [ ] Can import keywords with filters
- [ ] Can fetch and display data for selected keywords
- [ ] Filters work correctly
- [ ] Export functionality works
- [ ] Documentation is complete
- [ ] README has clear setup instructions
- [ ] Example config files provided

### Post-Launch Success Metrics

- **Adoption**: GitHub stars, forks, downloads
- **Engagement**: Active issues, PRs, discussions
- **User Feedback**: Positive reviews, feature requests
- **Reliability**: Low bug reports, high uptime

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GSC API rate limits (1,200 QPM) | High | Throttle to 1,000 QPM; pagination for large imports; exponential backoff on errors |
| Row limit (25K per request) | High | Pagination with `startRow` parameter; fetch in batches |
| Large keyword sets (>100K) | Medium | Show warnings; allow cancellation; estimate time upfront; use server-side filters |
| Token expiration | Medium | Auto-refresh logic; clear re-auth flow |
| Quota exceeded errors | Medium | Exponential backoff retry; user-friendly error messages; suggest reducing filters |
| User confusion | Medium | Clear documentation; helpful error messages; progress indicators |
| API changes | Low | Version pinning; monitor API updates |

---

## 12. Timeline & Milestones

### Phase 1: MVP (Weeks 1-2)
- First-run setup flow
- Keyword import with filters
- Main app functionality
- Basic documentation

### Phase 2: Polish (Week 3)
- Error handling improvements
- UX refinements
- Documentation completion
- Testing

### Phase 3: Launch (Week 4)
- Open source preparation
- README and docs
- Example configurations
- Initial release

---

## 13. Appendix

### 13.1 Glossary

- **GSC**: Google Search Console
- **First-Run Mode**: Initial setup flow for new users
- **Keyword Import**: Fetching and storing keywords from GSC API
- **Monthly Aggregation**: Combining daily API data into monthly totals (the only granularity we support)
- **Monthly Granularity**: Data displayed as one column per month - this is the only time period supported by the tool

### 13.2 References

- [GSC API Documentation](https://developers.google.com/webmaster-tools/search-console-api-original)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google OAuth2](https://developers.google.com/identity/protocols/oauth2)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Nov 2024 | Initial | First draft |

