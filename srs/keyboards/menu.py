from typing import Dict

from aiogram.types import InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from core.config import settings


def create_button(
    text: str, url: str = None, callback_data: str = None
) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, url=url, callback_data=callback_data)


def create_payment_keyboard(confirmation_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [create_button('Перейти к оплате', url=confirmation_url)],
            [create_button('Назад', callback_data='back')],
        ]
    )


back_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [create_button('Назад', callback_data='back')],
    ]
)

sub_detail = InlineKeyboardMarkup(
    inline_keyboard=[
        [create_button('Подписаться', url=settings.INVITE_LINK)],
        [create_button('Назад', callback_data='back')],
    ]
)

subscription_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [create_button('1 месяц | 990 ₽', callback_data='one_month')],
        [create_button('6 месяцев | 4990 ₽', callback_data='six_months')],
        [create_button('1 год | 7990 ₽', callback_data='one_year')],
        [create_button('Назад', callback_data='back')],
    ]
)


def create_main_menu(user_db: Dict | None = None) -> InlineKeyboardMarkup:
    main_menu_buttons = [
        [create_button('Оплатить/Подписаться', callback_data='pay_sub')],
    ]
    subscription = user_db.get('subscription')
    if subscription and subscription.get('active'):
        main_menu_buttons.append(
            [create_button('Отменить подписку', callback_data='cancel_sub')]
        )
    return InlineKeyboardMarkup(inline_keyboard=main_menu_buttons)


def create_confirmation_keyboard(
    callback_data_confirm: str, callback_data_cancel: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                create_button(
                    'Да, отменить подписку', callback_data=callback_data_confirm
                )
            ],
            [
                create_button(
                    'Нет, оставить подписку', callback_data=callback_data_cancel
                )
            ],
        ]
    )
