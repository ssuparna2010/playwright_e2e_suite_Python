import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, file_name):
        self.file_path = os.path.join("Testware", file_name)
        self.sheet_names = pd.ExcelFile(self.file_path).sheet_names  # Get all sheet names

    def load_test_packs(self):
        """Load test packs from the Excel file."""
        if "TestPacks" not in self.sheet_names:
            raise ValueError(f"Sheet 'TestPacks' not found in {self.file_path}. Available sheets: {self.sheet_names}")
        df = pd.read_excel(self.file_path, sheet_name="TestPacks")
        valid_rows = []
        for index, row in df.iterrows():
            if pd.isna(row["TestPackName"]) or row["TestPackName"] == "":
                break
            valid_rows.append(row)
        return pd.DataFrame(valid_rows)

    def load_test_cases(self, test_pack_name):
        """Load test cases from the specified test pack sheet."""
        if test_pack_name not in self.sheet_names:
            raise ValueError(f"Sheet '{test_pack_name}' not found in {self.file_path}. Available sheets: {self.sheet_names}")
        df = pd.read_excel(self.file_path, sheet_name=test_pack_name)
        valid_rows = []
        for index, row in df.iterrows():
            if pd.isna(row["AutomationTestID"]) or row["AutomationTestID"] == "":
                break
            valid_rows.append(row)
        return pd.DataFrame(valid_rows)

    def load_test_steps(self, test_pack_name):
        """Load test steps from the specified test pack scripts sheet, handling merged cells for ScriptId."""
        script_sheet_name = f"{test_pack_name} - Scripts"
        if script_sheet_name not in self.sheet_names:
            raise ValueError(f"Sheet '{script_sheet_name}' not found in {self.file_path}. Available sheets: {self.sheet_names}")

        # Load the test pack scripts sheet into a DataFrame
        df = pd.read_excel(self.file_path, sheet_name=script_sheet_name)

        # Ensure the ScriptId column exists
        if "ScriptId" not in df.columns:
            raise ValueError(f"Column 'ScriptId' not found in sheet '{script_sheet_name}'.")

        # Forward-fill the ScriptId column to handle merged cells
        df["ScriptId"] = df["ScriptId"].ffill()

        # Ensure ScriptId values are stripped of leading/trailing whitespace and lowercase
        df["ScriptId"] = df["ScriptId"].astype(str).str.strip().str.lower()

        return df
    def load_object_map(self):
        """Load the object map from the Excel file."""
        if "ObjectMap" not in self.sheet_names:
            raise ValueError(f"Sheet 'ObjectMap' not found in {self.file_path}. Available sheets: {self.sheet_names}")
        df = pd.read_excel(self.file_path, sheet_name="ObjectMap")
        return df

    def get_test_packs(self):
        """Retrieve test packs with RunMode set to 'Yes'."""
        test_packs = self.load_test_packs()
        return test_packs[test_packs["RunMode"].str.lower() == "yes"]

    def get_test_cases(self, test_pack_name):
        """Retrieve test cases with RunMode set to 'Yes' for a specific test pack."""
        test_cases = self.load_test_cases(test_pack_name)
        logger.info(f"Test cases for {test_pack_name}: {test_cases}")
        return test_cases[test_cases["RunMode"].str.lower() == "yes"]

    def get_test_steps(self, test_pack_name, automation_test_id):
        """Retrieve test steps for a specific AutomationTestID in a specific test pack."""
        test_steps = self.load_test_steps(test_pack_name)
        
        # Normalize automation_test_id
        automation_test_id = str(automation_test_id).strip().lower()
        
        # Debug: Print the automation_test_id being searched for
        print(f"Searching for AutomationTestID: '{automation_test_id}'")
        
        # Debug: Print unique ScriptId values in the test_steps DataFrame
        print("Unique ScriptId values in test_steps:")
        print(test_steps["ScriptId"].unique())
        
        # Filter test steps based on ScriptId
        filtered_steps = test_steps[test_steps["ScriptId"] == automation_test_id]
        
        # Debug: Print the number of rows found
        print(f"Number of rows found for '{automation_test_id}': {len(filtered_steps)}")
        
        return filtered_steps

    def get_object_details(self, object_name):
        """Retrieve object details from the object map."""
        object_map = self.load_object_map()
        return object_map[object_map["ObjectName"] == object_name]
