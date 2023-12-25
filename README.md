# seller.py

Скрипт разработан для проведения инвентаризации и управления ценами на маркетплейсе [Ozon](https://https://www.ozon.ru/). 
Он составляет списки оставшихся часов и обновляет на них цены на [Ozon](https://https://www.ozon.ru/), беря для этого данные с сайта [Timeworld](https://timeworld.ru/). 
Для запуска необходимо указать в .env файле следующие переменные окружения для токенов: SELLER_TOKEN, CLIENT_ID, которые можно получить через [API Ozon](https://docs.ozon.ru/api/seller/).

# market.py

Скрипт разработан для проведения инвентаризации и управления ценами на маркетплейсе [Яндекс Маркет](https://market.yandex.ru/). 
Он составляет списки оставшихся часов и обновляет на них цены на [Яндекс Маркет](https://market.yandex.ru/), беря для этого данные с сайта [Timeworld](https://timeworld.ru/).
Для запуска необходимо указать в .env файле следующие переменные окружения для токенов: MARKET_TOKEN, FBS_ID, DBS_ID, WAREHOUSE_FBS_ID, WAREHOUSE_DBS_ID которые можно получить через [API Яндекс Маркет](https://yandex.ru/dev/market/partner-api/doc/ru/).