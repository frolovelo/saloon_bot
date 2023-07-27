from datetime import datetime, timedelta
from threading import Lock, Thread
from time import sleep

# хранит объекты GoogleSheet по ключу id
client_dict = {}
# хранит название календаря по ключу id
calendar_dict = {}
# хранит время создания объекта GoogleSheet
timer_dict = {}
# Lock для синхронизации доступа к словарям
lock = Lock()


def clear_unused_info(chat_id):
    """
        Отчищает данные из GoogleSheet,
        не затрагивает кэшированные данные

        :param chat_id: id пользователя
        """
    if client_dict.get(chat_id):
        client = client_dict[chat_id]
        client.lst_currant_date = None
        client.dct_currant_time = None
        # client.lst_records = None

        client.name_service = None
        client.name_master = None
        client.date_record = None
        client.time_record = None
        # print(client_dict[chat_id])
    if calendar_dict.get(chat_id):
        del calendar_dict[chat_id]


def clear_all_dict(chat_id):
    """
    Отчищает все словари по chat_id

    :param chat_id: id пользователя
    """

    # print(client_dict)
    # print(calendar_dict)
    # print(timer_dict)

    if client_dict.get(chat_id):
        del client_dict[chat_id]
    if calendar_dict.get(chat_id):
        del calendar_dict[chat_id]
    if timer_dict.get(chat_id):
        del timer_dict[chat_id]

    # print(client_dict)
    # print(calendar_dict)
    # print(timer_dict)


def clear_client_dict(period_clear_minutes=60):
    """
    Отчищает все неактивные элементы словаря

    :param period_clear_minutes: периодичность отчистки в минутах
    """
    while True:
        print('ОТЧИСТКА')
        sleep(period_clear_minutes * 60)
        at_now = datetime.now()
        lst_to_del = []
        with lock:
            for k, v in timer_dict.items():
                if v + timedelta(minutes=period_clear_minutes) >= at_now:
                    lst_to_del.append(k)
            for chat_id in lst_to_del:
                clear_all_dict(chat_id)


clear_thread = Thread(target=clear_client_dict)
clear_thread.daemon = True
clear_thread.start()
