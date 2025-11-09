# GSC Explorer

<div align="center">

**A simple, localhost-only tool for exploring Google Search Console keyword-page performance data**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)

</div>

---

## 🎯 Overview

GSC Explorer is a lightweight, open-source Streamlit application that makes it easy to explore Google Search Console data. Instead of wrestling with complex notebooks or dealing with the limitations of the native GSC UI, you can quickly query, filter, and view keyword-page performance metrics over time.

**Built for marketers and SEO analysts who need quick insights, not complex analytics.**

### 📹 Demo Video

**Quick walkthrough of the setup and usage:**

<video width="800" controls>
  <source src="https://raw.githubusercontent.com/surendranb/gsc-explorer/main/assets/demo.mp4" type="video/mp4">
  Your browser does not support the video tag. 
  <a href="https://www.youtube.com/watch?v=nCCzrRRMKso">Watch on YouTube instead</a>
</video>

> 💡 **Note**: If the video doesn't load, [watch it on YouTube](https://www.youtube.com/watch?v=nCCzrRRMKso)

### Key Features

- 🔍 **Simple Keyword Exploration** - Select keywords and instantly see page-level performance
- 📊 **Monthly Trend Analysis** - View metrics aggregated by month for easy trend spotting
- 🎯 **Flexible Filtering** - Filter by keyword, page, and metric (clicks, impressions, position, CTR)
- 📥 **Export Ready** - Built-in data export for further analysis
- 🚀 **Quick Setup** - Get started in minutes with guided setup flow
- 💾 **Local-First** - Everything runs locally, your data stays private

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Search Console account with API access
- Google Cloud Project with Search Console API enabled

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/gsc-explorer.git
   cd gsc-explorer
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Google OAuth credentials:**
   
   **Step-by-step:**
   
   a. **Go to Google Cloud Console**
      - Visit: https://console.cloud.google.com/
      - Sign in with your Google account
   
   b. **Create or Select a Project**
      - Click the project dropdown at the top
      - Click "New Project" or select an existing one
   
   c. **Enable Search Console API**
      - Go to: https://console.cloud.google.com/apis/library
      - Search for "Google Search Console API"
      - Click on it and press "Enable"
   
   d. **Configure OAuth Consent Screen**
      - Go to: https://console.cloud.google.com/apis/credentials/consent
      - Click "Create" or "Edit App"
      - Choose "External" user type
      - Fill in required fields (App name, email, etc.)
      - Add your email as a test user
      - Save and continue through all steps
   
   e. **Create OAuth Credentials**
      - Go to: https://console.cloud.google.com/apis/credentials
      - Click "Create Credentials" → "OAuth client ID"
      - Application type: **Web application**
      - Name: `GSC Explorer`
      - Click "Create"
      - **After creating**, click on the OAuth client to edit it
      - Scroll to "Authorized redirect URIs"
      - Click "+ ADD URI" and add exactly: `http://localhost:8080/` (with trailing slash)
      - Click "SAVE"
      - Wait 1-2 minutes for changes to propagate
   
   f. **Download Credentials**
      - Click the download icon (⬇️) next to your OAuth client
      - Save the file as `gsc_credentials.json`
      - Place it in the project root directory

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

6. **Follow the setup wizard:**
   
   The app will guide you through 4 simple steps:
   
   - **Step 1: Setup Credentials** - Verify your `gsc_credentials.json` file is detected
   - **Step 2: Authenticate** - Click "Authenticate with Google" (browser will open automatically)
   - **Step 3: Select Property** - Choose which GSC property to analyze
   - **Step 4: Import Keywords** - Configure filters and import keywords from GSC
   
   After completing setup, you'll be taken to the main app to start exploring!

---

## 📖 Usage Guide

### First-Time Setup

When you first run the app, you'll go through a simple 4-step setup:

1. **Step 1: Setup Credentials** - Verify your `gsc_credentials.json` file is in place
2. **Step 2: Authenticate** - Connect your Google account (browser will open automatically)
3. **Step 3: Select Property** - Choose which GSC property to analyze
4. **Step 4: Import Keywords** - Configure filters and import keywords from GSC

