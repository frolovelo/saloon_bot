"""
Взаимодействие с Telegram
"""
from datetime import datetime
from telebot import types, TeleBot
from telebot.types import CallbackQuery, ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN
import telebot_calendar
from google_sheet import GoogleSheets, get_cache_services
from keyboards import create_markup_menu, button_to_menu
import clear_dict

bot = TeleBot(TOKEN)

CLIENT_PHONE = {467168798: '+79522600066', 288041146: '+79215528067'}  # sql сделать


def get_client_id(client_id, client_username) -> str:
    """Создаёт строку записи пользователя

    :param client_id: id чата/пользователя
    :param client_username: username пользователя
    :return: 'id: id @username tel: phone'"""
    id_client = f"id: {str(client_id)}\n@{str(client_username)}\n"
    if CLIENT_PHONE.get(client_id, None) is not None:
        if CLIENT_PHONE[client_id] != '':
            id_client += 'tel: ' + CLIENT_PHONE[client_id]
        else:
            id_client += 'tel: None'
    return id_client


def create_client(chat_id) -> GoogleSheets:
    """
    Создаёт объект GoogleSheet по chat_id

    :chat_id: id чата/клиента
    """
    if clear_dict.CLIENT_DICT.get(chat_id):
        return clear_dict.CLIENT_DICT[chat_id]
    client = GoogleSheets(chat_id)
    clear_dict.CLIENT_DICT[chat_id] = client
    clear_dict.TIMER_DICT[chat_id] = datetime.now()
    return client


@bot.message_handler(commands=['start'])
def check_phone_number(message):
    """Запрашивает номер телефона у пользователя единожды"""

    if CLIENT_PHONE.get(message.chat.id, None) is None:
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        button_phone = types.KeyboardButton(text="Отправить телефон 📞",
                                            request_contact=True)
        markup.add(button_phone)
        bot.send_message(message.chat.id, 'Для записи на услуги требуется номер телефона.',
                         reply_markup=markup)

        @bot.message_handler(content_types=['contact'])
        def contact(message_contact):
            """Получает объект <contact> -> вызывает функцию стартового меню"""
            if message_contact.contact is not None:
                CLIENT_PHONE[message_contact.chat.id] = message_contact.contact.phone_number
                bot.send_message(message_contact.chat.id,
                                 text='Спасибо за доверие!',
                                 reply_markup=ReplyKeyboardRemove())
                menu(message_contact)
    else:
        menu(message)


@bot.message_handler(content_types=['text'])
def any_word_before_number(message_any):
    """Обработчик любых текстовых сообщений"""
    bot.send_message(message_any.chat.id,
                     text='Пользоваться ботом возможно только при наличии номера телефона!\n'
                          'Взаимодействие с ботом происходит кнопками.')


def menu(message):
    """Главное меню"""
    clear_dict.clear_unused_info(message.chat.id)
    bot.send_message(message.chat.id, "Выберите пункт меню:",
                     reply_markup=create_markup_menu())


@bot.callback_query_handler(lambda call: call.data == 'CANCEL_RECORD')
def cancel_record(call):
    """
    InlineKeyboardMarkup - Выбор записи для отмены
    """
    client = create_client(call.message.chat.id)
    client_id = get_client_id(call.message.chat.id, call.from_user.username)
    records = client.get_record(client_id)
    if len(records) != 0:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            *[InlineKeyboardButton(text=' - '.join(x[:3]),
                                   callback_data=f'CANCEL {ind}'
                                   ) for ind, x in enumerate(records)])
        markup.add(*button_to_menu(return_callback=None,
                                   menu_text='В главное меню'))
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text='Какую запись вы хотите отменить?🙈',
                              reply_markup=markup
                              )
    else:
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text='Отменять пока нечего 🤷'
                              )
        check_phone_number(call.message)


@bot.callback_query_handler(lambda call: call.data.startswith('CANCEL'))
def approve_cancel(call):
    """
    Обработка inline callback запросов
    Подтверждение отмены записи
    """
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(*[InlineKeyboardButton(text='Подтверждаю',
                                      callback_data='APPROVE' + call.data),
                 InlineKeyboardButton(text='В главное меню',
                                      callback_data='MENU')])
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text='Точно отменить?',
                          reply_markup=markup)


