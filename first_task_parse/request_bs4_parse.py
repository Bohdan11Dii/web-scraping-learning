import json

import requests
from bs4 import BeautifulSoup
from bs4.element import AttributeValueList


# 1. Ця функція відповідає ТІЛЬКИ за мережу та перевірку статус-коду
def fetch_html(url):
    """Робить запит до сайту та повертає сирий HTML-текст, якщо все ОК."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text
        print(f"Помилка: Сервер повернув статус {response.status_code}")
    except requests.RequestException as e:
        print(f"Помилка мережі: {e}")

    return None


# 2. Ця функція відповідає ТІЛЬКИ за витягування даних з готового HTML
def parse_page_quotes(html_content):
    """Приймає сирий HTML, шукає першу цитату і повертає її дані."""
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, "html.parser")
    first_quote_div = soup.find_all("div", class_="quote")

    if not first_quote_div:
        return None

    quote_data = []

    for quote_div in first_quote_div:
        text = quote_div.find("span", class_="text").text
        author = quote_div.find("small", class_="author").text
        tags = [tag.text for tag in quote_div.find_all("a", class_="tag")]

        quote_data.append({"text": text, "author": author, "tags": tags})
    return quote_data


def get_next_page_url(html_content) -> None | str | AttributeValueList:
    soup = BeautifulSoup(html_content, "html.parser")

    pagination = soup.select_one(".next a")
    if pagination is None:
        return None
    return pagination.get("href")


def save_to_json(data, filename):
    with open(filename, "w", encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


# 3. Головний оркестратор програми
# 3. Головний оркестратор програми
if __name__ == "__main__":
    # Починаємо з першої сторінки
    current_url = "https://quotes.toscrape.com"
    ALL_QUOTES = []

    print("Починаємо парсинг сайту...")

    # Цикл працює, поки у змінній current_url є адреса сторінки
    while current_url:
        print(f"Парсимо сторінку: {current_url}")

        # Крок 1: Завантажуємо HTML ПОТОЧНОЇ сторінки
        html = fetch_html(current_url)
        if not html:
            print(f"Не вдалося завантажити сторінку: {current_url}")
            break

        # Крок 2: Парсимо цитати з цього HTML
        quote_data = parse_page_quotes(html)
        if quote_data:
            ALL_QUOTES.extend(quote_data)  # Додаємо 10 цитат до загального списку

        # Крок 3: Шукаємо відносний шлях до НАСТУПНОЇ сторінки (наприклад, '/page/2/')
        pagination_url = get_next_page_url(html)

        # Крок 4: Оновлюємо current_url для наступної ітерації циклу
        if pagination_url:
            # Склеюємо домен і відносний шлях
            current_url = f"https://quotes.toscrape.com{pagination_url}"
        else:
            # Якщо кнопки "Next" немає (остання сторінка) — робимо None, і цикл зупиниться
            current_url = None

    save_to_json(ALL_QUOTES, "quotes.json")

    print("\nПарсинг завершено!")
    print(f"Всього зібрано цитат: {len(ALL_QUOTES)}")
