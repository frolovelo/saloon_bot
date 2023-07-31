from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_markup_menu():
    menu_buttons = ['Запись✅', 'Отмена записи❌', 'Мои записи📝']
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(text=menu_buttons[0], callback_data='RECORD'))
    markup.add(InlineKeyboardButton(text=menu_buttons[1], callback_data='CANCEL_RECORD'))
    markup.add(InlineKeyboardButton(text=menu_buttons[2], callback_data='MY_RECORD'))

    return markup


def button_to_menu(call_data_return, text_return='Назад', text_cancel='Вернуться в меню'):
    if call_data_return:
        return [InlineKeyboardButton(text=text_return, callback_data=call_data_return),
                InlineKeyboardButton(text=text_cancel, callback_data='MENU')]
    else:
        return [InlineKeyboardButton(text=text_cancel, callback_data='MENU')]