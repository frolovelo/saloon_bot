from datetime import datetime, timedelta
from time import time

# from config import *
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from concurrent.futures import ThreadPoolExecutor

# https://www.youtube.com/watch?v=82DGz7IxW7c -настройка подключения
# gspread.exceptions.APIError: {'code': 500, 'message': 'Internal error encountered.', 'status': 'INTERNAL'}

myscope = ["https://www.googleapis.com/auth/spreadsheets",
           "https://www.googleapis.com/auth/drive"]

mycreds = ServiceAccountCredentials.from_json_keyfile_name('beautysaloon-392108-e0e38d544ad6.json', myscope)
myclient = gspread.authorize(mycreds)
sh = myclient.open('SaloonSheet')


def time_score(func):
    """Декоратор для поиска слабых мест"""

    def wrapper(*args, **kwargs):
        start = time()
        res = func(*args, **kwargs)
        print(f"---{func.__name__} = %s seconds ---" % round(time() - start, 2))
        return res

    return wrapper


class GoogleSheets:
    def __init__(self, client_id):
        self.client_id = client_id
        self.dct_master_service = None
        self.lst_currant_date = None
        self.dct_currant_time = None

        self.name_service = None
        self.name_master = None
        self.date_record = None
        self.time_record = None
        self.ignor_worksheets = ['Шаблон', 'Работники']

    def __str__(self):
        return f'{self.client_id, self.name_service, self.name_master, self.date_record, self.time_record}'

    def get_services(self) -> dict:
        """
        Названия актуальных услуг и имена мастеров
        return dict{name_service: name_master}
        """
        dct = {}
        ws = sh.worksheet('Работники')
        for i in ws.get_all_records():
            dct[i['Услуга'].strip()] = dct.get(i['Услуга'].strip(), [])
            dct[i['Услуга'].strip()].append(i['Мастер'].strip())
        self.dct_master_service = dct
        return dct

    def get_all_days(self) -> list:
        """ВСЕ доступные дни для записи на определенную услугу"""

        def actual_date(sheet_name, count_days=7) -> bool:
            """
            Проверяет по названию листа актуальные даты для записи на ближайшие 7 дней,
            а также наличие свободного времени
            return: bool
            """
            if sheet_name.title not in self.ignor_worksheets:
                if datetime.now().date() <= \
                        datetime.strptime(sheet_name.title, '%d.%m.%y').date() <= \
                        (datetime.now().date() + timedelta(days=count_days)):
                    val = sheet_name.get_all_records()
                    for dct in val:
                        if self.name_master is not None:
                            if dct['Мастер'].strip() == self.name_master:
                                if dct['Услуга'].strip() == self.name_service:
                                    for k, v in dct.items():
                                        if str(v).strip() == '':
                                            return sheet_name.title.strip()
                        elif dct['Услуга'].strip() == self.name_service:
                            for k, v in dct.items():
                                if str(v).strip() == '':
                                    return sheet_name.title.strip()
            return False

        with ThreadPoolExecutor(8) as executor:  # Без потоков - время 2.5 сек
            res = executor.map(actual_date, sh.worksheets())
            res = list(filter(lambda x: type(x) is str, res))

        return res

    def get_free_time(self) -> dict:
        """Функция выгружает ВСЕ СВОБОДНОЕ ВРЕМЯ для определенной ДАТЫ"""
        dct = {}
        try:
            all_val = sh.worksheet(self.date_record).get_all_records()
        except gspread.exceptions.WorksheetNotFound as not_found:
            print(not_found, '- Дата занята/не найдена')
            return {}

        for i in all_val:
            if self.name_master is None:
                if i['Услуга'].strip() == self.name_service:
                    for k, v in i.items():
                        if str(v).strip() == '':
                            dct['Время'] = dct.get('Время', [])
                            dct['Время'].append(k.strip())
            else:
                if i['Услуга'].strip() == self.name_service and i['Мастер'].strip() == self.name_master:
                    for k, v in i.items():
                        if str(v).strip() == '':
                            dct['Время'] = dct.get('Время', [])
                            dct['Время'].append(k.strip())

        if len(dct) > 0:
            dct['Время'] = sorted(list(set(dct['Время'])))
        self.dct_currant_time = dct
        return dct

    def set_time(self, id_client) -> bool:
        """Производит запись на услугу - заносит в таблицу"""
        try:
            all_val = sh.worksheet(self.date_record).get_all_records()
        except gspread.exceptions.WorksheetNotFound as not_found:
            print(not_found, '- Дата занята/не найдена')
            return False

        row_num = 1
        for i in all_val:
            row_num += 1
            col_num = 0
            if self.name_master is None:
                if i['Услуга'].strip() == self.name_service:
                    for key_time, val_use in i.items():
                        col_num += 1
                        if key_time.strip() == self.time_record and val_use.strip() == '':
                            self.name_master = i['Мастер'].strip()
                            sh.worksheet(self.date_record).update_cell(row_num, col_num, f'{id_client}')
                            return True
            else:
                if i['Услуга'].strip() == self.name_service and i['Мастер'].strip() == self.name_master:
                    for key_time, val_use in i.items():
                        col_num += 1
                        if key_time.strip() == self.time_record and val_use.strip() == '':
                            sh.worksheet(self.date_record).update_cell(row_num, col_num, f'{id_client}')
                            return True
        return False
