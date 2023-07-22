from datetime import datetime
from config import TOKEN
from google_sheet import GoogleSheets
from telebot import types, TeleBot
from telebot.types import CallbackQuery, ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import telebot_calendar
from keyboards import create_markup_menu
from clear_dict import *

bot = TeleBot(TOKEN)

client_phone_number = {467168798: '+79522600066', 288041146: '+79215528067'}  # sql сделать


def get_client_id(client_id, client_username):
    """Создаёт строку формата id, username, phone"""
    id_client = f"id: {str(client_id)}\n@{str(client_username)}\n"
    if client_phone_number.get(client_id, None) is not None:
        if client_phone_number[client_id] != '':
            id_client += 'tel: ' + client_phone_number[client_id]
        else:
            id_client += 'tel: None'
    return id_client


def create_client(chat_id):
    """Создаёт объект GoogleSheet по chat_id"""
    client = GoogleSheets(chat_id)
    client_dict[chat_id] = client
    timer_dict[chat_id] = datetime.now()
    return client


@bot.message_handler(commands=['start'])
def check_phone_number(message):
    """Запрашивает номер телефона у пользователя единожды"""
    clear_all_dict(message.chat.id)

    if client_phone_number.get(message.chat.id, None) is None:
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
                client_phone_number[message.chat.id] = message_contact.contact.phone_number
                bot.send_message(message.chat.id, text='Спасибо за доверие!', reply_markup=ReplyKeyboardRemove())
                menu(message)
    else:
        menu(message)


@bot.message_handler(content_types=['text'])
def any_word_before_number(message_any):
    """Обработчик любых текстовых сообщений"""
    bot.send_message(message_any.chat.id, 'Пользоваться ботом возможно только при наличии номера телефона!\n'
                                          'Взаимодействие с ботом происходит кнопками.')


@bot.message_handler(func=lambda message: message.text == 'MENU')
def menu(message):
    """Главное меню"""
    bot.send_message(message.chat.id, "Выберите пункт меню:", reply_markup=create_markup_menu())


@bot.callback_query_handler(lambda call: call.data == 'CANCEL_RECORD')
def cancel_record(call):
    """
    InlineKeyboardMarkup - Выбор записи для отмены
    """
    client = create_client(call.message.chat.id)
    client_id = get_client_id(call.message.chat.id, call.from_user.username)
    records = client.get_record(client_id)
    if len(records) != 0:
        client.lst_records = records
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            *[InlineKeyboardButton(text=' - '.join(x[:3]), callback_data=f'CANCEL {ind}') for ind, x in
              enumerate(records)])
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
    markup.add(*[InlineKeyboardButton(text='Подтверждаю', callback_data='APPROVE' + call.data),
                 InlineKeyboardButton(text='В главное меню', callback_data='APPROVE_MENU')])
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
    if 'MENU' not in call.data:
        client = client_dict.get(call.from_user.id)
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
        else:
            bot.delete_message(chat_id=call.message.chat.id,
                               message_id=call.message.message_id)
    else:
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)

    check_phone_number(call.message)


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
    client = create_client(call.message.chat.id)

    all_serv = client.get_services()
    client.dct_master_service = all_serv
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(*[InlineKeyboardButton(text=x, callback_data='SERVICE' + x) for x in all_serv.keys()])
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
    client = client_dict.get(call.from_user.id)
    if client:
        name_ser = client.name_service = call.data.lstrip('SERVICE')
        dct = client.dct_master_service
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(*[InlineKeyboardButton(text=x, callback_data='MASTER' + x) for x in dct[name_ser]])
        markup.add(InlineKeyboardButton(text='Любой мастер', callback_data='MASTER' + 'ЛЮБОЙ'))

        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Выбери Мастера:",
                              reply_markup=markup)
    else:
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        check_phone_number(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith('MASTER'))
def choice_date(call):
    """
    Обработка inline callback запросов
    Выбор даты
    """
    client = client_dict.get(call.from_user.id)
    if client:
        if call.data.lstrip('MASTER') != 'ЛЮБОЙ':
            client.name_master = call.data.lstrip('MASTER')
        lst = client.get_all_days()
        lst = list(map(lambda x: datetime.strptime(x, '%d.%m.%y').date(), lst))
        client.lst_currant_date = lst
        calendar_dict[call.message.chat.id] = str(call.message.chat.id)
        bot.edit_message_text(chat_id=call.from_user.id,
                              message_id=call.message.message_id,
                              text='Выбери доступную дату:\n ✅ - есть свободное время',
                              reply_markup=telebot_calendar.create_calendar(
                                  name='CALENDAR' + calendar_dict[call.message.chat.id], lst_current_date=lst)
                              )
    else:
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        check_phone_number(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith('CALENDAR'))
def choice_time(call: CallbackQuery):
    """
    Обработка inline callback запросов
    Выбор времени
    """
    client = client_dict.get(call.from_user.id)
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

            markup = InlineKeyboardMarkup(row_width=4)
            markup.add(*[InlineKeyboardButton(text=x, callback_data='TIME' + x) for x in lst_times])

            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            bot.send_message(
                chat_id=call.from_user.id,
                text="Выбери время:",
                reply_markup=markup
            )

        elif action == "CANCEL":
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            # print(f"{calendar_dict[call.message.chat.id]}: Отмена")
            check_phone_number(call.message)
    else:
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        check_phone_number(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith('TIME'))
def set_time(call):
    """
    Обработка inline callback запросов
    Выбор времени
    """
    client = client_dict.get(call.from_user.id)
    if client:
        client.time_record = call.data.lstrip('TIME')
        id_client = get_client_id(call.message.chat.id, call.from_user.username)
        if client.set_time(id_client):
            bot.edit_message_text(chat_id=call.from_user.id,
                                  message_id=call.message.message_id,
                                  text=f'Успешно записал вас!\n\n'
                                       f'• Услуга: {client.name_service}\n'
                                       f'• Мастер: {client.name_master}\n'
                                       f'• Дата: {client.date_record}\n'
                                       f'• Время: {client.time_record}',
                                  )
            check_phone_number(call.message)
        else:
            bot.send_message(call.message.chat.id, 'Время кто-то забронировал...\nПопробуй другое!')
    else:
        bot.delete_message(chat_id=call.message.chat.id,
                           message_id=call.message.message_id)
        check_phone_number(call.message)


bot.infinity_polling()
