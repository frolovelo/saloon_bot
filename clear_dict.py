"""
Хранение информации о пользователе и отчистка
"""
from datetime import datetime, timedelta
from threading import Lock, Thread
from time import sleep

# хранит объекты GoogleSheet по ключу id
CLIENT_DICT = {}
# хранит название календаря по ключу id
CALENDAR_DICT = {}
# хранит время создания объекта GoogleSheet
TIMER_DICT = {}
# Lock для синхронизации доступа к словарям
lock = Lock()


def clear_unused_info(chat_id) -> None:
    """
        Отчищает данные из GoogleSheet,
        не затрагивает кэшированные данные

        :param chat_id: id пользователя
        """
    if CLIENT_DICT.get(chat_id):
        client = CLIENT_DICT[chat_id]
        client.lst_currant_date = None
        client.dct_currant_time = None
        # client.lst_records = None
        client.name_service = None
        client.name_master = None
        client.date_record = None
        client.time_record = None

    if CALENDAR_DICT.get(chat_id):
        del CALENDAR_DICT[chat_id]


def clear_all_dict(chat_id) -> None:
    """
    Отчищает все словари по chat_id

    :param chat_id: id пользователя
    """
    if CLIENT_DICT.get(chat_id):
        del CLIENT_DICT[chat_id]
    if CALENDAR_DICT.get(chat_id):
        del CALENDAR_DICT[chat_id]
    if TIMER_DICT.get(chat_id):
        del TIMER_DICT[chat_id]


def clear_client_dict(period_clear_minutes=60) -> None:
    """
    Отчищает все неактивные элементы словарей

    :param period_clear_minutes: периодичность отчистки в минутах
    """
    while True:
        sleep(period_clear_minutes * 60)
        at_now = datetime.now()
        lst_to_del = []
        with lock:
            for key, val in TIMER_DICT.items():
                if val + timedelta(minutes=period_clear_minutes) >= at_now:
                    lst_to_del.append(key)
            for chat_id in lst_to_del:
                clear_all_dict(chat_id)


clear_thread = Thread(target=clear_client_dict)
clear_thread.daemon = True
clear_thread.start()
