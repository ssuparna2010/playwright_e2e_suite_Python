from datetime import datetime
import os
import pandas as pd
import pytest
import configparser
import json
import logging
from utils.data_loader import DataLoader
from actions.base_actions import BaseActions
from utils.ai_evaluator import perform_evaluation

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
        base_url = config["playwright"]["base_URL"].strip()
        return browser_name, headless_mode, test_execution_sheet, force_new_browser_session, base_url
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
browser_name, headless_mode, test_execution_sheet, force_new_browser_session, base_url = load_config()
test_data = load_test_data(test_execution_sheet)

# Add logging to verify test packs
test_packs = test_data.get_test_packs()["TestPackName"]
logger.info(f"Loaded test packs: {test_packs}")

@pytest.mark.parametrize("test_pack_name", test_packs)
def test_run_test_cases(test_pack_name, record_testsuite_property, page):
    """Execute test cases using the shared browser and page."""
    logger.info(f"Running test pack: {test_pack_name}")
    report_steps = []
    base = BaseActions(page, report_steps)

    # Set timeout for the page
    page.set_default_timeout(60000)  # 60 seconds

    # Load test cases for the current test pack
    test_cases = test_data.get_test_cases(test_pack_name)
    logger.info(f"Loaded test cases: {test_cases}")
    
    for index, test_case in test_cases.iterrows():
        automation_test_id = test_case["AutomationTestID"]
        logger.info(f"Running test case: {automation_test_id}")
        
        # Load test steps for the current test case
        test_steps = test_data.get_test_steps(test_pack_name, automation_test_id)
        
        # Forward-fill the ScriptId column to handle merged cells
        test_steps["ScriptId"] = test_steps["ScriptId"].ffill()
        logger.info(f"Loaded test steps for {automation_test_id}: {test_steps}")
     
        test_case_result = {
            "test_case_id": automation_test_id,
            "status": "Pass",  # Default status
            "steps": [],
            "elapsed_time": None  # Placeholder for elapsed time
        }

        isOK = 0  # 0 = Success, 1 = Failure (for the entire test case)

        # Reset step_no for each test case
        step_no = 0  # Start step_no from 0 for each test case
        start_time = datetime.now()

        for step_index, step in test_steps.iterrows():
            step_no += 1  # Increment step_no for each step
            
            input_value = step.get("TestData", None)

            if test_pack_name == "GenAIEvaluation":
                # Handle GenAIEvaluation specific columns
                script_id = step["ScriptId"]
                step_desc = step["StepDescription"]
                evaluators = step["Evaluators"]
                query = step["Query"]
                context = step["Context"]
                ground_truth = step["Ground_Truth"]
                # Handle NaN values
                query = query if pd.notna(query) else ""
                context = context if pd.notna(context) else ""
                ground_truth = ground_truth if pd.notna(ground_truth) else ""

                logger.info(f"Evaluating response with query: {query}, context: {context}, ground_truth: {ground_truth}")

                step_isOK, actual_result, expected_result,output_path = perform_evaluation(script_id,step_no, step_desc, evaluators, query, context, ground_truth, input_value)
                    
            

                # Log step result
                step_result = {
                    "step_no": step_no,
                    "step_desc": step_desc,
                    "expected_result": expected_result,
                    "actual_result": actual_result,
                    "status": "Pass" if step_isOK == 0 else "Fail",
                    "evaluator_path": output_path  # No screenshot for GenAIEvaluation steps
                }
                test_case_result["steps"].append(step_result)

            else:
                # Handle regular test steps
                action = step["StepName"]
                step_desc = step["StepDescription"]
                object_name = step["ObjectName"]
                optionaldata = step.get("OptionalData", None)
                propertyname = step.get("PropertyName", None)

                # Handle NaN values in object_name
                if pd.isna(object_name):
                    object_name = "NA"

                # Get object details from the object map
                object_details = test_data.get_object_details(object_name)

                if not object_details.empty:
                    # Extract all relevant details from the object map
                    selector = {
                        "application": object_details.iloc[0]["Application"],
                        "object_type": object_details.iloc[0]["ObjectType"],
                        "parent_locator": object_details.iloc[0]["ParentObjectLocator"],
                        "child_locator1": object_details.iloc[0]["ChildObjectLocator1"] or None,
                        "child_locator2": object_details.iloc[0]["ChildObjectLocator2"] or None,
                        "child_locator3": object_details.iloc[0]["ChildObjectLocator3"] or None,
                        "locator": object_details.iloc[0]["ParentObjectLocator"]
                    }
                else:
                    selector = {
                        "locator": object_name
                    }

                step_isOK = 0  # Initialize step_isOK
                screenshot_path = None  # Initialize screenshot_path

                try:
                    if action.lower() == "launchapplication":
                        if object_name == "NA":
                            selector = base_url
                            logger.info(f"Navigating to URL: {selector}")
                        else:
                            selector = selector["locator"]
                            logger.info(f"Navigating to URL: {selector}")  
                        page.goto(selector)
                        actual_result = f"Navigated to '{selector}'"
                        expected_result = f"Should navigate to '{selector}'"
                    else:
                        expected_result = base.get_expected_result(action, selector, input_value)
                        step_isOK, actual_result = base.perform_action(step_no, step_desc, expected_result, action, selector, input_value, optionaldata, propertyname)
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
                        "screenshot_path": screenshot_path if screenshot_path else "N/A"
                    }
                    test_case_result["steps"].append(step_result)
                    logger.error(f"Step {step_no} failed: {actual_result}")

        end_time = datetime.now()
        elapsed_time = end_time - start_time
        elapsed_time_seconds = elapsed_time.total_seconds()  # Convert to seconds
        test_case_result["elapsed_time"] = round(elapsed_time_seconds, 2)

        # Update test case status based on isOK
        test_case_result["status"] = "Pass" if isOK or step_isOK == 0 else "Fail"

        # Attach results to the report
        record_testsuite_property(f"TestCase_{automation_test_id}", json.dumps(report_steps))
        test_results.append(test_case_result)
        logger.info(f"Test case {automation_test_id} completed with status: {test_case_result['status']}")

        # Fail the test if isOK is 1
        if isOK == 1:
            pytest.fail(f"Test case {automation_test_id} failed due to one or more step failures.")

# Generate the HTML report after all tests are executed
@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    from report_generator import generate_html_report
    print("test_results",test_results)
    generate_html_report(test_results)
    logger.info("HTML report generated.")
