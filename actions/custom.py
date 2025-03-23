from datetime import datetime
import os
import time
from playwright.sync_api import Page

class CustomTransactActions:
    def __init__(self, page: Page, report_steps):
        self.page = page
        self.report_steps = report_steps  # Store test steps

    def perform_action(self, step_no, step_desc, expected_result, action, selector=None, input_value=None):
        """Perform custom transact-related actions"""
        start_time = time.time()
        isOK = 0  # 0 = Success, 1 = Failure
        actual_result = ""
        screenshot_path = None  # Store screenshot if failure occurs

        try:
            action = action.lower()  # Convert action to lower case for case-insensitive comparison

            if action == "clickfindbutton":
                locator = self.page.locator('app-root button[name="Find"]')
                locator.wait_for(state="visible", timeout=90000)  # Wait for visibility
                locator.click(force=True)  # Click the element with force
                actual_result = "Clicked on find button successfully"

            elif action == "clickvalidatebutton":
                locator = self.page.locator('app-root button[name="Validate a deal"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on validate button successfully"

            elif action == "clickcommitbutton":
                locator = self.page.locator('app-root button[name="Commit the deal"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on commit button successfully"

            elif action == "clickupdatebutton":
                locator = self.page.locator('app-root button[name="Update"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on update button successfully"

            elif action == "clickmoreoptionsbutton":
                locator = self.page.locator('app-root button[name="MoreOptions"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                self.page.wait_for_timeout(2000)  # Wait for 2 seconds
                locator.click(force=True)
                actual_result = "Clicked on more options button successfully"

            elif action == "clickrtabutton":
                locator = self.page.locator('app-root button[name="Return to application screen"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on RTA button successfully"

            elif action == "clickholdbutton":
                locator = self.page.locator('app-root button[name="Place a contract on Hold"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on hold button successfully"

            elif action == "clickhelpbutton":
                locator = self.page.locator('app-root button[name="Help"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on help button successfully"

            elif action == "clicksearchfieldsbutton":
                locator = self.page.locator('app-root button[name="Search"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on search fields button successfully"

            elif action == "clickinfobutton":
                locator = self.page.locator('app-root button[name="Info"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on info button successfully"

            elif action == "clickverifybutton":
                locator = self.page.locator('app-root button[name="Verifies a deal"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on verify button successfully"

            elif action == "clickreversebutton":
                locator = self.page.locator('app-root button[name="Reverses a deal from the live file"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on reverse button successfully"

            elif action == "clicknewdealbutton":
                locator = self.page.locator('app-root button[name="screenNewTool"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on new deal button successfully"

            elif action == "clickeditbutton":
                locator = self.page.locator('app-root button[name="screenEditTool"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on edit button successfully"

            elif action == "clickviewbutton":
                locator = self.page.locator('app-root button[name="screenViewTool"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on view button successfully"

            elif action == "clickperformactionbutton":
                locator = self.page.locator('app-root button[name="screenActionTool"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on perform action button successfully"

            elif action == "clickmoreactionsbutton":
                locator = self.page.locator('app-root button[name="idInputMenu"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on more actions button successfully"

            elif action == "clickappscreenhelpbutton":
                locator = self.page.locator('app-root button[name="screenHelpTool"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on app screen help button successfully"

            elif action == "clickdeletebutton":
                locator = self.page.locator('app-root button[name="Deletes a Deal"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on delete button successfully"

            elif action == "clickauthorisebutton":
                locator = self.page.locator('app-root button[name="Authorises a deal"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on authorise button successfully"

            elif action == "clickenquiryselectionbutton":
                locator = self.page.locator('app-root button[name="EnquirySelection"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on enquiry selection button successfully"

            elif action == "clickcolumnselectorbutton":
                locator = self.page.locator('app-root button[name="ColumnSelector"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on column selector button successfully"

            elif action == "clickrefreshbutton":
                locator = self.page.locator('app-root button[name="Refresh"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on refresh button successfully"

            elif action == "clickautorefreshbutton":
                locator = self.page.locator('app-root button[name="AutoRefresh"]')
                locator.wait_for(state="visible", timeout=90000)
                locator.click(force=True)
                actual_result = "Clicked on auto refresh button successfully"

            else:
                raise ValueError(f"Unsupported action: {action}")

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
