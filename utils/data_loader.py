import pandas as pd
import os

class DataLoader:
    def __init__(self, file_name):
        self.file_path = os.path.join("Testware", file_name)
        self.sheet_names = pd.ExcelFile(self.file_path).sheet_names  # Get all sheet names

    def load_test_cases(self):
        """Load test cases from the Excel file."""
        if "TestPlan" not in self.sheet_names:
            raise ValueError(f"Sheet 'TestPlan' not found in {self.file_path}. Available sheets: {self.sheet_names}")
        return pd.read_excel(self.file_path, sheet_name="TestPlan")

    def load_test_steps(self):
        """Load test steps from the Excel file."""
        if "TestScript" not in self.sheet_names:
            raise ValueError(f"Sheet 'TestScript' not found in {self.file_path}. Available sheets: {self.sheet_names}")
        return pd.read_excel(self.file_path, sheet_name="TestScript")

    def get_test_cases(self):
        """Retrieve unique test case IDs."""
        test_cases = self.load_test_cases()
        return test_cases["TestCase_ID"].unique()

    def get_test_steps(self, test_case_id):
        """Retrieve test steps for a specific test case."""
        test_steps = self.load_test_steps()
        return test_steps[test_steps["TestCase_ID"] == test_case_id]
