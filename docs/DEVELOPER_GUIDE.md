# Developer Guide: GSC Explorer

**Version:** 1.0  
**Date:** November 2024

---

## 1. Project Philosophy

### Core Principles

1. **Simplicity First**: This is a localhost-only, single-user tool. No authentication, no multi-tenancy, no scaling concerns.
2. **Marketer's Tool**: Built for non-technical users who need quick access to GSC data, not developers.
3. **Focused Scope**: We solve one problem well - monthly trend exploration. Nothing more.
4. **Local-First**: Everything runs locally. No cloud dependencies, no external services.

### What This Means for Development

- ✅ **DO**: Keep code simple and readable
- ✅ **DO**: Prioritize user experience over code elegance
- ✅ **DO**: Use straightforward patterns (no over-engineering)
- ✅ **DO**: Add helpful error messages for non-technical users
- ❌ **DON'T**: Add authentication layers (not needed)
- ❌ **DON'T**: Optimize for scale (single user)
- ❌ **DON'T**: Add enterprise features (not the use case)
- ❌ **DON'T**: Over-abstract (YAGNI principle)

---

## 2. Architecture Principles

### 2.1 Application Type

- **Type**: Single-page Streamlit application
- **Deployment**: Localhost only (`streamlit run app.py`)
- **Users**: One user per instance (the person running it)
- **Data**: Stored locally (SQLite + JSON config files)

### 2.2 Code Organization

```
gsc-explorer/
├── app.py                 # Main Streamlit app (entry point)
├── modules/
│   ├── __init__.py
│   ├── setup.py          # First-run setup logic
│   ├── gsc_client.py     # GSC API client (auth + data fetching)
│   └── utils.py          # Helper functions
├── config/
│   └── config.example.json
├── data/                  # Created at runtime
│   └── keywords.db       # SQLite database
├── requirements.txt
├── README.md
└── .gitignore
```

### 2.3 Module Responsibilities

- **`app.py`**: UI orchestration, routing between setup/main modes
- **`modules/setup.py`**: First-run flow (auth, property selection, keyword import)
- **`modules/gsc_client.py`**: All GSC API interactions (isolated, testable)
- **`modules/utils.py`**: Pure utility functions (path resolution, data transforms)

### 2.4 State Management

- **Session State**: Use Streamlit's `st.session_state` for:
  - Selected keywords
  - Current results
  - Configuration (site_url, etc.)
- **Persistent State**: 
  - `token.json`: OAuth credentials
  - `config.json`: App configuration
  - `data/keywords.db`: Keywords database

---

## 3. Coding Standards

### 3.1 Python Style

- **PEP 8**: Follow Python style guide
- **Type Hints**: Use type hints for function parameters and returns
- **Docstrings**: Use Google-style docstrings for all functions
- **Line Length**: Max 100 characters (Streamlit UI code can be longer if needed)

### 3.2 Function Design

**Good:**
```python
def fetch_keyword_data(keyword: str, site_url: str) -> pd.DataFrame:
    """
    Fetch page-level data for a keyword from GSC API.
    
    Args:
        keyword: Search query keyword
        site_url: GSC property URL
        
    Returns:
        DataFrame with columns: query, page, year_month, clicks, impressions, position, ctr
    """
    # Implementation
```

**Bad:**
```python
def get_data(kw, url):  # No types, no docstring
    # Implementation
```

### 3.3 Error Handling

- **User-Friendly Messages**: All errors should be understandable by non-technical users
- **Graceful Degradation**: If something fails, show helpful guidance, don't crash
- **Logging**: Use Python's `logging` module for debugging (not `print`)

**Good:**
```python
try:
    data = fetch_from_api()
except Exception as e:
    st.error("Unable to fetch data from Google Search Console.")
    st.info(f"Error: {str(e)}. Please check your internet connection and try again.")
    logger.error(f"API error: {e}", exc_info=True)
    return pd.DataFrame()
```

**Bad:**
```python
data = fetch_from_api()  # Will crash if API fails
```

### 3.4 Constants and Configuration

- **Magic Numbers**: Define constants at module level
- **Config Values**: Store in `config.json` or environment variables
- **Default Values**: Make defaults sensible for typical use case

```python
# Good
DEFAULT_MIN_IMPRESSIONS = 50
DEFAULT_DATE_RANGE_MONTHS = 16
MAX_ROWS_PER_REQUEST = 25000

# Bad
if impressions > 50:  # Magic number
```

---

## 4. GSC API Best Practices

### 4.1 Rate Limiting

- **Always throttle**: Never exceed 1,000 requests/minute (safety margin)
- **Batch operations**: Group API calls when possible
- **Progress feedback**: Show user what's happening

```python
# Good
import time

def fetch_with_throttle(requests_per_minute=1000):
    delay = 60 / requests_per_minute
    for item in items:
        result = api_call(item)
        time.sleep(delay)  # Throttle
        yield result
```

### 4.2 Pagination

- **Always handle pagination**: Use `startRow` parameter
- **Check row count**: If < 25K rows returned, you're done
- **Progress tracking**: Show which batch you're on

