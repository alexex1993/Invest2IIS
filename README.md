# Invest2IIS

## Описание
Invest2IIS — это инструмент предназначенный для мониторинга ваших инвестиций в собственном телеграм боте. 


## Возможности
- Запрос состояния портфеля
- Уведомлерие при изменении доступных денежных средств


## Установка
0. Сделайте телеграм бота и CHAT_ID для приватного общения с ботом
1. Получите API-токен в веб-версии [Тинькоф Инвестиции Настройки](https://www.tbank.ru/invest/settings/) -> Токены T‑Bank Invest API -> Создать токен (достаточно токена на чтение)
2. Получите номер счета (подробнее в главе ниже)
3. Клонируйте репозиторий и установите пакет `pip install .` находясь внутри репозитория
4. В корень проекта добавьте `.env`-файл с переменными
    ```
    TOKEN = "xxxxxx:yyyyyyy"  # Получить бота в боте @BotFather
    CHAT_ID = 12345 # ID чата в телеграм - ваш уникальный ID переписки
    TINKOFF_TOKEN = "t.xxxxxYYYY"  # 
    TINKOFF_ACCOUNT_ID = "12345678"       # ID счета в Тинькофф
    ```
5. Запустите пакет `python3 main.py`


## Получения номера счета 
```
from tinkoff.invest import Client

TINKOFF_TOKEN = "t.xxxxxYYYY" 

with Client(TINKOFF_TOKEN) as client:
    # Получение списка счетов
    accounts = client.users.get_accounts()
    for account in accounts.accounts:
        print(f"ID счета: {account.id}, Тип: {account.type}, Статус: {account.status}, Название: {account.name}")
```

## Пример бота (запросы и уведомления)

<img width="990" height="1280" alt="image" src="https://github.com/user-attachments/assets/79d23528-2fb7-4ac1-98c0-97d12efb3daf" />
