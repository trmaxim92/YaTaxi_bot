from sqlalchemy import delete, insert, select, update

from bottaxi.models.models import UserModel, DriverSettingsModel, AccountParkModel, HelpModel
from bottaxi.services.other_functions.phone_formatter import phone_formatting



async def get_info_from_help(session):
    """Получение поля text из таблицы Help."""
    exists = await session.get(HelpModel, 1)

    return exists


async def add_or_update_text_for_help(session, text):
    """Добавление текста для команды /configure_help."""
    exists = await get_info_from_help(session)

    if exists is None:
        result = await session.execute(
            insert(
                HelpModel
            ).values(
                text=text
            ).returning(HelpModel.text)
        )
        await session.commit()
        return result.fetchone()[0]

    elif exists is not None:
        result = await session.execute(
            update(
                HelpModel
            ).where(
                HelpModel.id == exists.id
            ).values(
                text=text
            ).returning(HelpModel.text)
        )

        await session.commit()
        return result.fetchone()[0]


async def add_url_driver(session, driver_url, phone):
    """Добавление url страницы водителя парка."""
    user = (await session.execute(
        select(
            DriverSettingsModel.telegram_id
        ).join(
            UserModel
        ).where(
            UserModel.phone == phone
        ).union_all(
            select(
                UserModel.telegram_id
            ).where(
                UserModel.phone == phone)
        ))).fetchall()
    print(user)

    # если записи нет в driver_settings, то она создается
    if len(user) == 1:
        await session.execute(
            insert(
                DriverSettingsModel
            ).values(
                telegram_id=user[0][0],
                url_driver_limit=driver_url
            ))
    # если такая запись есть, то она обновляется
    elif len(user) > 1:
        await session.execute(
            update(
                DriverSettingsModel
            ).where(
                DriverSettingsModel.telegram_id == user[0][0]
            ).values(
                url_driver_limit=driver_url
            ))

    await session.commit()


async def get_url_driver_limit(session, phone):
    """Получить url страницы водителя в парке / вкладка "Детали"."""
    result = (await session.execute(
        select(
            DriverSettingsModel.url_driver_limit
        ).join(
            UserModel
        ).where(
            UserModel.phone == phone
        ))).fetchone()

    return result


async def update_account_password(session, password):
    """Обновление / установка пароля парка."""
    exists = await get_account_password(session)

    if exists is None:
        result = (await session.execute(
            insert(
                AccountParkModel
            ).values(
                password=password
            ).returning(AccountParkModel.password))).scalar()

        await session.commit()
        return result

    if exists is not None:
        result = (await session.execute(
            update(
                AccountParkModel
            ).where(
                AccountParkModel.id == exists.id
            ).values(
                password=password
            ).returning(AccountParkModel.password))).scalar()

        await session.commit()
        return result


async def get_account_password(session):
    """Получение пароля парка."""
    result = (await session.get(
        AccountParkModel, 1)).password

    return result


async def delete_access_user(session, telegram_id):
    """Отключить доступ пользователю для смены в долг."""
    result = (await session.execute(
        update(
            DriverSettingsModel
        ).where(
            DriverSettingsModel.telegram_id == telegram_id
        ).values(
            access_limit=False).returning(DriverSettingsModel.access_limit))).scalar()
    await session.commit()

    return result


async def add_or_update_limit_user(session, taxi_id, limit):
    """Добавление или обновление записи водителя с лимитом."""

    # возвращается две записи из бд, если в обеих таблицах есть связанная запись.
    user = (await session.execute(
        select(
            DriverSettingsModel.telegram_id, UserModel.first_name, UserModel.middle_name
        ).join(
            UserModel
        ).where(
            UserModel.taxi_id == taxi_id
        ).union_all(
            select(
                UserModel.telegram_id, UserModel.first_name, UserModel.middle_name
            ).where(
                UserModel.taxi_id == taxi_id)

        ))).fetchall()

    # если записи нет в driver_settings, то она создается
    if len(user) == 1:
        await session.execute(
            insert(
                DriverSettingsModel
            ).values(
                telegram_id=user[0][0],
                limit=limit,
                access_limit=True
            ))
    # если такая запись есть, то она обновляется
    elif len(user) > 1:
        await session.execute(
            update(
                DriverSettingsModel
            ).where(
                DriverSettingsModel.telegram_id == user[0][0]
            ).values(
                limit=limit,
                access_limit=True
            ))
    await session.commit()

    return user[0]


async def access_debt_mode(session, user_id):
    """Получить статуса для смены в долг."""
    result = (await session.execute(
        select(
            DriverSettingsModel.access_limit, DriverSettingsModel.limit
        ).join(
            UserModel
        ).where(
            UserModel.telegram_id == user_id))).fetchone()

    return result


async def get_user_unique_phone(session, phone):
    """Получить одного пользователя по telegram_id."""
    user_phone = phone_formatting(phone)
    result = (await session.execute(select(
        UserModel.first_name, UserModel.middle_name, UserModel.taxi_id, UserModel.last_name, UserModel.telegram_id
    ).where(UserModel.phone == user_phone))).fetchone()

    return result


async def get_all_users(session):
    """Получить список пользователей."""
    result = (await session.execute(select(
        UserModel.first_name, UserModel.last_name, UserModel.middle_name, UserModel.phone, UserModel.telegram_id))).fetchall()

    return result


async def get_user(session, user_id):
    """Получить одного пользователя по telegram_id."""
    result = (await session.execute(select(
        UserModel.first_name, UserModel.middle_name, UserModel.taxi_id, UserModel.phone, UserModel.last_name
    ).where(UserModel.telegram_id == user_id))).fetchone()

    return result


async def add_user(session, user):
    """Запрос на добавление в БД."""
    result = await session.execute(insert(UserModel).values(
        telegram_id=user.get('telegram_id'),
        first_name=user.get('first_name'),
        last_name=user.get('last_name'),
        middle_name=user.get('middle_name', ' '),
        phone=user.get('phone'),
        taxi_id=user.get('taxi_id')
    ).returning(
        UserModel.first_name, UserModel.last_name, UserModel.middle_name)
    )
    await session.commit()

    return result.first()


async def drop_user(session, phone, state):
    """Запрос на удаление из БД."""

    # проверка номер телеофна на соответствие.
    user_phone = phone_formatting(phone)
    # проверяем есть ли такой пользователь
    user = (await session.execute(select(UserModel.telegram_id).where(UserModel.phone == user_phone))).first()

    if user is not None:
        # удаление номера телефона
        await session.execute(delete(UserModel).where(UserModel.phone == user_phone))
        await session.commit()
        # сброс состояния пользователя.
        await state.finish()
        return f'Пользователь с номером телефона +{user_phone} успешно удален'
    else:
        return f'Пользователь с номером телефона +{user_phone} не найден. Попробуйте ввести ещё раз..'
