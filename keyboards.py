from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_markup_menu():
    menu_buttons = ['Запись✅', 'Отмена записи❌', 'Мои записи📝']
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(text=menu_buttons[0], callback_data='RECORD'))
    markup.add(InlineKeyboardButton(text=menu_buttons[1], callback_data='CANCEL_RECORD'))
    markup.add(InlineKeyboardButton(text=menu_buttons[2], callback_data='MY_RECORD'))

    return markup
