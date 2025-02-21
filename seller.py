import io
import logging.config
import os
import re
import zipfile
from environs import Env

import pandas as pd
import requests

logger = logging.getLogger(__file__)


def get_product_list(last_id, client_id, seller_token):
    """Получить список товаров магазина озон.

    Args:
        last_id (str): id последнего продукта в предыдущем 
        запросе для пагинации
        client_id (str): id клиента для аутентифицации API Ozon.
        seller_token (str): токен продавца для аутентификации API Ozon.

    Returns:
        dict: словарь с информаций о списке товаров от Ozon.

    Examples:
        >>> get_product_list(last_id, client_id, seller_token)
        {"result" : {"items": [{"offer_id: "78910", "name": "Casio7893"}],
        "total": 1500, "last_id": "78910"}}

    """
    url = "https://api-seller.ozon.ru/v2/product/list"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {
        "filter": {
            "visibility": "ALL",
        },
        "last_id": last_id,
        "limit": 1000,
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def get_offer_ids(client_id, seller_token):
    """Получить артикулы товаров магазина озон.
    
    Args:
        client_id (str): id клиента для аутентифицации API Ozon.
        seller_token (str): токен продавца для аутентификации API Ozon.

    Returns:
        list: список артикулов

    Examples:
        >>> get_offer_ids(client_id, seller_token)
        ["78910", ...]

    """
    last_id = ""
    product_list = []
    while True:
        some_prod = get_product_list(last_id, client_id, seller_token)
        product_list.extend(some_prod.get("items"))
        total = some_prod.get("total")
        last_id = some_prod.get("last_id")
        if total == len(product_list):
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer_id"))
    return offer_ids


def update_price(prices: list, client_id, seller_token):
    """Обновить цены товаров.
    
    Args:
        prices (list): спикок цен на товары
        client_id (str): id клиента для аутентифицации API Ozon.
        seller_token (str): токен продавца для аутентификации API Ozon.
    
    Returns:
        dict: словарь с обновленными ценами на Ozon.

    Examples:
        >>> update_price(prices, client_id, seller_token)
        {'result': 'success', 'updated_items': 1}
        
    """
    url = "https://api-seller.ozon.ru/v1/product/import/prices"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"prices": prices}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def update_stocks(stocks: list, client_id, seller_token):
    """Обновить остатки.
    
    Args:
        prices (list): спикок цен на товары
        client_id (str): id клиента для аутентифицации API Ozon.
        seller_token (str): токен продавца для аутентификации API Ozon.
    
    Returns:
        dict: словарь с обновленными данными об остатках товара на Ozon.

    Examples:
        >>> update_stocks(stocks: list, client_id, seller_token)
        {'result': 'success', 'updated_items': 1}

    """
    url = "https://api-seller.ozon.ru/v1/product/import/stocks"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"stocks": stocks}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def download_stock():
    """Скачать файл ostatki с сайта casio.
    
    Returns:
        dict: словарь с данными об остатках часов Casio на складе
    
    """
    # Скачать остатки с сайта
    casio_url = "https://timeworld.ru/upload/files/ostatki.zip"
    session = requests.Session()
    response = session.get(casio_url)
    response.raise_for_status()
    with response, zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(".")
    # Создаем список остатков часов:
    excel_file = "ostatki.xls"
    watch_remnants = pd.read_excel(
        io=excel_file,
        na_values=None,
        keep_default_na=False,
        header=17,
    ).to_dict(orient="records")
    os.remove("./ostatki.xls")  # Удалить файл
    return watch_remnants


def create_stocks(watch_remnants, offer_ids):
    """Создать словарь с данными об остатках на складе.

    Args:
        watch_remnants (dict): словарь с данными об остатках часов 
            Casio на складе
        offer_ids: список артикулов

    Returns:
        dict: обновленный словарь с данными об остатках 

    """
    # Уберем то, что не загружено в seller
    stocks = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append({"offer_id": str(watch.get("Код")), "stock": stock})
            offer_ids.remove(str(watch.get("Код")))
    # Добавим недостающее из загруженного:
    for offer_id in offer_ids:
        stocks.append({"offer_id": offer_id, "stock": 0})
    return stocks


def create_prices(watch_remnants, offer_ids):
    """Сформировать цены.

    Args:
        watch_remnants (dict): словарь с данными об остатках часов
            Casio на складе
        offer_ids: список артикулов

    Returns:
        list: список словарей с ценами на часы 

    """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "auto_action_enabled": "UNKNOWN",
                "currency_code": "RUB",
                "offer_id": str(watch.get("Код")),
                "old_price": "0",
                "price": price_conversion(watch.get("Цена")),
            }
            prices.append(price)
    return prices


def price_conversion(price: str) -> str:
    """Преобразовать цену. Пример: 5'990.00 руб. -> 5990.
    
    Args:
        price(str): цена в формате сроки для преобразования

    Returns:
        str: преобразованная цена без символов

    Examples:
        >>> price_conversion("5'990.00 руб.")
        "5990"
           
    """
    return re.sub("[^0-9]", "", price.split(".")[0])


def divide(lst: list, n: int):
    """Разделить список lst на части по n элементов.
    
    Args:
        lst (list): список
        n (int): кол-во элементов

    Yields:
        lst (list): списки с элементами

    Examples:
        >>> divide(list, 2):
        >>> [1, 2]

    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def upload_prices(watch_remnants, client_id, seller_token):
    """Загрузить словарь с ценами.

    Args:
        watch_remnants (dict): словарь с данными об остатках часов 
            Casio на складе 
        client_id (str): id клиента для аутентифицации API Ozon.
        seller_token (str): токен продавца для аутентификации API Ozon.

    Returns:
        dict: словарь с ценами    

    """
    offer_ids = get_offer_ids(client_id, seller_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_price in list(divide(prices, 1000)):
        update_price(some_price, client_id, seller_token)
    return prices


async def upload_stocks(watch_remnants, client_id, seller_token):
    """Загрузить словарь с ценами.

    Args:
        watch_remnants (dict): словарь с данными об остатках часов
            Casio на складе 
        client_id (str): id клиента для аутентифицации API Ozon.
        seller_token (str): токен продавца для аутентификации API Ozon.

    Returns:
        dict: словарь с остатками    

    """
    offer_ids = get_offer_ids(client_id, seller_token)
    stocks = create_stocks(watch_remnants, offer_ids)
    for some_stock in list(divide(stocks, 100)):
        update_stocks(some_stock, client_id, seller_token)
    not_empty = list(filter(lambda stock: (stock.get("stock") != 0), stocks))
    return not_empty, stocks


def main():
    env = Env()
    seller_token = env.str("SELLER_TOKEN")
    client_id = env.str("CLIENT_ID")
    try:
        offer_ids = get_offer_ids(client_id, seller_token)
        watch_remnants = download_stock()
        # Обновить остатки
        stocks = create_stocks(watch_remnants, offer_ids)
        for some_stock in list(divide(stocks, 100)):
            update_stocks(some_stock, client_id, seller_token)
        # Поменять цены
        prices = create_prices(watch_remnants, offer_ids)
        for some_price in list(divide(prices, 900)):
            update_price(some_price, client_id, seller_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
