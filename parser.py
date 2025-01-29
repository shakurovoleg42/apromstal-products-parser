import requests
import gspread
import google.auth
from google.auth.transport.requests import Request
import time
import logging
import json
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Константы
GOOGLE_SHEETS_CREDENTIALS = "credintails.json"
SPREADSHEET_ID = "1y_IUnjRHsdEKMDVOYBAFFEAJmzNa9_DJrA_E-10dqac"
SHEET_NAME = "Лист1"
API_URL = "https://api.apromstal.kz/api/products/"
LOCAL_JSON_FILE = "products.json"
LAST_URL_FILE = "last_url.txt"


# Авторизация в Google Sheets
def authenticate_with_google(credentials_file):
    credentials, project = google.auth.load_credentials_from_file(credentials_file)
    credentials = credentials.with_scopes(
        ["https://www.googleapis.com/auth/spreadsheets"]
    )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return credentials


# Получение данных из API
def fetch_all_products(api_url):
    products = []
    current_url = api_url

    while current_url:
        try:
            logging.info(f"Запрос к API: {current_url}")
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "products" in data:
                products.extend(data["products"])
                save_products_to_local_json(data["products"], LOCAL_JSON_FILE)
                write_to_google_sheet(
                    data["products"],
                    GOOGLE_SHEETS_CREDENTIALS,
                    SPREADSHEET_ID,
                    SHEET_NAME,
                )

                last_url = data.get("pagination", {}).get("next_page_url")
                if last_url:
                    write_last_url(LAST_URL_FILE, last_url)
                    logging.info(f"Обновлен last_url.txt: {last_url}")
                else:
                    logging.warning("Следующей страницы нет.")

                current_url = last_url
            else:
                logging.error("Некорректный ответ API.")
                break

            time.sleep(10)
        except requests.RequestException as e:
            logging.error(f"Ошибка запроса: {e}")
            break
    return products


# Запись в локальный JSON файл
def save_products_to_local_json(products, file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r+", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_data.extend(products)
                f.seek(0)
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=4)
        logging.info(f"Сохранено в {file_path}")
    except Exception as e:
        logging.error(f"Ошибка записи в JSON: {e}")


# Запись в Google Таблицу
def write_to_google_sheet(data, credentials_file, spreadsheet_id, sheet_name):
    try:
        credentials = authenticate_with_google(credentials_file)
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
        rows = [
            [f"https://apromstal.kz/products/{product['slug']}"] for product in data
        ]
        sheet.append_rows(rows)
        logging.info("Данные добавлены в Google Таблицу.")
    except Exception as e:
        logging.error(f"Ошибка записи в Google Таблицу: {e}")


# Чтение последнего URL
def read_last_url(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return API_URL


# Запись последнего URL
def write_last_url(file_path, url):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(url)
        logging.info(f"Последний URL ({url}) записан в {file_path}")
    except Exception as e:
        logging.error(f"Ошибка записи в {file_path}: {e}")


def main():
    try:
        logging.info("Запуск программы.")
        last_url = read_last_url(LAST_URL_FILE)
        products = fetch_all_products(last_url)
        logging.info("Данные успешно обновлены.")
    except Exception as e:
        logging.error(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
