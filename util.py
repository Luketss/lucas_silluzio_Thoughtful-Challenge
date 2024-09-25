import re
import os
import csv
import datetime
import requests
import uuid
import glob

from RPA.Excel.Files import Files

IMAGE_FOLDER = "./images"


def create_image_folder() -> None:
    dir = "./images"
    if not os.path.exists(dir):
        os.makedirs(dir)


def set_month_range(number_of_months: int) -> tuple[str, str]:
    today = datetime.date.today()
    end = today.strftime("%b. %d, %Y")

    if number_of_months < 2:
        start = today.replace(day=1).strftime("%b. %d, %Y")
    else:
        start = (
            (today - datetime.timedelta(days=30 * (number_of_months - 1)))
            .replace(day=1)
            .strftime("%b. %d, %Y")
        )

    return start, end


def replace_date_with_hour(date: str) -> str:
    if re.match("\d\w ago", date):
        return f"{datetime.datetime.now().strftime('%b')} {datetime.datetime.now().day}"
    return date


def write_csv_data(data: list, file_path: str) -> None:
    lib = Files()
    lib.create_workbook()
    lib.append_rows_to_worksheet(data)
    lib.save_workbook(file_path)


def download_image_from_url(image_url: str) -> str:
    image_name = str(uuid.uuid4())
    if image_url == "":
        return ""
    img_data = requests.get(image_url).content
    with open(f"./images/{image_name}.jpg", "wb") as handler:
        handler.write(img_data)
    return image_name


def check_phrases(text_pattern: str, text: str, count=0) -> int:
    """Counts occurrences of a word (ignoring punctuation) in a given text."""
    words = [word.strip(",.;:-?!") for word in text.split()]
    return words.count(text_pattern) + count


def check_for_dolar_sign(text: str) -> bool:
    """Checks if a text contains a dollar sign or mentions of dollars."""
    dollar_pattern = re.compile(
        r"(\$\s*\d{1,}(?:.\d{0,}){0,2})|(\d{1,}\s*(dollars|usd|dollar))", re.IGNORECASE
    )
    return bool(re.search(dollar_pattern, text))


def split_extracted_text(text: list) -> tuple[str, str, str]:
    """Splits a list of extracted text into date, title, and description."""
    try:
        date, title, description, *_ = text
        return date, title, description
    except ValueError:
        return "", "", ""


def get_all_files_from_folder(path: str = f"{IMAGE_FOLDER}/*.jpg") -> list[str]:
    """Returns all file paths from the specified folder."""
    return glob.glob(path)


if __name__ == "__main__":
    print(set_month_range(1))
