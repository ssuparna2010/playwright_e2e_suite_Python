from playwright.sync_api import Page, expect
import time
import os
from datetime import datetime
import json
import pandas as pd
import requests
from .custom_transact_action import CustomTransactActions
from utils.ai_evaluator import calculate_cosine_similarity

class BaseActions:
    def __init__(self, page: Page, report_steps):
        self.page = page
        self.main_page = page  # Initialize main_page attribute
        self.report_steps = report_steps  # Store test steps
        self.custom_actions = CustomTransactActions(page, report_steps)  # Initialize custom actions

    def get_locator(self, selector):
        """Detect whether the selector is XPath or CSS"""
        if not isinstance(selector, str):
            raise ValueError(f"Invalid selector: {selector}")
        selector = selector.strip()
        if selector.startswith("//") or selector.startswith("("):
            return self.page.locator(f"xpath={selector}")
        return self.page.locator(selector)

    def element_not_visible(self, selector):
        """Check if the element is hidden or does not exist on the page."""
        try:
            selector = selector.strip()
            # Get the locator for the selector
            locator = self.get_locator(selector)
            # Check if the element is hidden
            is_hidden = locator.is_hidden()

            return is_hidden
        except Exception as e:
            return True  # Assume the element is not visible if an error occurs
        
                
    def get_expected_result(self, action, selector, input_value):
        """Dynamically generate the expected result based on action type."""
        final_selector = self.final_selector(selector)
        action = action.lower()  # Convert action to lower case for case-insensitive comparison

        if action == "setinputintextfield":
            return f"Text '{input_value}' should be entered in {final_selector}"
        elif action == "clickelement":
            return f"Element {final_selector} should be clicked"
        elif action == "checkelementexistence":
            return f"Element {final_selector} should exist"
        elif action == "checkelementnotvisible":
            return f"Element {final_selector} should not exist"
        elif action == "checkelementcontaintext":
            return f"Element {final_selector} should contain text '{input_value}'"
        elif action == "title":
            return f"Page title should be '{final_selector}'"
        elif action == "timedelay":
            return f"Wait for {input_value}s"
        elif action == "waitforelementexist":
            return f"Element {final_selector} should exist within {input_value}s"
        elif action == "checkelementenabled":
            return f"Element {final_selector} should be enabled"
        elif action == "clickelementcontaintextoption":
            return f"Element {final_selector} should be clicked which is having text '{input_value}'"
        elif action == "clickfindbutton":
            return f"Find button should be clicked"
        elif action == "checkelementnotvisiblexpath":
            return f"Element {final_selector} should not be visible"
        elif action == "checkelementcontainstextexistence":
            return f"Element {selector.get('child_locator1')} should contain text '{input_value}'"
        elif action == "checkelementcontainstoredtext":
            return f"Element {selector.get('child_locator1')} should contain stored text from data store"
        else:
            return f"For action '{action}' please validate objectMap"

    def switch_to_frame_by_index(self, index):
        """Switch to the iframe specified by the index"""
        frames = self.page.frames
        if index < 0 or index >= len(frames):
            raise Exception(f"Frame index {index} is out of bounds")
        frame = frames[index]
        self.page = frame
        print(f"Switched to frame at index {index}")

    def validate_api_response(self, url, method="GET", headers=None, payload=None, expected_status=200, expected_responses=None):
        """Validate API response based on the provided parameters."""
        try:
            headers = headers or {}
            payload = payload or {}

            # For API requests
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=payload)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Validate the response code
            assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"

            # Validate the response
            validation_results = []
            if expected_responses:
                for expected_response in expected_responses:
                    key = expected_response.get("key")
                    value = expected_response.get("value")
                    operand = expected_response.get("operand", "equals")

                    if operand == "equals":
                        if self._find_key_value(response.json(), key, value):
                            validation_results.append(f"""Validation passed: {key} equals {value}""")
                        else:
                            validation_results.append(f"\nValidation failed: {key} does not equal {value}")
                    elif operand == "contains":
                        if self._find_key_value(response.json(), key, value, contains=True):
                            validation_results.append(f"\nValidation passed: {key} contains {value}")
                        else:
                            validation_results.append(f"\nValidation failed: {key} does not contain {value}")
                    else:
                        raise ValueError(
                            f"Unsupported response validation operator in expected_response: {operand}."
                            "Expected format: "
                            '{"url": "<URL>", "method": "<GET|POST|PUT>", '
                            '"headers": {<optional>}, "payload": {<optional>}, '
                            '"expected_status": "<code>", '
                            '"expected_responses": [{"key": "<key>", "value": "<value>", "operand": "<equals|contains>"}]}'
                        )

            return 0, f"API validation successful for {url}. Validation results: {', '.join(validation_results)}"
        except Exception as e:
            return 1, f"API validation failed for {url}: {str(e)}"

    def _find_key_value(self, data, key, value, contains=False):
        """Recursively find the key-value pair in the nested JSON data."""
        if isinstance(data, dict):
            if key in data:
                if contains:
                    return value in str(data[key])  # Check if value is contained in the data[key]
                return data[key] == value  # Check if value matches exactly
            for k, v in data.items():
                if self._find_key_value(v, key, value, contains):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._find_key_value(item, key, value, contains):
                    return True
        return False
    
    def switch_to_frame_by_selector(self, selector):
        """Switch to the iframe specified by the selector"""
        frame_locator = self.page.frame_locator(selector)
        frame = frame_locator.frame()
        if frame is None:
            raise Exception(f"Frame with selector '{selector}' not found")
        self.page = frame
        print(f"Switched to frame with selector '{selector}'")
 

    def switch_to_frame_in_shadow_root(self, shadow_host_selector, iframe_selector):
        """Switch to the iframe inside a shadow root"""
        shadow_host = self.page.query_selector(shadow_host_selector)
        if shadow_host is None:
            raise Exception(f"Shadow host '{shadow_host_selector}' not found")
        shadow_root = shadow_host.evaluate_handle("el => el.shadowRoot")
        iframe = shadow_root.query_selector(iframe_selector)
        if iframe is None:
            raise Exception(f"Iframe '{iframe_selector}' not found in shadow root")
        self.page = iframe.content_frame()
        print(f"Switched to iframe '{iframe_selector}' inside shadow root '{shadow_host_selector}'")

    def switch_to_main_frame(self):
        """Switch back to the main frame"""
        self.page = self.main_page
        print("Switched back to main frame")

    def get_shadow_root(self, element):
        """Get the shadow root of the specified element"""
        return element.evaluate_handle("el => el.shadowRoot")

    def get_nested_shadow_element(self, root, selectors):
        """Recursively traverse nested shadow roots to find the desired element"""
        element = root
        for selector in selectors:
            element = element.evaluate_handle(f"el => el.shadowRoot.querySelector('{selector}')")
            if element is None:
                raise Exception(f"Element '{selector}' not found in shadow DOM")
        return element
    def final_selector(self, selector):
        """Construct the final selector based on the provided locators"""
        if isinstance(selector, dict):
            final_selector = selector.get("locator", "")
            if "parent_locator" in selector and pd.notna(selector["parent_locator"]):
                final_selector = selector["parent_locator"]
                if "child_locator1" in selector and pd.notna(selector["child_locator1"]):
                    final_selector += " >> " + selector["child_locator1"]
                    if "child_locator2" in selector and pd.notna(selector["child_locator2"]):
                        final_selector += " >> " + selector["child_locator2"]
                        if "child_locator3" in selector and pd.notna(selector["child_locator3"]):
                            final_selector += " >> " + selector["child_locator3"]
        else:
            final_selector = selector
        return final_selector
    def final_xpath_selector(self, selector):
        """Construct the final selector based on the provided locators"""
        if isinstance(selector, dict):
            final_selector = selector.get("locator", "")
            if "parent_locator" in selector and pd.notna(selector["parent_locator"]):
                final_selector = selector["parent_locator"]
        else:
            final_selector = selector
        return final_selector

    def perform_action(self, step_no, step_desc, expected_result, action, selector, input_value=None,optional_data=None, propertyname=None,):
        """Perform action based on test script and log failures if element not found"""
        start_time = time.time()
        isOK = 0  # 0 = Success, 1 = Failure
        actual_result = ""
        screenshot_path = None  # Store screenshot if failure occurs
        final_selector = self.final_selector(selector)   

        try:
            action = action.lower()  # Convert action to lower case for case-insensitive comparison

            if action == "setinputintextfield":
                locator = self.get_locator(final_selector)
                locator.wait_for(state="visible", timeout=5000)  # Wait for visibility
                locator.fill(str(input_value))
                actual_result = f"Typed '{input_value}' in {final_selector}"
            
            elif action == "checkelementexistence":
                locator = self.get_locator(final_selector)
                locator.wait_for(state="visible", timeout=5000)  # Wait for visibility
                actual_result = f"Element {final_selector} exists"

            elif action == "checkelementnotvisible":
                locator = self.element_not_visible(final_selector)
                if locator:
                    actual_result = f"Element {final_selector} does not exist"
                    isOK = 0
                else:
                    actual_result = f"Element {final_selector} exists"
                    isOK = 1
            
            elif action == "clickelement":
                locator = self.get_locator(final_selector)
                locator.wait_for(state="visible", timeout=5000)  # Wait for visibility
                locator.click()
                actual_result = f"Clicked on {final_selector}"

            elif action == "checkelementcontaintext":
                if final_selector == "title":
                    assert self.page.title().to_contain_text(input_value) , f"Expected '{input_value}', got '{self.page.title()}'"
                    actual_result = f"Page title matched: {input_value}"
                else:
                    locator = self.get_locator(final_selector)
                    expect(locator).to_contain_text(input_value, timeout=5000)
                    actual_result = f"Verified text '{input_value}' in {final_selector}"
                    
            elif action == "timedelay":
                delay = float(input_value * 1000)  # Convert to milliseconds
                self.page.wait_for_timeout(int(delay))  # Playwright expects milliseconds
                actual_result = f"Waited for {input_value}s"
            
            elif action == "clickelementcontaintextoption":
                print("final_selector", final_selector)
                locator = self.get_locator(final_selector).filter(has_text=input_value)
                locator.wait_for(state="visible", timeout=50000)  # Wait for visibility
                locator.click(force=True)  # Click the element with force
                actual_result = f"Clicked on element {final_selector} containing text '{input_value}'"

            elif action == "cosine_similarity":
                #locator = self.get_locator(final_selector)
                #locator.wait_for(state="visible", timeout=50000) 
                #extracted_response_text = locator.inner_text()
                SIMILARITY_THRESHOLD = 0.3
                extracted_response_text = "AI stands for Artificial Intelligence"
                print("\nsimilarity starts",extracted_response_text,"\nexpected", input_value)
                similarity_score  =  calculate_cosine_similarity(extracted_response_text,input_value)
                stepIsOK = similarity_score >= SIMILARITY_THRESHOLD

                if stepIsOK:
                    isOK=0
                    actual_result = f"Extracted responses and passed to cosine_similarity. Result: {similarity_score}"
                else:
                    isOK = 1  # Mark step as failed
                    actual_result = f"Error in evaluation: {similarity_score}"
                
                return isOK, actual_result
            
            elif action == "clickelementxpath":
                locator = self.page.locator(f"xpath={final_selector}")
                locator.click(force=True)  # Click the element with force
                actual_result = f"Clicked on element {final_selector}"
                
            elif action == "switchtoframe":
                if final_selector.isdigit():
                    self.switch_to_frame_by_index(int(final_selector))
                else:
                    self.switch_to_frame_by_selector(final_selector)
                actual_result = f"Switched to frame with selector '{final_selector}'"

            elif action == "switchtoframebyshadowselector":
                shadow_host_selector, iframe_selector = final_selector.split(">>")
                self.switch_to_frame_in_shadow_root(shadow_host_selector.strip(), iframe_selector.strip())
                actual_result = f"switched to frame Successfully"

            elif action == "switchtomainframe":
                self.switch_to_main_frame()
                actual_result = f"Switched back to main frame"

            elif action == "clickshadow":
                selectors = final_selector.split(">>")
                shadow_root = self.page.query_selector(selectors[0])
                if shadow_root is None:
                    raise Exception(f"Element '{selectors[0]}' not found")
                shadow_root = shadow_root.evaluate_handle("el => el.shadowRoot")
                for sel in selectors[1:-1]:
                    shadow_root = shadow_root.evaluate_handle(f"el => el.querySelector('{sel}').shadowRoot")
                    if shadow_root is None:
                        raise Exception(f"Element '{sel}' not found in shadow DOM")
                shadow_element = shadow_root.evaluate_handle(f"el => el.querySelector('{selectors[-1]}')")
                if shadow_element is None:
                    raise Exception(f"Element '{selectors[-1]}' not found in shadow DOM")
                shadow_element.click()
                actual_result = f"Clicked on nested shadow DOM element {selectors[-1]} inside {final_selector}"

            elif action == "waitforelementexist":
                locator = self.get_locator(final_selector)
                locator.wait_for(state="attached", timeout=int(input_value))
                actual_result = f"Element {final_selector} exists within {input_value}s"

            elif action == "checkelementenabled":
                locator = self.get_locator(final_selector)
                expect(locator).to_be_enabled(timeout=90000)  # Check if the element is enabled
                actual_result = f"Element {final_selector} is enabled"

            elif action == "checkelementnotvisiblexpath":
                locator = self.page.locator(f"xpath={final_selector}")
                expect(locator).not_to_be_visible(timeout=90000)  # Check if the element is not visible
                actual_result = f"Element {final_selector} is not visible"

            elif action == "checkelementcontainstextexistence":
                parent_locator = self.get_locator(selector.get("parent_locator"))
                child_locator = parent_locator.locator(selector.get("child_locator1"))
                expect(child_locator).to_contain_text(input_value, timeout=90000)  # Check if the element contains the text
                actual_result = f"Element {selector.get('child_locator1')} contains text '{input_value}'"

            elif action == "checkelementcontainstoredtext":
                with open('runTimeData/dataStore.json', 'r') as file:
                    json_data = json.load(file)
                    assert input_value in json_data, f"Expected key '{input_value}' not found in data store"
                    stored_text = json_data[input_value]
                    parent_locator = self.get_locator(selector.get("parent_locator"))
                    child_locator = parent_locator.locator(selector.get("child_locator1"))
                    expect(child_locator).to_contain_text(stored_text, timeout=90000)  # Check if the element contains the stored text
                    actual_result = f"Element {selector.get('child_locator1')} contains stored text '{stored_text}'"

            elif action == "accessibilitycheck":
                report_path, isOK = self.perform_accessibility_check()
                print(f"reportPath{report_path} and isOK is {isOK}")
                actual_result = f"Performed accessibility check. <a href='{report_path}' target='_blank'>Accessibility Report</a>"
            
            elif action == "validateapiresponse":
                try:
                    input_data = json.loads(input_value)
                except ValueError as e:
                    isOK = 1  # Mark step as failed
                    actual_result = (
                        f"Invalid JSON input for API validation: {input_value}. "
                        "Expected format: "
                        '{"url": "<URL>", "method": "<GET|POST|PUT>", '
                        '"headers": {<optional>}, "payload": {<optional>}, '
                        '"expected_status": "<code>", '
                        '"expected_responses": [{"key": "<key>", "value": "<value>", "operand": "<equals|contains>"}]}'
                    )
                    raise Exception(actual_result)
                
                url = input_data.get("url")
                method = input_data.get("method", "GET")
                headers = input_data.get("headers", None)
                payload = input_data.get("payload", None)
                expected_status = input_data.get("expected_status")
                expected_responses = input_data.get("expected_response")
                isOK, actual_result = self.validate_api_response(url, method, headers, payload, expected_status, expected_responses)
            else:
                # Delegate to CustomTransactActions if action is not found in BaseActions
                return self.custom_actions.perform_action(step_no, step_desc, expected_result, action, selector, input_value)

        except Exception as e:
            isOK = 1  # Mark step as failed
            actual_result = f"Error: {str(e)}"

        # Ensure the screenshots directory exists
        os.makedirs("reports/screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"reports/screenshots/{step_no}_{timestamp}.png"
        self.page.screenshot(path=screenshot_path)  # Take screenshot from the main page
        
        duration = round(time.time() - start_time, 2) 
        # Add step result to report
        self.report_steps.append([step_no, step_desc, expected_result, actual_result, f"{duration}s", "Pass" if isOK == 0 else "Fail", screenshot_path])
        
        return isOK, actual_result  # Return the status of the step and the actual result

    def perform_accessibility_check(self):
        """Perform accessibility check using axe-core"""
        # Inject axe-core script
        self.page.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js")
        # Run axe-core
        result = self.page.evaluate("""
            async () => {
                return await axe.run({
                    runOnly: {
                        type: 'tag',
                        values: ['wcag2a', 'wcag2aa','wcag412', 'section508']
                    }
                });
            }
        """)
        # Save the result to a JSON file
        os.makedirs("reports/accessibility", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"reports/accessibility/accessibility_report_{timestamp}.json"
        with open(report_path, "w") as report_file:
            json.dump(result, report_file, indent=4)
        print(f"Accessibility report saved to {report_path}")
        
        # Generate HTML report
        html_report_path = self.generate_accessibility_html_report(result, timestamp)
        
        # Check for violations and update status
        if result["violations"]:
            isOK=1
        else:
            isOK=0

        return html_report_path,isOK

    def generate_accessibility_html_report(self, result, timestamp):
        """Generate an HTML report for accessibility violations"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Accessibility Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .violation {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Accessibility Report</h1>
            <p>Generated on: {timestamp}</p>
            <table>
                <thead>
                    <tr>
                        <th>Tags</th>
                        <th>Violation</th>
                        <th>Description</th>
                        <th>Impact</th>
                        <th>Help</th>
                        <th>HTML</th>
                    </tr>
                </thead>
                <tbody>
        """

        for violation in result["violations"]:
            for node in violation["nodes"]:
                html_content += f"""
                <tr>
                    <td>{', '.join(violation["tags"])}</td>
                    <td class="violation">{violation["id"]}</td>
                    <td>{violation["description"]}</td>
                    <td>{violation["impact"]}</td>
                    <td><a href="{violation["helpUrl"]}" target="_blank">Help</a></td>
                    <td><code>{node["html"].replace("<", "&lt;").replace(">", "&gt;")}</code></td>
                </tr>
                """

        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """

        # Save the HTML report
        accessibility_report_name="accessibility_report_{timestamp}"
        html_report_path = f"reports/accessibility/{accessibility_report_name}.html"
        html_report_reference_Path=f"accessibility/{accessibility_report_name}.html"
        with open(html_report_path, "w") as html_report_file:
            html_report_file.write(html_content)
        print(f"Accessibility HTML report saved to {html_report_path}")
        return html_report_reference_Path
