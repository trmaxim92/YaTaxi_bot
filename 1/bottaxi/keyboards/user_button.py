from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bottaxi.models.query import access_debt_mode


async def choose_menu_for_user(session, telegram_id):
    """Выбирается клавиатура для пользователя с учетом его настроек."""
    access = await access_debt_mode(session, telegram_id)
    # если водителю не разрешена смена в долг, поле access_limit
    if access is None or not access[0]:
        menu = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='💳Безнал'),
                    KeyboardButton(text='💵Нал / Безнал'),
                ],
                [
                    # KeyboardButton(text='🏁Завершить тек. заказ'),
                    # KeyboardButton(text='❌Отменить текущий заказ')
                ],
                [
                    # KeyboardButton(text='📈Неоплаченные заказы'),
                    # KeyboardButton(text='💰Заработок'),
                    KeyboardButton(text='📝Справка')
                ]
            ],
            resize_keyboard=True
        )
        return menu

    # если водителю разрешена смена в долг, поле access_limit
    elif access[0]:
        menu_plus = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='💳Безнал'),
                    KeyboardButton(text='💵Нал / Безнал'),
                    KeyboardButton(text='🕰Смена в долг')
                ],
                [
                    # KeyboardButton(text='🏁Завершить тек. заказ'),
                    # KeyboardButton(text=switch),
                    # KeyboardButton(text='❌Отменить текущий заказ')
                ],
                [
                    # KeyboardButton(text='📈Неоплаченные заказы'),
                    # KeyboardButton(text='💰Заработок'),
                    KeyboardButton(text='📝Справка')
                ]
            ],
            resize_keyboard=True
        )
        return menu_plus
