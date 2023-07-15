from datetime import datetime, date
from config import TOKEN
from google_sheet import GoogleSheets
from telebot.callback_data import CallbackData, CallbackDataFilter
from telebot import types, TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import AdvancedCustomFilter

import telebot_calendar

bot = TeleBot(TOKEN)
client_dict = {}
calendar_dict = {}


# client1 = GoogleSheets()
# all_serv = client1.get_services()
# print(all_serv)
# # client1.name_master = 'Туманова Татьяна'
# name_serv = client1.get_all_days('Массаж')  # второй не обязательный
# print(len(name_serv), name_serv)
# time_to_rec = client1.get_free_time('18.07.23')
# print(time_to_rec)
# time_order = client1.set_time('10:00')
# print(time_order)
# print(client1)


@bot.message_handler(commands=['help', 'start'])
def choice_service(message):
    '''Выбор услуги для записи'''
    client = GoogleSheets(message.chat.id)
    client_dict[message.chat.id] = client
    all_serv = client.get_services()
    client.dct_master_service = all_serv
    markup = InlineKeyboardMarkup(row_width=3)
    markup.add(*[InlineKeyboardButton(text=x, callback_data=x) for x in all_serv.keys()])
    bot.send_message(message.chat.id, "Выбери услугу:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in client_dict[call.message.chat.id].dct_master_service.keys())
def choice_master(call):
    '''
    Обработка inline callback запросов
    Выбор мастера
    '''
    client = client_dict[call.message.chat.id]
    name_ser = client.name_service = call.data
    dct = client.dct_master_service
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(*[InlineKeyboardButton(text=x, callback_data=x) for x in dct[name_ser]])

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выбери Мастера:",
                          parse_mode='Markdown')
    bot.edit_message_reply_markup(call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in client_dict[call.message.chat.id].dct_master_service[
    client_dict[call.message.chat.id].name_service])
def choice_date(call):
    '''
    Обработка inline callback запросов
    Выбор даты
    '''
    client = client_dict[call.message.chat.id]
    client.name_master = call.data
    lst = client.get_all_days(client.name_service)
    lst = list(map(lambda x: datetime.strptime(x, '%d.%m.%y').date(), lst))
    client.lst_currant_date = lst
    calendar_dict[call.message.chat.id] = str(call.message.chat.id)
    bot.edit_message_text(chat_id=call.from_user.id,
                          message_id=call.message.message_id,
                          text='Выбери доступную дату:\n ✅ - есть свободное время')
    bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=telebot_calendar.create_calendar(
                                      name=calendar_dict[call.message.chat.id], lst_current_date=lst))


@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar_dict[call.message.chat.id]))
def choice_time(call: CallbackQuery):
    """
    Обработка inline callback запросов
    Выбор времени
    """
    client = client_dict[call.message.chat.id]
    lst = client.lst_currant_date
    # At this point, we are sure that this calendar is ours. So we cut the line by the separator of our calendar
    name, action, year, month, day = call.data.split(':')
    # Processing the calendar. Get either the date or None if the buttons are of a different type
    date = telebot_calendar.calendar_query_handler(
        bot=bot, call=call, name=name, action=action, year=year, month=month, day=day,
        lst_currant_date=lst
    )

    if action == "DAY":
        date_act = datetime(int(year), int(month), int(day)).strftime('%d.%m.%y')
        lst_times = client.get_free_time(date_act)
        markup = InlineKeyboardMarkup(row_width=4)
        for i in lst_times['Время']:
            print(i)
            print(type(i))
        markup.add(*[InlineKeyboardButton(text=x, callback_data=x) for x in lst_times['Время']])
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(
            chat_id=call.from_user.id,
            text="Выбери время:",
            reply_markup=markup
        )
        print(f"{calendar_dict[call.message.chat.id]}: Day: {date.strftime('%d.%m.%Y')}")

    elif action == "CANCEL":
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        print(f"{calendar_dict[call.message.chat.id]}: Отмена")
        del client_dict[call.message.chat.id]
        del calendar_dict[call.message.chat.id]
        choice_service(call.message)


@bot.callback_query_handler(func=lambda call: call.data in client_dict[call.message.chat.id].dct_currant_time['Время'])
def set_time(call):
    '''
    Обработка inline callback запросов
    Выбор времени
    '''
    client = client_dict[call.message.chat.id]
    id_client = str(call.message.chat.id) + str(call.message.from_user.id)
    print(id_client)
    if client.set_time(call.data, id_client):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f'Успешно записал вас {client}')
    else:
        bot.send_message(call.message.chat.id, 'Время кто-то забронировал...\nПопробуй другое!')
    print(client)


# del client_dict[call.message.chat.id]
# del calendar_dict[call.message.chat.id]
bot.infinity_polling()