@bot.callback_query_handler(lambda call: call.data.startswith('APPROVE'))
def set_cancel(call):
    """
    Обработка inline callback запросов
    Отмена записи
    """
    client = clear_dict.CLIENT_DICT.get(call.from_user.id)
    if client:
        client_info = client.lst_records[int(call.data.split()[1])]
        client.date_record, client.time_record, client.name_service, client.name_master = client_info
        client_id = get_client_id(call.message.chat.id, call.from_user.username)
        if client.set_time('', client_id):
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text='Запись отменена!')
        else:
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text='Не смог отменить запись.')
        check_phone_number(call.message)
    else:
        go_to_menu(call)


@bot.callback_query_handler(lambda call: call.data == 'MY_RECORD')
def show_record(call):
    """Показывает все записи клиента"""
    client = create_client(call.message.chat.id)

    client_id = get_client_id(call.message.chat.id, call.from_user.username)
    records = client.get_record(client_id)
    rec = ''
    if len(records) != 0:
        rec += 'Ближайшие записи:\n\n'
        for i in sorted(records, key=lambda x: (x[0], x[1], x[2])):
            rec += '🪷' + ' - '.join(i) + '\n'
    else:
        rec = 'Актуальных записей не найдено 🔍'
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=rec
                          )
    check_phone_number(call.message)


@bot.callback_query_handler(lambda call: call.data == 'RECORD')
def choice_service(call):
    """
    InlineKeyboardMarkup
    Выбор услуги для записи
    """
    create_client(call.message.chat.id)

    all_serv = get_cache_services()
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(*[InlineKeyboardButton(text=x,
                                      callback_data='SERVICE' + x
                                      ) for x in all_serv.keys()])
    markup.add(*button_to_menu(None))
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text="Выбери услугу:",
                          reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('SERVICE'))
def choice_master(call):
    """
    Обработка inline callback запросов
    Выбор мастера
    """
    client = clear_dict.CLIENT_DICT.get(call.from_user.id)
    if client:
        client.name_service = call.data[len('SERVICE'):]
        dct = get_cache_services()
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(*[InlineKeyboardButton(text=x,
                                          callback_data='MASTER' + x
                                          ) for x in dct[client.name_service]])
        markup.add(InlineKeyboardButton(text='Любой мастер',
                                        callback_data='MASTER' + 'ЛЮБОЙ'))
        markup.add(*button_to_menu('RECORD'))
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Выбери Мастера:",
                              reply_markup=markup)
    else:
        go_to_menu(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith('MASTER'))
def choice_date(call):
    """
    Обработка inline callback запросов
    Выбор даты
    """
    client = clear_dict.CLIENT_DICT.get(call.from_user.id)
    if client:
        if call.data[len('MASTER'):] != 'ЛЮБОЙ':
            client.name_master = call.data[len('MASTER'):]
        else:
            client.name_master = None
        lst = client.get_all_days()
        lst = list(map(lambda x: datetime.strptime(x, '%d.%m.%y').date(), lst))
        if len(lst) == 0:
            service = client.name_service if client.name_service else 'ЛЮБОЙ'
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(*button_to_menu('SERVICE' + service))
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="Для выбранного мастера нет доступных дат!\n"
                                       "Попробуй другого мастера😉",
                                  reply_markup=markup)
        else:
            client.lst_currant_date = lst
            clear_dict.CALENDAR_DICT[call.message.chat.id] = str(call.message.chat.id)
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=call.message.message_id,
                                  text='Выбери доступную дату:\n ✅ - есть свободное время',
                                  reply_markup=telebot_calendar.create_calendar(
                                      name='CALENDAR' + clear_dict.CALENDAR_DICT[call.message.chat.id],
                                      lst_current_date=lst)
                                  )
    else:
        go_to_menu(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith('CALENDAR'))
