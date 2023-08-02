"""
Календарь из inline-кнопок
"""
import datetime
import calendar
import typing

from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

MONTHS = (
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)
DAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


class CallbackData:
    """
    Callback data factory
    """

    def __init__(self, prefix, *parts, sep=":"):
        if not isinstance(prefix, str):
            raise TypeError(
                f"Prefix must be instance of str not {type(prefix).__name__}"
            )
        if not prefix:
            raise ValueError("Prefix can't be empty")
        if sep in prefix:
            raise ValueError(f"Separator {sep!r} can't be used in prefix")
        if not parts:
            raise TypeError("Parts were not passed!")
        # print(prefix, parts)
        self.prefix = prefix
        self.sep = sep

        self._part_names = parts

    def new(self, *args, **kwargs) -> str:
        """
        Generate callback data

        :param args:
        :param kwargs:
        :return:
        """

        args = list(args)

        data = [self.prefix]

        for part in self._part_names:
            value = kwargs.pop(part, None)
            if value is None:
                if args:
                    value = args.pop(0)
                else:
                    raise ValueError(f"Value for {part!r} was not passed!")

            if value is not None and not isinstance(value, str):
                value = str(value)

            if not value:
                raise ValueError(f"Value for part {part!r} can't be empty!'")
            if self.sep in value:
                raise ValueError(
                    f"Symbol {self.sep!r} is defined as the separator and can't be used in parts' values"
                )

            data.append(value)

        if args or kwargs:
            raise TypeError("Too many arguments were passed!")

        callback_data = self.sep.join(data)
        if len(callback_data) > 64:
            raise ValueError("Resulted callback data is too long!")

        return callback_data

    def parse(self, callback_data: str) -> typing.Dict[str, str]:
        """
        Parse data from the callback data

        :param callback_data:
        :return:
        """

        prefix, *parts = callback_data.split(self.sep)

        if prefix != self.prefix:
            raise ValueError(
                "Passed callback data can't be parsed with that prefix.")
        elif len(parts) != len(self._part_names):
            raise ValueError("Invalid parts count!")

        result = {"@": prefix}
        result.update(zip(self._part_names, parts))

        return result

    def filter(self, **config):
        """
        Generate filter

        :param config:
        :return:
        """

        # print(config, self._part_names)
        for key in config.keys():
            if key not in self._part_names:
                return False

        return True


def create_calendar(lst_current_date: list[datetime.date], name: str = "calendar", year: int = None, month: int = None,
                    ) -> InlineKeyboardMarkup:
    """
    Create a built-in inline keyboard with calendar

    :param lst_current_date: Список доступных дат для записи в формате datetime.date
    :param name: Имя календаря
    :param year: Год используемый календарём, если не используете текущий год.
    :param month: Месяц используемый календарём, если не используете текущий месяц.
    :return: Возвращает объект InlineKeyboardMarkup с календарём.
    """

    now_day = datetime.datetime.now()

    if year is None:
        year = now_day.year
    if month is None:
        month = now_day.month

    calendar_callback = CallbackData(name, "action", "year", "month", "day")
    data_ignore = calendar_callback.new("IGNORE", year, month, "!")
    data_months = calendar_callback.new("MONTHS", year, month, "!")

    keyboard = InlineKeyboardMarkup(row_width=7)

    keyboard.add(
        InlineKeyboardButton(
            MONTHS[month - 1] + " " + str(year), callback_data=data_months
        )
    )

    keyboard.add(
        *[InlineKeyboardButton(day, callback_data=data_ignore) for day in DAYS]
    )

    for week in calendar.monthcalendar(year, month):
        row = list()
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(
                    " ", callback_data=data_ignore))
            else:
                if datetime.date(year, month, day) in lst_current_date:
                    row.append(
                        InlineKeyboardButton(
                            str(day) + '✅',
                            callback_data=calendar_callback.new(
                                "DAY", year, month, day),
                        )
                    )
                else:
                    row.append(
                        InlineKeyboardButton(
                            str(day),
                            callback_data=calendar_callback.new(
                                "DAY_EMPTY", year, month, day),
                        )
                    )
        keyboard.add(*row)

    keyboard.add(
        InlineKeyboardButton(
            "<", callback_data=calendar_callback.new("PREVIOUS-MONTH", year, month, "!")
        ),
        InlineKeyboardButton(
            "Назад", callback_data=calendar_callback.new("RETURN", year, month, "!")
        ),
        InlineKeyboardButton(
            "Меню", callback_data=calendar_callback.new("MENU", year, month, "!")
        ),
        InlineKeyboardButton(
            ">", callback_data=calendar_callback.new("NEXT-MONTH", year, month, "!")
        ),
    )

    return keyboard


