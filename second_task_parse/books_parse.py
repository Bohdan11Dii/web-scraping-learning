import json

import requests
from bs4 import BeautifulSoup
import os
import re  # Модуль для очищення рядків від заборонених символів
from fake_useragent import UserAgent


def fetch_html(url, header=None):
    try:
        response = requests.get(url, timeout=10, headers=header)  # Завжди став timeout!
        response.raise_for_status()  # Якщо статус 404 або 500, це викличе помилку
        return response.text
    except requests.exceptions.RequestException as req_err:
        # Спочатку можна перехопити специфічні помилки мережі
        print(f"❌ Помилка мережі при запиті до {url}: {req_err}")
        return None
    except Exception as e:
        # А тут ми страхуємося від будь-яких інших непередбачуваних помилок
        print(f"💥 Непередбачувана помилка: {e}")
        return None


def parse_page_books(html_content, base_url):
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    find_tag_product = soup.find_all("article", class_="product_pod")

    if not find_tag_product:
        return []

    all_books = []
    for product in find_tag_product:
        h3_tag = product.find("h3")
        title = h3_tag.find("a")["title"] if h3_tag else "Невідомо"

        price = product.find("p", class_="price_color").text
        availability = product.find("p", class_="instock availability").text.strip()

        img_tag = product.find("img", class_="thumbnail")
        src_link = img_tag["src"] if img_tag else ""

        clean_src = src_link.replace("../", "")
        image_url = base_url + clean_src

        all_books.append({
            "title": title,
            "price": price,
            "availability": availability,
            "image_url": image_url
        })

    return all_books


# Ідеальна за SOLID функція: вона вміє ТІЛЬКИ завантажувати і зберігати бінарний файл
def download_single_image(img_url, folder_name, file_name, header=None):
    try:
        # Очищаємо назву файлу від символів, які заборонені в Windows/Linux (\ / : * ? " < > |)
        safe_file_name = re.sub(r'[\\/*?:"<>|]', "", file_name)
        # Замінимо пробіли на нижнє підкреслення, щоб назва файлу була красивою
        safe_file_name = safe_file_name.replace(" ", "_")

        file_path = os.path.join(folder_name, f"{safe_file_name}.jpg")

        # Робимо запит за картинкою
        response = requests.get(img_url, headers=header, timeout=10)
        if response.status_code == 200:
            # Записуємо чисті бінарні дані (.content) без жодних декодувань в текст
            with open(file_path, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Не вдалося завантажити картинку {file_name}: {e}")
    return False


def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Дані успішно збережено у файл {filename}!")


def get_next_page_url(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    pagination = soup.select_one(".next a")

    if pagination is None:
        return None

    return pagination.get("href")


if __name__ == "__main__":

    CURRENT_URL = "https://books.toscrape.com/"
    UA = UserAgent()
    header = {"User-Agent": UA.random}

    # 1. Отримуємо HTML
    ALL_SITE_BOOKS = []

    while CURRENT_URL:
        try:

            print("Початковий урл -----", CURRENT_URL)
            print("Починаємо парсинг сайту...")
            html = fetch_html(CURRENT_URL, header)

            if html:
                print("HTML успішно отримано!")

                # 2. Парсимо дані про книги (отримуємо список словників)
                books = parse_page_books(html, CURRENT_URL)
                print(f"Знайдено книг на сторінці: {len(books)}")

                # 3. Створюємо папку для фото, якщо її немає
                folder_name = "photos"
                os.makedirs(folder_name, exist_ok=True)

                # 4. Завантажуємо картинки, використовуючи вже готові дані з книги!
                downloaded_count = 0
                for book in books:
                    success = download_single_image(
                        img_url=book["image_url"],
                        folder_name=folder_name,
                        file_name=book["title"],
                        header=header
                    )
                    if success:
                        downloaded_count += 1

                print(f"Успішно завантажено {downloaded_count} з {len(books)} картинок.")
                print("-----------------------------------------------------------------")
                if books:
                    ALL_SITE_BOOKS.extend(books)

                # Крок 3: Шукаємо відносний шлях до НАСТУПНОЇ сторінки (наприклад, '/page/2/')
                pagination_url = get_next_page_url(html)

                # Крок 4: Оновлюємо current_url для наступної ітерації циклу
                if pagination_url:
                    # Склеюємо домен і відносний шлях
                    if "catalogue" in pagination_url:
                        CURRENT_URL = f"https://books.toscrape.com/{pagination_url}"

                    else:
                        CURRENT_URL = f"https://books.toscrape.com/catalogue/{pagination_url}"
                
                else:
                    # Якщо кнопки "Next" немає (остання сторінка) — робимо None, і цикл зупиниться
                    CURRENT_URL = None
        except ConnectionError as e:
            print(e)

    save_to_json(ALL_SITE_BOOKS, "books.json")

    print("\nПарсинг завершено!")
    print(f"Всього зібрано цитат: {len(ALL_SITE_BOOKS)}")
