import json
from datetime import datetime
from typing import Dict

import pytz
from core.bot_config import get_bot
from core.config import settings
from db.crud import get_user_with_subscription_by_user_id
from db.crud import update_payment
from db.crud import update_subscription
from db.db_helper import sessionmanager
from db.models import SubscriptionType
from fastapi import Request
from keyboards.menu import sub_detail
from starlette import status
from starlette.exceptions import HTTPException
from yookassa import Configuration
from yookassa import Payment
from yookassa.domain.common import SecurityHelper
from yookassa.domain.notification import WebhookNotificationEventType
from yookassa.domain.notification import WebhookNotificationFactory

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

bot = get_bot()


class YookassaService:
    @staticmethod
    def create_payment(
        price: float,
        user_id: int,
        is_subscription: bool = False,
        payment_method_id: str = None,
    ):
        price_value = f'{price:.2f}'
        payment_data = {
            'amount': {'value': price_value, 'currency': 'RUB'},
            'description': 'Оплата подписки 1% by TEMCHENKO',
            'capture': True,
            'metadata': {
                'user_id': user_id,
                'type_sub': 'first' if not is_subscription else 'continue',
            },
        }

        if is_subscription:
            payment_data['payment_method_id'] = payment_method_id
        else:
            payment_data.update(
                {
                    'payment_method_data': {'type': 'bank_card'},
                    'confirmation': {
                        'type': 'redirect',
                        'return_url': 'https://t.me/Temchenko58Bot',
                    },
                    'save_payment_method': True,
                }
            )

        return Payment.create(payment_data)


class WebhookService:
    @staticmethod
    async def process_webhook(request: Request) -> None:
        event_json = await request.json()
        notification_object = WebhookNotificationFactory().create(event_json)
        response_object = notification_object.object
        payment_method_id = response_object.payment_method.id

        user_db = await WebhookService._get_user(
            response_object.metadata.get('user_id')
        )
        subscription = user_db.get('subscription')
        type_sub = response_object.metadata.get('type_sub')
        card_info = {
            'card_type': response_object.payment_method.card.card_type,
            'card_last4': response_object.payment_method.card.last4,
            'card_expiry_month': response_object.payment_method.card.expiry_month,
            'card_expiry_year': response_object.payment_method.card.expiry_year,
            'card_issuer_country': response_object.payment_method.card.issuer_country,
        }
        card_info_str = json.dumps(card_info)

        if notification_object.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
            payment_amount = float(response_object.amount['value'])
            subscription_type, subscription_expiry = (
                SubscriptionType.get_subscription_name_by_price(payment_amount)
            )

            await WebhookService._update_payment(
                payment_id=response_object.id,
                data={'status': response_object.status},
            )

            text = f'Подписка оформлена успешно! Тип подписки: {SubscriptionType.get_sub_type(subscription_type)}.'
            if type_sub == 'continue':
                text = f'Продление подписки успешно! Тип подписки: {SubscriptionType.get_sub_type(subscription_type)}.'
                current_subscription_expiry = subscription.get('subscription_expiry')
                subscription_expiry = (
                    current_subscription_expiry - datetime.now(tz=pytz.UTC)
                ) + subscription_expiry

                await bot.send_message(user_db.get('user_telegram_id'), text)
            await bot.send_message(
                user_db.get('user_telegram_id'), text, reply_markup=sub_detail
            )

            await WebhookService.create_subscription(
                user_db.get('id'),
                payment_method_id,
                card_info_str,
                subscription_type,
                subscription_expiry,
            )

    @staticmethod
    async def check_ip(request: Request) -> None:
        forwarded_for = request.headers.get('x-forwarded-for')
        ip = forwarded_for.split(',')[0].strip() if forwarded_for else None
        if not ip or not SecurityHelper().is_ip_trusted(ip):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Запрос поступил не от Yookassa',
            )

    @staticmethod
    async def _update_payment(payment_id: int, data: Dict) -> None:
        async with sessionmanager.session() as session:
            await update_payment(session, payment_id, data)

    @staticmethod
    async def _get_user(user_id: int) -> Dict:
        async with sessionmanager.session() as session:
            return await get_user_with_subscription_by_user_id(session, int(user_id))

    @staticmethod
    async def create_subscription(
        user_id: int,
        payment_method_id: str,
        card_info_str: str,
        subscription_type: str,
        subscription_expiry: str,
    ):
        async with sessionmanager.session() as session:
            data = {
                'subscription_expiry': subscription_expiry,
                'subscription_type': subscription_type,
                'payment_method_id': payment_method_id,
                'active': True,
                'card_info': card_info_str,
            }
            await update_subscription(session, user_id, data)
