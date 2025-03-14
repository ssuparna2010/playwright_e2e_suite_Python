import pytest
import configparser
from playwright.sync_api import sync_playwright
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read config.ini file
config = configparser.ConfigParser()
try:
    config.read("config\config.ini")
    browser_name = config["playwright"]["browser"].strip()
    headless_mode = config.getboolean("playwright", "headless")
    force_new_browser_session = config.getboolean("playwright", "force_new_browser_session")
    logger.info(f"force_new_browser_session: {force_new_browser_session}")
except Exception as e:
    logger.error(f"Error reading config.ini: {str(e)}")
    pytest.fail(f"Configuration error: {str(e)}")

@pytest.fixture(scope="session")
def playwright():
    """Fixture to manage Playwright instance."""
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright):
    """Fixture to manage browser instance."""
    if not force_new_browser_session:
        logger.info("Launching browser for the session...")
        browser = getattr(playwright, browser_name).launch(headless=headless_mode)
        yield browser
        logger.info("Closing browser after the session...")
        browser.close()
    else:
        logger.info("No browser launched for the session (force_new_browser_session=True).")
        yield None

@pytest.fixture(scope="session")
def browser_context(browser, playwright):
    """Fixture to manage browser context."""
    if not force_new_browser_session:
        logger.info("Creating a new browser context for the session...")
        context = browser.new_context()
        yield context
        logger.info("Closing browser context after the session...")
        context.close()
    else:
        logger.info("No browser context created for the session (force_new_browser_session=True).")
        yield None

@pytest.fixture
def page(browser_context, playwright):
    """Fixture to manage page instance."""
    if force_new_browser_session:
        logger.info("Launching new browser and context for this test case...")
        browser = getattr(playwright, browser_name).launch(headless=headless_mode)
        context = browser.new_context()
        page = context.new_page()
        yield page
        logger.info("Closing browser and context for this test case...")
        context.close()
        browser.close()
    else:
        logger.info("Reusing browser context and creating a new page for this test case...")
        page = browser_context.new_page()
        yield page
        logger.info("Closing page for this test case...")
        page.close()

@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    """Generate HTML report after all tests have run."""
    from test_init import test_results
    from report_generator import generate_html_report
    if test_results:
        generate_html_report(test_results)
