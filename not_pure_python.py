import os
from pathlib import Path
import time

import requests
from robocorp import browser
from robocorp import workitems
from robocorp.tasks import task
from RPA.Excel.Files import Files as Excel

FILE_NAME = "challenge.xlsx"
EXCEL_URL = f"https://rpachallenge.com/assets/downloadFiles/{FILE_NAME}"
OUTPUT_DIR = Path(os.getenv("ROBOT_ARTIFACTS", "output"))


@task
def solve_challenge():
    """
    Main task which solves the RPA challenge!

    Downloads the source data Excel file and uses Playwright to fill the entries inside
    rpachallenge.com.
    """
    item = workitems.inputs.current
    print("Received payload:", item.payload)
    browser.configure(
        browser_engine="firefox", screenshot="only-on-failure", headless=False
    )
    try:
        # Reads a table from an Excel file hosted online.
        # excel_file = download_file(
        #     EXCEL_URL, target_dir=OUTPUT_DIR, target_filename=FILE_NAME
        # )
        # excel = Excel()
        # excel.open_workbook(excel_file)
        # rows = excel.read_worksheet_as_table("Sheet1", header=True)

        # Surf the automation challenge website and fill in information from the table
        #  extracted above.
        page = browser.goto("https://www.latimes.com/")
        page.click(
            "//button[@class='flex justify-center items-center h-10 py-0 px-2.5 bg-transparent border-0 text-header-text-color cursor-pointer transition-colors hover:opacity-80 xs-5:px-5 md:w-10 md:p-0 md:ml-2.5 md:border md:border-solid md:border-header-border-color md:rounded-sm lg:ml-3.75']",
            timeout=60000,
        )
        page.fill("//input[@placeholder='Search']", item.payload.get("message"))
        page.keyboard.press("Enter")
        time.sleep(3)
        select_category(item.payload.get("category"), page)
        page.select_option("//select[@name='s']", "1")
        time.sleep(10)

        # browser.screenshot(element)
    finally:
        # A place for teardown and cleanups. (Playwright handles browser closing)
        print("Automation finished!")


def select_category(item_category: list[str], page):
    if len(item_category) == 0:
        return
    try:
        for item in item_category:
            page.click(f"//span[normalize-space()='{item}']")
    except:
        print(f"Category not found")


def extract_table_elements(page):
    ul_element = page.find_element("//ul[@class='search-results-module-results-menu']")

    # Get all <li> elements inside the <ul>
    li_elements = ul_element.find_elements_by_tag_name("li")

    # Iterate through each <li> element and extract text or other attributes
    for li in li_elements:
        print(li.text)


def download_file(url: str, *, target_dir: Path, target_filename: str) -> Path:
    """
    Downloads a file from the given URL into a custom folder & name.

    Args:
        url: The target URL from which we'll download the file.
        target_dir: The destination directory in which we'll place the file.
        target_filename: The local file name inside which the content gets saved.

    Returns:
        Path: A Path object pointing to the downloaded file.
    """
    # Obtain the content of the file hosted online.
    response = requests.get(url)
    response.raise_for_status()  # this will raise an exception if the request fails
    # Write the content of the request response to the target file.
    target_dir.mkdir(exist_ok=True)
    local_file = target_dir / target_filename
    local_file.write_bytes(response.content)
    return local_file
