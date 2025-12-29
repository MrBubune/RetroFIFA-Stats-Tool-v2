# Retro FIFA Stats App Walkthrough

## Prerequisites
1.  **Python**: Ensure Python is installed.
2.  **Google Cloud Setup**:
    - **Enable APIs**: Google Sheets API & Google Drive API.
    - **OAuth Consent**: Set to "External" (or Internal if you have a mocked org), add your email as a test user.
    - **Credentials**: Create OAuth Client ID (Desktop), download as `client_secrets.json`.

## Installation
1.  **Install Requirements**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Setup Credentials**:
    - Place `client_secrets.json` in this folder.
    - OR Add contents to `.streamlit/secrets.toml`:
      ```toml
      [google_oauth]
      client_id = "..."
      client_secret = "..."
      ...
      ```

## Running the App
```bash
streamlit run app.py
```

## First Time Login
1.  The app will ask you to "Sign in with Google".
2.  A browser window will open. Grant access to your Drive/Sheets.
3.  **Success**: The app will save a `token.json` file locally. You won't need to log in again until this token expires.
4.  The app will automatically connect to (or create) a spreadsheet named "RetroFIFAStats" in your Google Drive.

## Pages Guide
- **Squad Information**: Add players here first. The database needs players to record stats.
- **Transfer Information**: Manage your transfer history.
- **Player Stats**:
    - **Tab 1**: Input match data. Select players from your squad. A grid will appear to enter stats for each player.
    - **Tab 2**: View aggregated stats (Per 90, Accuracy %).
- **Team Stats**: View overall wins/losses and team totals.
