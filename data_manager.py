import pandas as pd
import os

class DataManager:
    def __init__(self, user_email=None):
        self.user_email = user_email
        self.data_dir = "data"
        self.worksheet_names = ["Squad", "Transfers", "MatchStats"]
        
        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Headers Definition
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

    def set_user(self, email):
        """Set the current user email."""
        self.user_email = email

    def get_excel_path(self, email=None):
        """Public method to get Excel path."""
        target_email = email if email else self.user_email
        if not target_email:
             raise Exception("User not authenticated.")
        safe_email = target_email.replace("@", "_at_").replace(".", "_dot_")
        return os.path.join(self.data_dir, f"{safe_email}_Stats.xlsx")

    def _get_excel_path(self):
        return self.get_excel_path()



    def load_or_create_spreadsheet(self, sheet_name=None):
        """Ensures Excel file exists for the user."""
        if not self.user_email:
            return 
            
        path = self._get_excel_path()
        if not os.path.exists(path):
            # Create a new Excel file with empty sheets
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                for name in self.worksheet_names:
                    df = pd.DataFrame(columns=self.headers[name])
                    df.to_excel(writer, sheet_name=name, index=False)
        else:
            # Check if all sheets exist, if not create them (rare case but good safety)
            # This is hard with ExcelWriter in append mode without overwriting.
            # Assuming file integrity for now or just reading.
            pass

    def get_data(self, worksheet_name) -> pd.DataFrame:
        """Fetch all records from a worksheet in the Excel file."""
        path = self._get_excel_path()
        if not os.path.exists(path):
             return pd.DataFrame(columns=self.headers.get(worksheet_name, []))
        
        try:
            return pd.read_excel(path, sheet_name=worksheet_name)
        except ValueError:
            # Sheet might not exist
            return pd.DataFrame(columns=self.headers.get(worksheet_name, []))
        except Exception:
            return pd.DataFrame(columns=self.headers.get(worksheet_name, []))

    def write_data(self, worksheet_name, df: pd.DataFrame):
        """Overwrite a specific worksheet in the Excel file."""
        path = self._get_excel_path()
        
        # We need to preserve other sheets. The best way is to load all, update one, save all.
        # Or use openpyxl to replace a sheet.
        # Efficient approach: load all sheets into a dict of DFs, update the one, write back.
        
        if os.path.exists(path):
            all_sheets = pd.read_excel(path, sheet_name=None)
        else:
            all_sheets = {}
            for name in self.worksheet_names:
                all_sheets[name] = pd.DataFrame(columns=self.headers[name])
        
        all_sheets[worksheet_name] = df
        
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            for name, sheet_df in all_sheets.items():
                sheet_df.to_excel(writer, sheet_name=name, index=False)

    def append_data(self, worksheet_name, df: pd.DataFrame):
        """Append rows to a specific worksheet."""
        path = self._get_excel_path()
        
        if os.path.exists(path):
            try:
                # Read specific sheet
                existing_df = pd.read_excel(path, sheet_name=worksheet_name)
            except ValueError:
                 existing_df = pd.DataFrame(columns=self.headers.get(worksheet_name, []))
            
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            self.write_data(worksheet_name, updated_df)
        else:
            self.write_data(worksheet_name, df)

    def list_spreadsheets(self):
        return []
