import json
from datetime import datetime
from typing import Dict

import pytz
from aiogram.types import CallbackQuery
from db.crud import create_payment
from db.crud import get_user_with_subscription
from db.crud import update_subscription
from db.db_helper import sessionmanager
from db.models import SubscriptionType
from keyboards.menu import back_button
from keyboards.menu import create_confirmation_keyboard
from keyboards.menu import create_main_menu
from keyboards.menu import create_payment_keyboard
from keyboards.menu import sub_detail
from keyboards.menu import subscription_menu
from services.yookassa_service import YookassaService


async def format_subscription_info(user_db: Dict) -> str:
    subscription = user_db.get('subscription', {})
    expiry_date = subscription.get('subscription_expiry')
    is_active = subscription.get('active', False)

    if expiry_date and expiry_date > datetime.now(pytz.UTC):
        formatted_expiry_date = expiry_date.astimezone(pytz.UTC).strftime('%d.%m.%Y')
        sub_type_text = SubscriptionType.get_sub_type(
            subscription.get('subscription_type', 'Неизвестно')
        )

        card_info = json.loads(user_db.get('card_info', '{}')) if user_db.get('card_info') else {}
        card_text = (
            f"{card_info.get('card_type', 'Неизвестно')}: **** **** **** {card_info.get('card_last4', 'XXXX')}"
            if card_info
            else ''
        )

        if is_active:
            return (
                f"Ваша подписка активна.\n"
                f"Тип подписки: {sub_type_text}.\n"
                f"Дата окончания: {formatted_expiry_date}.\n"
                f"{card_text}"
            )
        else:
            return (
                f"Подписка будет активна до: {formatted_expiry_date}.\n"
                f"Тип подписки: {sub_type_text}.\n"
                f"{card_text}"
            )

    return None


async def process_pay_sub(callback_query: CallbackQuery) -> None:
    async with sessionmanager.session() as session:
        user_db = await get_user_with_subscription(session, callback_query.from_user.id)
    info_text = await format_subscription_info(user_db)
    if info_text:
        await callback_query.message.edit_text(
            text=info_text,
            reply_markup=sub_detail,
        )
    else:
        await callback_query.message.edit_text(
            'Выберите тип подписки:',
            reply_markup=subscription_menu,
        )


async def process_back_button(callback_query: CallbackQuery) -> None:
    async with sessionmanager.session() as session:
        user_db = await get_user_with_subscription(session, callback_query.from_user.id)
    await callback_query.message.edit_text(
        'Вы вернулись в главное меню.', reply_markup=create_main_menu(user_db)
    )
    await callback_query.answer()


async def process_subscription_selection(callback_query: CallbackQuery) -> None:
    async with sessionmanager.session() as session:
        user_db = await get_user_with_subscription(session, callback_query.from_user.id)
    subscription = user_db.get('subscription')
    if subscription.get('active') and subscription.get('subscription_expiry'):
        formatted_expiry_date = (
            subscription['subscription_expiry']
            .astimezone(pytz.UTC)
            .strftime('%d.%m.%Y')
        )
        sub_type_text = SubscriptionType.get_sub_type(
            subscription.get('subscription_type')
        )
        await callback_query.message.edit_text(
            f'Ваша подписка активна.\nТип подписки: {sub_type_text}.\nДата окончания: {formatted_expiry_date}.',
            reply_markup=back_button,
        )
        return

    selected_price = SubscriptionType.get_price(callback_query.data)
    if selected_price:
        payment = YookassaService.create_payment(selected_price, user_db.get('id'))
        confirmation_url = payment.confirmation.confirmation_url
        async with sessionmanager.session() as session:
            await create_payment(
                session,
                {
                    'payment_id': payment.id,
                    'user_id': user_db.get('id'),
                    'price': selected_price,
                    'payment_date': datetime.fromisoformat(
                        payment.created_at.strip('Z')
                    ).astimezone(pytz.UTC),
                    'status': payment.status,
                },
            )
        await callback_query.message.edit_text(
            'Нажмите кнопку ниже, чтобы завершить оплату подписки.',
            reply_markup=create_payment_keyboard(confirmation_url),
        )


async def process_cancel_sub_confirmation(callback_query: CallbackQuery) -> None:
    await callback_query.message.edit_text(
        'Вы уверены, что хотите отменить подписку?',
        reply_markup=create_confirmation_keyboard(
            'confirm_cancel_sub', 'keep_subscription'
        ),
    )
    await callback_query.answer()


async def process_confirm_cancel_sub(callback_query: CallbackQuery) -> None:
    async with sessionmanager.session() as session:
        user_db = await get_user_with_subscription(session, callback_query.from_user.id)
        await update_subscription(
            session, user_db.get('id'), {'active': False, 'card_info': ''}
        )
        user_db['subscription']['active'] = False
    await callback_query.message.edit_text(
        'Подписка отменена.', reply_markup=create_main_menu(user_db)
    )
    await callback_query.answer()


async def process_keep_subscription(callback_query: CallbackQuery) -> None:
    async with sessionmanager.session() as session:
        user_db = await get_user_with_subscription(session, callback_query.from_user.id)
    await callback_query.message.edit_text(
        'Вы вернулись в главное меню.', reply_markup=create_main_menu(user_db)
    )
    await callback_query.answer()
