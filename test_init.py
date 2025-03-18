from datetime import datetime
import os
import pytest
import configparser
import json
import logging
from utils.data_loader import DataLoader
from actions.base_actions import BaseActions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store test results
test_results = []

def load_config():
    """Load configuration settings from config.ini."""
    config = configparser.ConfigParser()
    try:
        config.read("config/config.ini")
        browser_name = config["playwright"]["browser"].strip()
        headless_mode = config.getboolean("playwright", "headless")
        test_execution_sheet = config["playwright"]["testExecutionSheet"].strip()
        force_new_browser_session = config.getboolean("playwright", "force_new_browser_session")
        return browser_name, headless_mode, test_execution_sheet, force_new_browser_session
    except Exception as e:
        logger.error(f"Error reading config.ini: {str(e)}")
        pytest.fail(f"Configuration error: {str(e)}")

def load_test_data(test_execution_sheet):
    """Load test data from the specified Excel file."""
    try:
        data_loader = DataLoader(test_execution_sheet)
        return data_loader
    except Exception as e:
        logger.error(f"Error loading test data: {str(e)}")
        pytest.fail(f"Test data error: {str(e)}")

# Load configuration and test data
browser_name, headless_mode, test_execution_sheet, force_new_browser_session = load_config()
test_data = load_test_data(test_execution_sheet)

@pytest.mark.parametrize("test_case_id", test_data.get_test_cases())
def test_run_test_cases(test_case_id, record_testsuite_property, page):
    """Execute test cases using the shared browser and page."""
    report_steps = []
    base = BaseActions(page, report_steps)

    # Set timeout for the page
    page.set_default_timeout(60000)  # 60 seconds

    # Load test data
    data_loader = load_test_data(load_config()[2])
    test_steps = data_loader.get_test_steps(test_case_id)

    test_case_result = {
        "test_case_id": test_case_id,
        "status": "Pass",  # Default status
        "steps": [],
        "elapsed_time": None  # Placeholder for elapsed time
    }

    isOK = 0  # 0 = Success, 1 = Failure (for the entire test case)

    # Reset step_no for each test case
    step_no = 0  # Start step_no from 0 for each test case
    start_time = datetime.now()

    for index, step in test_steps.iterrows():
        step_no += 1  # Increment step_no for each step
        step_desc = step["Step_Description"]
        action = step["Action"]
        selector = step["Selector"]
        input_value = step.get("Input", None)

        step_isOK = 0  # Initialize step_isOK

        try:
            if action.lower() == "launchapplication":
                logger.info(f"Navigating to URL: {selector}")
                page.goto(selector)
                actual_result = f"Navigated to '{selector}'"
                expected_result = f"Should navigate to '{selector}'"
            else:
                expected_result = base.get_expected_result(action, selector, input_value)
                step_isOK, actual_result = base.perform_action(step_no, step_desc, expected_result, action, selector, input_value)
                if step_isOK == 1:
                    isOK = 1  # Mark test case as failed if any step fails

            # Ensure the screenshots directory exists
            os.makedirs("reports/screenshots", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"{step_no}_{timestamp}"
            screenshot_path = f"reports/screenshots/{screenshot_name}.png"
            page.screenshot(path=screenshot_path)

            # Log step result
            step_result = {
                "step_no": step_no,
                "step_desc": step_desc,
                "expected_result": expected_result,
                "actual_result": actual_result,
                "status": "Pass" if step_isOK == 0 else "Fail",
                "screenshot_path": f"screenshots/{screenshot_name}.png"
            }
            test_case_result["steps"].append(step_result)

        except Exception as e:
            isOK = 1  # Mark test case as failed
            actual_result = f"Error: {str(e)}"
            expected_result = "Action performed successfully"
            step_result = {
                "step_no": step_no,
                "step_desc": step_desc,
                "expected_result": expected_result,
                "actual_result": actual_result,
                "status": "Fail",
                "screenshot_path": screenshot_path
            }
            test_case_result["steps"].append(step_result)
            logger.error(f"Step {step_no} failed: {actual_result}")

    
    end_time=datetime.now()
    elapsed_time=end_time-start_time
    elapsed_time_seconds = elapsed_time.total_seconds()  # Convert to seconds
    test_case_result["elapsed_time"] = round(elapsed_time_seconds, 2)

    # Update test case status based on isOK
    test_case_result["status"] = "Pass" if isOK == 0 else "Fail"

    # Attach results to the report
    record_testsuite_property(f"TestCase_{test_case_id}", json.dumps(report_steps))
    test_results.append(test_case_result)

    # Fail the test if isOK is 1
    if isOK == 1:
        pytest.fail(f"Test case {test_case_id} failed due to one or more step failures.")