```python
# Good
def fetch_all_keywords(service, site_url, filters):
    all_keywords = []
    start_row = 0
    batch_size = 25000
    
    while True:
        response = query_api(start_row=start_row, row_limit=batch_size)
        keywords = extract_keywords(response)
        all_keywords.extend(keywords)
        
        if len(keywords) < batch_size:
            break  # Last page
            
        start_row += batch_size
        time.sleep(0.06)  # Throttle
    
    return all_keywords
```

### 4.3 Error Handling

- **Retry logic**: Exponential backoff for quota errors
- **User feedback**: Clear messages about what went wrong
- **Graceful failure**: Don't crash, return empty DataFrame

```python
# Good
def fetch_with_retry(service, site_url, keyword, max_retries=3):
    for attempt in range(max_retries):
        try:
            return api_call(service, site_url, keyword)
        except HttpError as e:
            if e.resp.status == 429:  # Quota exceeded
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
                continue
            else:
                raise
    raise Exception("Max retries exceeded")
```

### 4.4 Data Aggregation

- **Monthly aggregation**: Always aggregate daily API data to monthly
- **Consistent logic**: Sum clicks/impressions, average position/CTR
- **One row per month**: Ensure exactly 1 row per keyword+page+month

---

## 5. Streamlit Best Practices

### 5.1 Performance

- **Cache expensive operations**: Use `@st.cache_data` for:
  - Database queries
  - API calls that don't change frequently
  - Data transformations
- **Avoid re-running**: Don't put expensive operations in main script body

```python
# Good
@st.cache_data
def load_keywords():
    return fetch_from_database()

# Bad
def main():
    keywords = fetch_from_database()  # Runs every time user interacts
```

### 5.2 User Experience

- **Loading states**: Always show progress for long operations
- **Clear labels**: Use descriptive labels for all UI elements
- **Helpful defaults**: Pre-fill sensible values
- **Error prevention**: Disable buttons when inputs invalid

```python
# Good
if not site_url or not selected_keywords:
    st.button("Fetch Data", disabled=True)
else:
    st.button("Fetch Data", type="primary")

# Bad
st.button("Fetch Data")  # Works even when invalid
```

### 5.3 Layout

- **Sidebar for controls**: Keep main area for results
- **Consistent spacing**: Use `st.markdown("---")` for sections
- **Collapsible sections**: Use `st.expander()` for optional info

---

## 6. Testing Strategy

### 6.1 Testing Philosophy

- **Focus on critical paths**: Test first-run setup and data fetching
- **Mock external dependencies**: Mock GSC API calls in tests
- **Test utilities**: Test pure functions (data transforms, aggregations)

### 6.2 What to Test

- ✅ **GSC API client**: Mock API responses, test error handling
- ✅ **Data aggregation**: Test monthly aggregation logic
- ✅ **Pagination**: Test pagination logic with mock data
- ✅ **Utils**: Test helper functions
- ❌ **Streamlit UI**: Don't test UI rendering (too complex, low value)

### 6.3 Test Structure

```
tests/
├── __init__.py
├── test_gsc_client.py
├── test_utils.py
└── fixtures/
    └── mock_api_responses.json
```

---

## 7. Documentation Standards

### 7.1 Code Comments

- **Why, not what**: Comments should explain reasoning, not restate code
- **Complex logic**: Comment non-obvious business logic
- **API quirks**: Document GSC API limitations and workarounds

```python
# Good
# GSC API returns daily data, but we only display monthly aggregates.
# We aggregate by summing clicks/impressions and averaging position/CTR.
monthly_data = aggregate_to_monthly(daily_data)

# Bad
# This aggregates data to monthly
monthly_data = aggregate_to_monthly(daily_data)
```

### 7.2 README Requirements

- **Quick start**: Get running in < 5 minutes
- **Screenshots**: Show what the app looks like
- **Troubleshooting**: Common issues and solutions
- **Limitations**: What the tool doesn't do

### 7.3 Inline Documentation

- **Function docstrings**: Every function should have a docstring
- **Module docstrings**: Explain module purpose
- **Complex sections**: Comment why, not what

---

## 8. Security Considerations

### 8.1 Credentials

- **Never commit**: `token.json`, `gsc_credentials.json` must be in `.gitignore`
- **Local only**: Credentials stay on user's machine
- **No sharing**: Don't build features to share credentials

### 8.2 Input Validation

- **Sanitize inputs**: Validate user inputs before API calls
- **SQL injection**: Use parameterized queries (SQLite handles this)
- **Path traversal**: Validate file paths

```python
# Good
def get_db_path():
    base_dir = Path(__file__).parent.parent
    db_path = base_dir / 'data' / 'keywords.db'
    # Validate path is within project directory
    if not str(db_path).startswith(str(base_dir)):
        raise ValueError("Invalid database path")
    return db_path
```

---

## 9. Performance Guidelines

### 9.1 Database

- **Indexes**: Add indexes on frequently queried columns
- **Batch operations**: Use transactions for multiple inserts
- **Connection management**: Close connections properly