def create_months_calendar(
        name: str = "calendar", year: int = None
) -> InlineKeyboardMarkup:
    """
    Создаёт календарь из месяцев

    param name:
    param year:
    return:
    """

    if year is None:
        year = datetime.datetime.now().year

    calendar_callback = CallbackData(name, "action", "year", "month", "day")

    keyboard = InlineKeyboardMarkup()

    for i, month in enumerate(zip(MONTHS[0::2], MONTHS[1::2])):
        keyboard.add(
            InlineKeyboardButton(
                month[0], callback_data=calendar_callback.new(
                    "MONTH", year, 2 * i + 1, "!")
            ),
            InlineKeyboardButton(
                month[1],
                callback_data=calendar_callback.new(
                    "MONTH", year, 2 * i + 2, "!"),
            ),
        )
    return keyboard


def calendar_query_handler(
        bot: TeleBot,
        call: CallbackQuery,
        name: str,
        action: str,
        year: int,
        month: int,
        day: int,
        lst_currant_date: list
) -> None or datetime.datetime:
    """
    The method creates a new calendar if the forward or backward button is pressed
    This method should be called inside CallbackQueryHandler.


    :param bot: The object of the bot CallbackQueryHandler
    :param call: CallbackQueryHandler data
    :param day:
    :param month:
    :param year:
    :param action:
    :param name:
    :param lst_currant_date: Список доступных дат для записи в формате date
    :return: Returns a tuple
    """

    current = datetime.datetime(int(year), int(month), 1)
    if action == "IGNORE":
        bot.answer_callback_query(callback_query_id=call.id, text='Тут ничего нет')
        return False, None
    elif action == "DAY_EMPTY":
        bot.answer_callback_query(callback_query_id=call.id, text='Свободного времени нет')
        return False, None
    elif action == "DAY":
        return datetime.datetime(int(year), int(month), int(day))
    elif action == "PREVIOUS-MONTH":
        preview_month = current - datetime.timedelta(days=1)
        bot.edit_message_text(
            text=call.message.text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_calendar(
                name=name, year=int(preview_month.year), month=int(preview_month.month),
                lst_current_date=lst_currant_date
            ),
        )
        return None
    elif action == "NEXT-MONTH":
        next_month = current + datetime.timedelta(days=31)
        bot.edit_message_text(
            text=call.message.text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_calendar(
                name=name, year=int(next_month.year), month=int(next_month.month),
                lst_current_date=lst_currant_date
            ),
        )
        return None
    elif action == "MONTHS":
        bot.edit_message_text(
            text=call.message.text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_months_calendar(name=name, year=current.year),
        )
        return None
    elif action == "MONTH":
        bot.edit_message_text(
            text=call.message.text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_calendar(
                name=name, year=int(year), month=int(month),
                lst_current_date=lst_currant_date),
        )
        return None
    elif action == "MENU":
        # bot.delete_message(
        #     chat_id=call.message.chat.id, message_id=call.message.message_id
        # )
        return "MENU", None
    elif action == "RETURN":
        return "RETURN", None
    else:
        bot.answer_callback_query(callback_query_id=call.id, text="ERROR!")
        # bot.delete_message(
        #     chat_id=call.message.chat.id, message_id=call.message.message_id
        # )
        return None