def choice_time(call: CallbackQuery):
    """
    Обработка inline callback запросов
    Выбор времени
    """
    client = clear_dict.CLIENT_DICT.get(call.from_user.id)
    if client:
        lst = client.lst_currant_date
        # At this point, we are sure that this calendar is ours. So we cut the line by the separator of our calendar
        name, action, year, month, day = call.data.split(':')
        # Processing the calendar. Get either the date or None if the buttons are of a different type
        telebot_calendar.calendar_query_handler(
            bot=bot, call=call, name=name, action=action, year=year, month=month, day=day,
            lst_currant_date=lst
        )

        if action == "DAY":
            client.date_record = datetime(int(year), int(month), int(day)).strftime('%d.%m.%y')
            lst_times = client.get_free_time()
            client.dct_currant_time = lst_times

            markup = InlineKeyboardMarkup(row_width=3)
            markup.add(*[InlineKeyboardButton(text=x,
                                              callback_data='TIME' + x
                                              ) for x in lst_times])
            master = 'MASTER' + (client.name_master if client.name_master else 'ЛЮБОЙ')
            markup.add(*button_to_menu(master))
            text = "Выберите время:" if len(lst_times) != 0 else "Для выбранного даты нет доступного времени!\n" \
                                                                 "Попробуй другую дату😉"
            bot.delete_message(chat_id=call.message.chat.id,
                               message_id=call.message.message_id)
            bot.send_message(
                chat_id=call.from_user.id,
                text=text,
                reply_markup=markup
            )

        elif action == "MENU":
            go_to_menu(call)
        elif action == "RETURN":
            call.data = 'SERVICE' + client.name_service
            choice_master(call)
    else:
        go_to_menu(call)


@bot.callback_query_handler(lambda call: call.data.startswith('TIME'))
def approve_record(call):
    """
    Обработка inline callback запросов
    Подтверждение отмены записи
    """
    client = clear_dict.CLIENT_DICT.get(call.from_user.id)

    if client:
        client.time_record = call.data[len('TIME'):]
        id_calendar = clear_dict.CALENDAR_DICT[call.from_user.id]
        date_string = client.date_record
        date_object = datetime.strptime(date_string, '%d.%m.%y')
        formatted_date = date_object.strftime('%Y:') + str(date_object.month) + ':' + str(date_object.day)
        name_calendar = 'CALENDAR' + id_calendar + ':DAY:' + formatted_date

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton(text='Подтверждаю',
                                        callback_data='APP_REC'))
        markup.add(*button_to_menu(name_calendar))
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=f'Проверьте данные записи:\n\n'
                                   f'🛎️ Услуга: {client.name_service}\n'
                                   f'👤 Мастер: {client.name_master if client.name_master else "Любой"}\n'
                                   f'📅 Дата: {client.date_record}\n'
                                   f'🕓 Время: {client.time_record}',
                              reply_markup=markup)
    else:
        go_to_menu(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith('APP_REC'))
def set_time(call):
    """
    Обработка inline callback запросов
    Выбор времени
    """
    client = clear_dict.CLIENT_DICT.get(call.from_user.id)
    if client:
        id_client = get_client_id(call.message.chat.id, call.from_user.username)
        if client.set_time(id_client):
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=call.message.message_id,
                                  text=f'Успешно записал вас!\n\n'
                                       f'🛎️ Услуга: {client.name_service}\n'
                                       f'👤 Мастер: {client.name_master if client.name_master else "Любой"}\n'
                                       f'📅 Дата: {client.date_record}\n'
                                       f'🕓 Время: {client.time_record}',
                                  )
            check_phone_number(call.message)
        else:
            bot.send_message(call.message.chat.id, 'Время кто-то забронировал...\nПопробуй другое!')
    else:
        go_to_menu(call)


@bot.callback_query_handler(func=lambda call: call.data == 'MENU')
def go_to_menu(call):
    """Возвращает в главное меню"""
    bot.delete_message(chat_id=call.message.chat.id,
                       message_id=call.message.message_id)
    check_phone_number(call.message)


bot.infinity_polling()
