"""
Создание клавиатуры главного меню и кнопок "Назад"/"Отмена"
"""
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_markup_menu():
    """
    Создаёт клавиатуру главного меню

    :return: InlineKeyboardMarkup
    """
    menu_buttons = ['Запись✅', 'Отмена записи❌', 'Мои записи📝']
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(text=menu_buttons[0], callback_data='RECORD'))
    markup.add(InlineKeyboardButton(text=menu_buttons[1], callback_data='CANCEL_RECORD'))
    markup.add(InlineKeyboardButton(text=menu_buttons[2], callback_data='MY_RECORD'))

    return markup


def button_to_menu(return_callback: str | None, return_text='Назад', menu_text='Вернуться в меню') \
        -> list[InlineKeyboardButton]:
    """
    Создает кнопки "Назад" и "В главное меню".

    :param return_callback: Callback-данные для кнопки "Назад".
                            Если значение - None, то кнопка не будет создана.
    :param return_text: Текст на кнопке "Назад" (по умолчанию - "Назад")
    :param menu_text: Текст на кнопке "В главное меню" (по умолчанию - "Вернуться в меню")

    :return: Список объектов InlineKeyboardButton
    """
    if return_callback:
        return [InlineKeyboardButton(text=return_text, callback_data=return_callback),
                InlineKeyboardButton(text=menu_text, callback_data='MENU')]
    return [InlineKeyboardButton(text=menu_text, callback_data='MENU')]
