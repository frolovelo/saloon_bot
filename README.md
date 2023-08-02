# saloon_bot

**saloon_bot** - telegram bot для записи в салон красоты с использованием Google Sheets

![Static Badge](https://img.shields.io/badge/python-3.11-blue)
![Static Badge](https://img.shields.io/badge/TelegramBotAPI-4.12.0-blue)
![Static Badge](https://img.shields.io/badge/gspread-5.10.0-blue)

![Static Badge](https://img.shields.io/badge/pylint_score-9%2C5-green)

<img style="height:450px;" src="https://i.ibb.co/gFCT55h/IMG-1551-1.gif" alt="IMG-1551-1">

------

## Описание
Данный проект представляет собой телеграмм бота, который позволяет пользователям записываться в салон красоты. 
Бот использует Google Sheets для хранения информации о клиентах и их записях.

**Пример таблицы:** https://docs.google.com/spreadsheets/d/1VmucIj0jhJcIDv3tkfpXtlLoDRh4Zhoa8DuCTzOuhuQ/edit?usp=sharing


**telebot documentation:** [https://github.com/eternnoir/pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI)

**gspread documentation:** [https://docs.gspread.org/en/v5.7.2/](https://docs.gspread.org/en/v5.7.2/)


## Установка

```
git clone https://github.com/frolovelo/saloon_bot.git
```
## Зависимости

**Windows**

```bash
pip install -r requirements.txt
```

**macOS/Linux:**

```bash
pip3 install -r requirements.txt
```

**Активация виртуального окружения (Windows):**

```bash
\venv\Scripts\activate
```

**Активация виртуального окружения (macOS/Linux):**

```bash
source venv/bin/activate
```

## Использование

1. Создайте config.py с содержимым:
```python
TOKEN = "YOUR_BOT_TOKEN"
```
2. Получите json ключ от Google Sheets (как получить: https://www.youtube.com/watch?v=82DGz7IxW7c)

Структура ключа:
```json
{
  "type": "service_account",
  "project_id": "beautysaloon",
  "private_key_id": "fGEFEfeEWR343253235",
  "private_key": "-----BEGIN PRIVATE KEY-----\n",
  "client_email": "my-account-service@beautysaloon.iam.gserviceaccount.com",
  "client_id": "10275785785778592",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/my-account-service",
  "universe_domain": "googleapis.com"
}
```
3. Замените название ключа в [google_sheet.py](google_sheet.py)
```python
# Название файла json ключа
creds = Credentials.from_service_account_file('YOUR_NAME_KEY.json', scopes=myscope)
client_main = gspread.Client(creds)
```

4. Для тестового запуска рекомендуется скопировать данные из ***примера таблицы:*** https://docs.google.com/spreadsheets/d/1VmucIj0jhJcIDv3tkfpXtlLoDRh4Zhoa8DuCTzOuhuQ/edit?usp=sharing


5. Сменить данные на свои в [google_sheet.py](google_sheet.py):
```python
# Название таблицы
sh = client_main.open('YOUR_TABLE_NAME')
# Страницы таблицы, которые должны игнорироваться во избежание проблем
IGNOR_WORKSHEETS = ['Работники']
# Страница таблицы, на которой перечислены все действующие работники и услуги
NAME_SHEET_WORKERS = 'Работники'
# Названия основных колонок(очередность важна!)
NAME_COL_SERVICE = 'Услуга'
NAME_COL_MASTER = 'Мастер'
```
* ``` sh = client_main.open('YOUR_TABLE_NAME')``` - имя вашей таблицы
* ```IGNOR_WORKSHEETS``` - имена листов, структура которых отличается от листов для записи
* ```NAME_SHEET_WORKERS``` - имя листа со всеми услугами и работниками
* ``` NAME_COL_SERVICE``` и ```NAME_COL_MASTER``` - названия колонок в вашей таблице

#### Примечание:
1. Лист ```NAME_SHEET_WORKERS``` требуется для выдачи клиентам списка мастеров и услуг;
2. Листы для записи должны иметь определенный формат имени: 'дд.мм.гг';
3. В листах для записи следует соблюдать лишь первые две колонки: 'Услуга', 'Мастер', 
время для записи вы можете ставить на своё усмотрение.

## Структура проекта

* [config.py]() - токен бота
* [main.py](main.py) - telegram бот 
* [google_sheet.py](google_sheet.py) - работа с Google Sheet
* [clear_dict.py](clear_dict.py) - хранение информации о пользователях и периодичная отчистка
* [keyboards.py](keyboards.py) - клавиатуры и кнопки Telebot
* [telebot_calendar.py](telebot_calendar.py) - клавиатура в виде календаря
* [requirements.txt](requirements.txt) - библиотеки


## Референсы

  [purgy](https://github.com/purgy/telebot-calendar) - Telebot календарь