### Using the Main App

Once setup is complete:

1. **Select Keywords** - Use the sidebar to search and select keywords
2. **Configure Site URL** - Verify or update your GSC property URL
3. **Fetch Data** - Click "🚀 Fetch Data" to retrieve performance metrics
4. **Explore Results** - Filter by keyword, page, or metric to analyze trends
5. **Export** - Use the built-in export functionality to download your data

### Importing More Keywords

Need to add more keywords or update your keyword list?

1. Click the **"ℹ️ Database Info & Settings"** expander at the top
2. Click **"📥 Import Keywords"**
3. Configure your import settings and import new keywords

### Troubleshooting

**"Redirect URI mismatch" error:**
- Make sure `http://localhost:8080/` is added to your OAuth client's authorized redirect URIs
- Wait 1-2 minutes after saving changes in Google Cloud Console

**"User does not have sufficient permission" error:**
- Verify you selected the correct GSC property in Step 3
- Make sure you have access to that property in Google Search Console

**No keywords found after import:**
- Check your date range - make sure it's not too narrow
- Lower your minimum impressions threshold
- Verify the property has search data in that date range

---

## 📁 Project Structure

```
gsc-explorer/
├── app.py                 # Main Streamlit application
├── modules/
│   ├── __init__.py
│   ├── setup.py          # First-run setup flow
│   ├── gsc_client.py     # GSC API client (auth + data fetching)
│   └── utils.py          # Helper functions
├── config/
│   └── config.example.json
├── docs/
│   ├── PRD.md            # Product requirements document
│   └── DEVELOPER_GUIDE.md # Development guide
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 🔧 Configuration

### Environment Setup

The app uses local files for configuration (all auto-generated except credentials):

- **`gsc_credentials.json`** - Google OAuth credentials (you provide this)
- **`config/config.json`** - App configuration (auto-generated)
- **`token.json`** - OAuth token (auto-generated)
- **`data/keywords.db`** - SQLite database with imported keywords (auto-generated)

All sensitive files are excluded from git via `.gitignore`.

### Supported GSC Property Types

- Domain properties: `sc-domain:example.com`
- URL prefix properties: `https://example.com/`

### Multi-Domain Support

You can import keywords for multiple domains. Each import is tagged with its domain, allowing you to:
- Import keywords for different GSC properties
- Filter keywords by domain in the main app
- Keep data organized by property

---

## 🎨 Features in Detail

### Monthly Trend Analysis

All data is aggregated at the monthly level, making it easy to spot trends over time. The app automatically:
- Fetches daily data from the GSC API
- Aggregates to monthly totals (sum for clicks/impressions, average for position/CTR)
- Displays results in a pivot table format with months as columns

### Flexible Filtering

- **By Keyword** - Filter results to specific keywords
- **By Page** - See which pages perform best for selected keywords
- **By Metric** - Focus on clicks, impressions, position, or CTR

### Multi-Domain Support

The app supports multiple domains. Each keyword import is tagged with its domain, allowing you to:
- Import keywords for different properties
- Filter keywords by domain in the main app
- Keep data organized by property

---

## 🛠️ Development

### Running in Development Mode

```bash
streamlit run app.py --logger.level=debug
```

### Project Philosophy

This project follows a **simplicity-first** approach:

- ✅ Keep code simple and readable
- ✅ Prioritize user experience over code elegance
- ✅ Use straightforward patterns (no over-engineering)
- ✅ Focus on one thing well: monthly trend exploration

See [DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md) for more details.

---

## 📚 Documentation

- **[Developer Guide](./docs/DEVELOPER_GUIDE.md)** - Development best practices (for those who want to modify)
- **[Product Requirements](./docs/PRD.md)** - Product requirements document

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## ⚠️ Important Notes

- **Localhost Only**: This app is designed for local use only. Do not deploy to production without proper security measures.
- **API Limits**: The GSC API has rate limits. The app handles this automatically, but large imports may take time.
- **Data Privacy**: All data is stored locally. Your credentials and tokens never leave your machine.

---

<div align="center">

**Made with ❤️ for the SEO community**

⭐ Star this repo if you find it useful!

</div>
