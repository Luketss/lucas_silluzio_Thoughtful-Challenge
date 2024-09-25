import os
from pathlib import Path
import time
import logging
import datetime
from robocorp import workitems
from robocorp.tasks import task

from RPA.Browser.Selenium import Selenium
from RPA.Robocorp.WorkItems import WorkItems

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from util import (
    set_month_range,
    write_csv_data,
    replace_date_with_hour,
    download_image_from_url,
    check_for_dolar_sign,
    check_phrases,
    create_image_folder,
    get_all_files_from_folder,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(os.getenv("ROBOT_ARTIFACTS", "output"))
result_file_name = "result.xlsx"
result_file_path = os.path.join(OUTPUT_DIR, result_file_name)
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


class SeleniumScraper:
    def __init__(self, url, search_phrase, category, number_months, wi):
        self.url = url
        self.search_phrase = search_phrase
        self.category = category
        self.number_months = number_months
        self.wi = wi
        self.driver = None
        self.headless = False
        self.result = []
        logger.info(
            f"""Received payload:
            url:{self.url},
            phrase:{self.search_phrase},
            category:{self.category},
            months:{self.number_months},"""
        )

    def set_browser_options(self, browser="firefox"):
        if browser == "chrome":
            options = webdriver.ChromeOptions()
        else:
            options = webdriver.FirefoxOptions()

        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--start-maximized")
        return options

    def open_browser(self, browser="firefox"):
        logger.info(f"Opening {browser} browser")
        options = self.set_browser_options(browser)
        if browser == "chrome":
            self.driver = webdriver.Chrome(options=options)
        else:
            self.driver = webdriver.Firefox(options=options)
        self.driver.maximize_window()

    def close_browser(self):
        if self.driver:
            self.driver.quit()

    def open_website(self):
        self.driver.get(self.url)
        wait = WebDriverWait(self.driver, 10)

    def begin_search(self):
        logger.info(f"start search")
        try:
            wait = WebDriverWait(self.driver, 10)
            search_button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[@aria-label='Go to search page']",
                    )
                )
            )
            self.driver.execute_script("arguments[0].click();", search_button)
            search_field = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//input[@placeholder='search']")
                )
            )
            search_field.send_keys(self.search_phrase)
            time.sleep(1)
            search_field.send_keys(Keys.ENTER)

            time.sleep(3)

        except Exception as e:
            print(f"Error during search: {e}")

    def select_category(self):
        logger.info(f"selection category")
        category_list = self.category
        if len(category_list) == 0:
            return
        for category_item in category_list:
            try:
                section = self.driver.find_element(
                    By.XPATH, f"//span[normalize-space()='{category_item}']"
                )
                section.click()
            except Exception as e:
                print(f"Category not found: {e}")

    def sort_newest_news(self, list_value="1"):
        logger.info(f"selecting newest")
        try:
            sort_dropdown = self.driver.find_element(By.XPATH, "//select[@name='s']")
            for option in sort_dropdown.find_elements(By.TAG_NAME, "option"):
                if option.get_attribute("value") == list_value:
                    option.click()
                    break
        except Exception as e:
            print(f"Error sorting news: {e}")

    def load_all_news(self):
        wait = WebDriverWait(self.driver, 120)
        logger.info("Waiting for page to load")
        arrow_element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//span[@class='pi pi-arrow-right p-button-icon']")
            )
        )
        logger.info("Page is fully loaded")

    def click_load_more(self):
        wait = WebDriverWait(self.driver, 3)
        while True:
            try:
                logger.info("Loading all data from page")
                button_element = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//span[normalize-space()='Load More']")
                    )
                )
                button_element.click()
            except:
                logger.info("All data is on page")
                break

    def get_ul_content(self):
        search_phrase = self.search_phrase
        result_list_element_xpath = "//div[@id='resultList']//div[@class='col']"
        result_list_element = self.driver.find_element(
            By.XPATH, result_list_element_xpath
        )
        div_elements = result_list_element.find_elements(
            By.XPATH, "//div[@class='col']/div"
        )
        logger.info(len(div_elements))
        for i in range(1, len(div_elements) - 1):
            element_title = div_elements[i].find_element(
                By.XPATH, f"(//div[@class='h2'])[{i}]"
            )
            title = element_title.text

            image = self.get_image_value(div_elements[i])

            # element_date = value.find_element(
            #     By.XPATH, ".//p[@class='promo-timestamp']"
            # )
            # date_text = element_date.text

            element_description = div_elements[i].find_element(
                By.XPATH,
                f"(//p[@class='desc'])[{i}]",
            )
            description = self.get_text_value(element_description)

            is_title_dolar = check_for_dolar_sign(title)
            is_description_dolar = check_for_dolar_sign(description)
            conut_in_title = check_phrases(text_pattern=search_phrase, text=title)
            phrases_count = check_phrases(
                text_pattern=search_phrase, text=title, count=conut_in_title
            )
            image_ref = download_image_from_url(image)
            logger.info(
                f"""{[
                    title,
                    description,
                    image_ref,
                    is_title_dolar,
                    is_description_dolar,
                    phrases_count,
                ]}"""
            )
            self.result.append(
                [
                    title,
                    description,
                    image_ref,
                    is_title_dolar,
                    is_description_dolar,
                    phrases_count,
                ]
            )

    def extract_website_data(self):
        logger.info(f"starting data extraction")
        self.load_all_news()
        self.click_load_more()
        self.get_ul_content()

        write_csv_data(self.result, result_file_path)

    def get_text_value(self, element) -> str:
        try:
            return element.text
        except:
            return ""

    def get_image_value(self, element) -> str:
        try:
            element_image = element.find_element(By.TAG_NAME, "img")
            return element_image.get_attribute("src")
        except:
            return ""

    def _wait_until_clickable(self, by, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, locator))
        )

    def _wait_until_visible(self, by, locator, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, locator))
        )

    def main(self):
        try:
            create_image_folder()
            self.open_browser()
            self.open_website()
            self.begin_search()
            # self.select_category()
            # self.sort_newest_news()
            self.extract_website_data()
        finally:
            self.close_browser()


@task
def controller():
    logger.info(f"========= CODE START ========")
    wi = WorkItems()
    wi.get_input_work_item()
    url = wi.get_work_item_variable("url")
    search_phrase = wi.get_work_item_variable("search_phrase")
    category = wi.get_work_item_variable("category")
    number_months = wi.get_work_item_variable("number_months")
    obj = SeleniumScraper(
        url=url,
        search_phrase=search_phrase,
        category=category,
        number_months=number_months,
        wi=wi,
    )
    obj.main()
    wi.create_output_work_item(
        variables={"process": "completed"}, files=result_file_path, save=True
    )
    logger.info(f"Result saved at: {result_file_path}")
