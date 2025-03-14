# playwright_e2e_suite_Python
The Playwright framework is developed using Python to validate UI and perform accessibility checks, ensuring the interface is functional and accessible. I plan to add API testing functionality to validate backend services and integrate generative AI to enhance testing efficiency, though this feature is still in research.

# Playwright with Python

Playwright is a powerful library for browser automation that allows you to control web browsers and interact with web pages programmatically. It supports multiple browsers such as Chromium, Firefox, and WebKit, and provides a high-level API to perform various browser actions.

## Installation

To use Playwright with Python, you need to install the `playwright` package. You can install it using pip:
## Overview
This project uses Playwright for browser automation and testing. It includes functionalities for performing various actions on web elements, checking accessibility compliance, and generating detailed reports.

## Setup

### Prerequisites
- Python 3.7 or higher
- Playwright
- pytest
- pytest-html

### Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/ssuparna2010/playwright_e2e_suite_Python.git
   cd playwright-automation

2. Install the required dependencies:
    pip install -r requirements.txt
    playwright install

3. Set up environment variables: Create a .env file in the root directory and add the necessary environment variables.

5. 4. Running Tests
To run the tests and generate an HTML report, use the following command:
    pytest [test_init.py] --html=report.html --self-contained-html
6. Directory Structure
actions/: Contains the BaseActions class with methods for performing various actions.
config/: Contains configuration files.
reports/: Contains generated reports.
tests/: Contains test scripts.
7. Key Features
  Browser Automation: Perform actions like clicking, typing, and switching frames.
  Accessibility Checks: Perform accessibility checks using axe-core and generate detailed reports.
  Error Handling: Handle timeouts and exceptions gracefully to ensure tests do not hang.

