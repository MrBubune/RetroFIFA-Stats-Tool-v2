import pandas as pd
import io

class DataManager:
    def __init__(self):
        # In-memory store: {sheet_name: df}
        self.worksheet_names = ["Squad", "Transfers", "MatchStats"]
        self.headers = {
            "Squad": [
                "Season", "Name", "Age", "Kit Number", "Position 1", "Position 2", "Position 3", "Position 4",
                "Nationality", "Height", "Weight", "Transfer Value", "Wage", "Contract Length",
                "Role", "Strong Foot", "Overall Start", "Overall End"
            ],
            "Transfers": [
                "Season", "Player Name", "Transfer Date", "Transfer Type", "Transfer Value"
            ],
            "MatchStats": [
                "Player Name", "Season", "Competition", "Opponent", "Scores", "Date",
                "Minutes Played", "Match Rating", "Goals", "Own Goals", "Assists",
                "Shots", "Shots on Target", 
                "Passes Attempted", "Passes Completed",
                "Short Passes Attempted", "Short Passes Completed",
                "Medium Passes Attempted", "Medium Passes Completed",
                "Long Passes Attempted", "Long Passes Completed",
                "Dribbles Attempted", "Dribbles Completed",
                "Crosses Attempted", "Crosses Completed",
                "Tackles Attempted", "Tackles Completed",
                "Interceptions", "Key Passes", "Key Dribbles", "Fouled",
                "Successful 1 on 1 Dribbles", "Fouls", "Penalties Conceded",
                "Blocks", "Out of Position", "Posession Won", "Posession Lost",
                "Clearances", "Headers Won", "Headers Lost",
                "Saves", "Shots Caught", "Shots Parried", "Crosses Caught", "Balls Stripped",
                "Man of the Match", "Started"
            ]
        }
        self.data = {name: pd.DataFrame(columns=self.headers[name]) for name in self.worksheet_names}
        self.current_save_name = "MySave"

    def load_from_bytes(self, file_bytes):
        """Load data from an Excel byte stream (uploaded file)."""
        try:
            # Load all sheets
            xls = pd.read_excel(file_bytes, sheet_name=None)
            for sheet in self.worksheet_names:
                if sheet in xls:
                    self.data[sheet] = xls[sheet]
                else:
                    self.data[sheet] = pd.DataFrame(columns=self.headers[sheet])
            return True, "Data loaded successfully."
        except Exception as e:
            return False, f"Error loading data: {e}"

    def save_to_bytes(self):
        """Save current data to an Excel byte stream for download."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for name, df in self.data.items():
                df.to_excel(writer, sheet_name=name, index=False)
        output.seek(0)
        return output

    def get_data(self, worksheet_name) -> pd.DataFrame:
        """Fetch all records from a worksheet in memory."""
        return self.data.get(worksheet_name, pd.DataFrame(columns=self.headers.get(worksheet_name, [])))

    def write_data(self, worksheet_name, df: pd.DataFrame):
        """Overwrite a specific worksheet in memory."""
        self.data[worksheet_name] = df

    def append_data(self, worksheet_name, df: pd.DataFrame):
        """Append rows to a specific worksheet in memory."""
        current = self.data.get(worksheet_name, pd.DataFrame(columns=self.headers.get(worksheet_name, [])))
        updated = pd.concat([current, df], ignore_index=True)
        self.data[worksheet_name] = updated
