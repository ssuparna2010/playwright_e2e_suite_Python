from playwright.sync_api import Page, expect
import pytest
import time
import os
from datetime import datetime
import json

class BaseActions:
    def __init__(self, page: Page, report_steps):
        self.page = page
        self.report_steps = report_steps  # Store test steps
        self.main_page = page  # Store reference to the main page
        
    def get_locator(self, selector):
        """Detect whether the selector is XPath or CSS"""
        if not isinstance(selector, str):
            raise ValueError(f"Invalid selector: {selector}")
        selector = selector.strip()
        if selector.startswith("//") or selector.startswith("("):
            return self.page.locator(f"xpath={selector}")
        return self.page.locator(selector)
    
    def get_expected_result(self, action, selector, input_value):
        """Dynamically generate the expected result based on action type."""
        if action == "Type":
            return f"Text '{input_value}' should be entered in {selector}"
        elif action == "Click":
            return f"Element {selector} should be clicked"
        elif action == "Assert":
            return f"Element {selector} should be visible"
        elif action == "Title":
            return f"Page title should be '{input_value}'"
        elif action == "Wait":
            return f"Wait for {input_value}ms"
        elif action == "WaitForElementExist":
            return f"Element {selector} should exist within {input_value}ms"
        else:
            return f"Action '{action}' executed successfully"

    def switch_to_frame_by_index(self, index):
        """Switch to the iframe specified by the index"""
        frames = self.page.frames
        if index < 0 or index >= len(frames):
            raise Exception(f"Frame index {index} is out of bounds")
        frame = frames[index]
        self.page = frame
        print(f"Switched to frame at index {index}")


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
        # Print the HTML content of the iframe
        frame_content = self.page.content()
        print(frame_content)

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

    def perform_action(self, step_no, step_desc, expected_result, action, selector, input_value=None):
        """Perform action based on test script and log failures if element not found"""
        start_time = time.time()
        isOK = 0  # 0 = Success, 1 = Failure
        actual_result = ""
        screenshot_path = None  # Store screenshot if failure occurs
        
        try:
            if action.lower() == "type":
                locator = self.get_locator(selector)
                locator.wait_for(state="visible", timeout=5000)  # Wait for visibility
                locator.fill(str(input_value))
                actual_result = f"Typed '{input_value}' in {selector}"

            elif action.lower() == "click":
                locator = self.get_locator(selector)
                locator.wait_for(state="visible", timeout=5000)  # Wait for visibility
                locator.click()
                actual_result = f"Clicked on {selector}"

            elif action.lower() == "assert":
                if selector == "title":
                    assert self.page.title() == input_value, f"Expected '{input_value}', got '{self.page.title()}'"
                    actual_result = f"Page title matched: {input_value}"
                else:
                    locator = self.get_locator(selector)
                    expect(locator).to_have_text(input_value, timeout=5000)
                    actual_result = f"Verified text '{input_value}' in {selector}"
                    
            elif action.lower() == "wait":
                self.page.wait_for_timeout(int(input_value))  # Convert input to integer (milliseconds)
                actual_result = f"Waited for {input_value}ms"

            elif action.lower() == "switchtoframe":
                if selector.isdigit():
                    self.switch_to_frame_by_index(int(selector))
                else:
                    self.switch_to_frame_by_selector(selector)
                actual_result = f"Switched to frame with selector '{selector}'"

            elif action.lower() == "switchtoframebyshadowselector":
                shadow_host_selector, iframe_selector = selector.split(">>")
                self.switch_to_frame_in_shadow_root(shadow_host_selector.strip(), iframe_selector.strip())
                actual_result = f"Switched to frame inside shadow root with selector '{selector}'"

            elif action.lower() == "switchtomainframe":
                self.switch_to_main_frame()
                actual_result = f"Switched back to main frame"

            elif action.lower() == "clickshadow":
                selectors = selector.split(">>")
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
                actual_result = f"Clicked on nested shadow DOM element {selectors[-1]} inside {selector}"

            elif action.lower() == "waitforelementexist":
                locator = self.get_locator(selector)
                locator.wait_for(state="attached", timeout=int(input_value))
                actual_result = f"Element {selector} exists within {input_value}ms"

            elif action.lower() == "accessibilitycheck":
                report_path,isOK = self.perform_accessibility_check()
                print(f"reportPath{report_path} and isOK is {isOK}")
                actual_result = f"Performed accessibility check. <a href='{report_path}' target='_blank'>Accessibility Report</a>"

        except Exception as e:
            isOK = 1  # Mark step as failed
            actual_result = f"Error: {str(e)}"

        # Ensure the screenshots directory exists
        os.makedirs("reports/screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"reports/screenshots/{step_no}_{timestamp}.png"
        self.main_page.screenshot(path=screenshot_path)  # Take screenshot from the main page
        
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
