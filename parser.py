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

# Учетные данные для Google Sheets
GOOGLE_SHEETS_CREDENTIALS = "credintails.json"  # Путь к файлу с учетными данными
SPREADSHEET_ID = "1y_IUnjRHsdEKMDVOYBAFFEAJmzNa9_DJrA_E-10dqac"
SHEET_NAME = "Лист1"  # Название листа в таблице

# API URL
API_URL = "https://api.apromstal.kz/api/products/"

# Путь для сохранения локального JSON файла
LOCAL_JSON_FILE = "products.json"


# Авторизация с использованием Google Credentials
def authenticate_with_google(credentials_file):
    credentials, project = google.auth.load_credentials_from_file(credentials_file)

    # Указываем scope для работы с Google Sheets API
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # Применяем правильный scope
    credentials = credentials.with_scopes(SCOPES)

    # Если токен истек, обновляем его
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())  # Обновляем токен, если он истек
    return credentials


# Получение данных из API
def fetch_all_products(api_url):
    products = []  # Список для хранения всех продуктов
    current_url = api_url  # Текущий URL для запроса

    while current_url:
        try:
            logging.info(
                f"Отправка запроса на URL: {current_url}"
            )  # Логирование запроса
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()  # Проверка на ошибки
            data = response.json()

            if "products" in data:
                # Добавляем продукты в список
                products.extend(data["products"])

                # Сразу записываем данные в локальный JSON и Google Таблицу
                save_products_to_local_json(data["products"], LOCAL_JSON_FILE)
                write_to_google_sheet(
                    data["products"],
                    GOOGLE_SHEETS_CREDENTIALS,
                    SPREADSHEET_ID,
                    SHEET_NAME,
                )

                # Получаем следующую страницу
                current_url = data.get("pagination", {}).get("next_page_url")
                logging.info(
                    f"Найдено {len(data['products'])} продуктов на текущей странице."
                )
            else:
                logging.error("Некорректный ответ API.")
                break

            # Задержка между запросами (например, 2 секунды)
            time.sleep(10)

        except requests.RequestException as e:
            logging.error(f"Ошибка запроса: {e}")
            break

    return products


# Сохранение продуктов в локальный JSON файл
def save_products_to_local_json(products, file_path):
    try:
        # Если файл существует, не перезаписываем, а добавляем новые данные
        if os.path.exists(file_path):
            with open(file_path, "r+", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_data.extend(
                    products
                )  # Добавляем новые продукты к существующим
                f.seek(0)  # Перемещаем указатель в начало файла
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
            logging.info(f"Данные успешно добавлены в файл: {file_path}")
        else:
            # Если файл не существует, создаем новый
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=4)
            logging.info(f"Данные успешно сохранены в новый файл: {file_path}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных в JSON файл: {e}")


# Запись данных в Google Таблицу
def write_to_google_sheet(data, credentials_file, spreadsheet_id, sheet_name):
    try:
        # Авторизация в Google Sheets API
        credentials = authenticate_with_google(credentials_file)
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

        # Преобразуем данные: добавляем префикс к slug
        rows = [
            [f"https://apromstal.kz/products/{product['slug']}"] for product in data
        ]

        logging.info(f"Записываем {len(rows)} продуктов в Google Таблицу...")
        # Записываем данные начиная с первой строки в столбце A
        sheet.append_rows(rows)  # Используем append_rows для добавления новых данных
        logging.info("Данные успешно записаны в Google Таблицу.")
    except Exception as e:
        logging.error(f"Ошибка при записи в Google Таблицу: {e}")


def main():
    try:
        logging.info("Запуск программы.")
        # Шаг 1: Получаем все продукты из API (включая постраничные данные)
        fetch_all_products(API_URL)
        logging.info(
            "Данные успешно записаны в Google Таблицу и сохранены в локальный JSON файл."
        )
    except Exception as e:
        logging.error(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