```python
# Good
conn = sqlite3.connect(DB_PATH)
try:
    conn.executemany("INSERT INTO keywords VALUES (?)", keyword_list)
    conn.commit()
finally:
    conn.close()
```

### 9.2 API Calls

- **Batch when possible**: Group related calls
- **Cache responses**: Cache keyword lists, property lists
- **Progress feedback**: Show progress for long operations

### 9.3 Memory

- **Stream large datasets**: Don't load everything into memory
- **Clear session state**: Clean up old data from session state
- **Pagination**: Paginate large keyword lists in UI

---

## 10. Common Patterns

### 10.1 First-Run Detection

```python
def is_first_run():
    """Check if this is the first time running the app."""
    token_exists = os.path.exists(TOKEN_FILE)
    db_exists = os.path.exists(DB_PATH)
    has_keywords = False
    
    if db_exists:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("SELECT COUNT(*) FROM keywords")
        has_keywords = cursor.fetchone()[0] > 0
        conn.close()
    
    return not (token_exists and db_exists and has_keywords)
```

### 10.2 Progress Display

```python
def show_progress(current, total, operation="Processing"):
    """Display progress bar and status."""
    progress = current / total if total > 0 else 0
    st.progress(progress)
    st.caption(f"{operation}: {current} / {total} ({progress*100:.1f}%)")
```

### 10.3 Error Display

```python
def show_error(error: Exception, user_message: str):
    """Display user-friendly error message."""
    st.error(user_message)
    with st.expander("Technical Details (for debugging)"):
        st.code(str(error))
    logger.error(f"Error: {error}", exc_info=True)
```

---

## 11. Development Workflow

### 11.1 Setup

1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (or use existing `/sep2025/bin/activate`)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `config/config.example.json` to `config.json`
6. Run: `streamlit run app.py`

### 11.2 Development

- **Iterate quickly**: Make changes, see results immediately
- **Test manually**: Click through the UI, test edge cases
- **Check logs**: Use Streamlit's built-in logging
- **Debug mode**: Run with `streamlit run app.py --logger.level=debug`

### 11.3 Before Committing

- [ ] Code follows style guide
- [ ] All functions have docstrings
- [ ] Error handling in place
- [ ] No hardcoded credentials
- [ ] `.gitignore` updated
- [ ] README updated if needed

---

## 12. Open Source Considerations

### 12.1 Code Quality

- **Readable code**: Future contributors should understand it easily
- **Clear structure**: Logical organization, consistent patterns
- **Good comments**: Explain why, not what

### 12.2 Contributing

- **Small PRs**: One feature/fix per PR
- **Clear descriptions**: Explain what and why
- **Tests**: Add tests for new features
- **Documentation**: Update docs if needed

### 12.3 Maintenance

- **Keep dependencies updated**: Regular security updates
- **Monitor API changes**: GSC API may change
- **User feedback**: Listen to issues and feature requests

---

## 13. Anti-Patterns to Avoid

### ❌ Over-Engineering

```python
# Bad: Unnecessary abstraction
class KeywordFetcherFactory:
    def create_fetcher(self, type):
        if type == "gsc":
            return GSCKeywordFetcher()
        # Only one type, why factory?

# Good: Simple function
def fetch_keywords(service, site_url):
    # Direct implementation
```

### ❌ Premature Optimization

```python
# Bad: Optimizing for scale we don't have
async def fetch_keywords_async():  # Async not needed for single user
    # Complex async code

# Good: Simple synchronous code
def fetch_keywords():
    # Simple, readable code
```

### ❌ Missing Error Handling

```python
# Bad: Assumes everything works
data = api_call()
process(data)

# Good: Handles errors gracefully
try:
    data = api_call()
except Exception as e:
    show_error_to_user(e)
    return
process(data)
```

---

## 14. Quick Reference

### Key Files

- `app.py`: Main entry point
- `modules/gsc_client.py`: All GSC API code
- `modules/setup.py`: First-run logic
- `config.json`: App configuration
- `data/keywords.db`: Keywords database

### Key Functions

- `is_first_run()`: Check if setup needed
- `authenticate()`: OAuth flow
- `import_keywords()`: Fetch and store keywords
- `fetch_keyword_page_data()`: Get page-level data
- `aggregate_to_monthly()`: Daily → monthly

### Common Tasks

- **Add new filter**: Update UI in `app.py`, add logic in filter function
- **Change API call**: Modify `modules/gsc_client.py`
- **Add new metric**: Update aggregation logic, add to pivot
- **Fix error handling**: Add try/except, show user-friendly message

---

## 15. Resources

- [Streamlit Docs](https://docs.streamlit.io/)
- [GSC API Docs](https://developers.google.com/webmaster-tools/search-console-api-original)
- [Python Best Practices](https://docs.python-guide.org/writing/style/)
- [PEP 8](https://pep8.org/)

---

**Remember**: Keep it simple. This is a tool for marketers, not a platform for developers. Code clarity > code cleverness.

