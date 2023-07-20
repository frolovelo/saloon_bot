from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

MENU_BUTTONS = ['Запись✅', 'Отмена записи❌', 'Мои записи📝']


def create_markup_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(text=MENU_BUTTONS[0], callback_data='RECORD'))
    markup.add(InlineKeyboardButton(text=MENU_BUTTONS[1], callback_data='CANCEL_RECORD'))
    markup.add(InlineKeyboardButton(text=MENU_BUTTONS[2], callback_data='MY_RECORD'))

    return markup
