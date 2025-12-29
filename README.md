# Retro FIFA Stats ⚽

A personal Streamlit application for tracking squad details, transfers, and match statistics for your Retro FIFA Career Mode saves.

## Features
- **Squad Management**: Track player attributes, contracts, and growth.
- **Transfer History**: Record all your career transfers.
- **Match Stats**: Log detailed stats for every match.
- **Dashboard**: Visualize player performance with Pizza Charts, Radar Comparisons, and detailed Trend Analysis.
- **Excel Backend**: All data is stored in a simple Excel file that you can download and keep.

## How to Run Locally

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/retro-fifa-stats.git
    cd retro-fifa-stats
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the app**:
    ```bash
    streamlit run app.py
    ```

## Cloud Deployment (Streamlit Cloud)

This app is designed to be stateless for cloud environments.

1.  **Push to GitHub**: Upload your code to a GitHub repository.
2.  **Deploy on Streamlit Cloud**:
    - Connect your GitHub account.
    - Select your repository and `app.py`.
    - Click **Deploy**.

**Important for Cloud Usage**:
- The app stores data in a **temporary** session file. 
- **Start of Session**: Enter your Team Name. You can either start fresh or upload your previous `.xlsx` backup.
- **End of Session**: **Back up your data** by clicking the "Download Excel Backup" button on the Home page before closing the tab. Data is **deleted** when the app restarts or sleeps.

## Tech Stack
-   **Frontend**: Streamlit
-   **Data Processing**: Pandas, OpenPyXL
-   **Visualization**: Plotly Graph Objects, Plotly Express
-   **Analysis**: Statsmodels (OLS Trendlines)
