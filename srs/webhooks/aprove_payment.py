import json
from datetime import datetime

import pytz
from core.bot_config import get_bot
from db.crud import get_user
from db.crud import update_payment
from db.crud import update_user
from db.db_helper import sessionmanager
from db.models import SubscriptionType
from fastapi import APIRouter
from fastapi import HTTPException
from starlette.requests import Request
from yookassa.domain.common import SecurityHelper
from yookassa.domain.notification import WebhookNotificationEventType
from yookassa.domain.notification import WebhookNotificationFactory

router = APIRouter()
bot = get_bot()


@router.post('/webhook/pay')
async def webhook(request: Request) -> None:
    forwarded_for = request.headers.get('x-forwarded-for')
    ip = forwarded_for.split(',')[0].strip() if forwarded_for else None
    if not ip or not SecurityHelper().is_ip_trusted(ip):
        raise HTTPException(
            status_code=400,
            detail='Запрос поступил не от Yookassa',
        )

    try:
        event_json = await request.json()
        notification_object = WebhookNotificationFactory().create(event_json)
        response_object = notification_object.object
        user_telegram_id = int(response_object.metadata.get('user_telegram_id'))
        type_sub = response_object.metadata.get('type_sub')

        if notification_object.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
            payment_amount = float(response_object.amount['value'])
            subscription_type, subscription_expiry = (
                SubscriptionType.get_subscription_name_by_price(payment_amount)
            )

            card_info = {
                'card_type': response_object.payment_method.card.card_type,
                'card_last4': response_object.payment_method.card.last4,
                'card_expiry_month': response_object.payment_method.card.expiry_month,
                'card_expiry_year': response_object.payment_method.card.expiry_year,
                'card_issuer_country': response_object.payment_method.card.issuer_country,
            }
            card_info_str = json.dumps(card_info)

            async with sessionmanager.session() as session:
                user_data = await get_user(session, user_telegram_id)

                if user_data:
                    await update_payment(
                        session,
                        payment_id=response_object.id,
                        data={'status': response_object.status},
                    )

                    current_expiry_date = user_data.get('subscription_expiry')

                    if current_expiry_date and current_expiry_date > datetime.now(
                        tz=pytz.UTC
                    ):
                        subscription_expiry + (
                            subscription_expiry - current_expiry_date
                        )

                    await update_user(
                        session,
                        user_telegram_id,
                        data={
                            'subscription_expiry': subscription_expiry,
                            'subscription_type': subscription_type,
                            'payment_method_id': response_object.payment_method.id,
                            'chat_id': user_data.get('chat_id'),
                            'active': True,
                            'card_info': card_info_str,
                        },
                    )

                    if type_sub == 'continue':
                        text = (
                            f'Ваше продление подписки прошло успешно! '
                            f'Тип подписки: {SubscriptionType.get_sub_type(subscription_type)}. '
                        )
                    else:
                        text = f'Подписка оформлена успешно! Тип подписки: {SubscriptionType.get_sub_type(subscription_type)}. '

                    await bot.send_message(
                        chat_id=user_data.get('chat_id'),
                        text=text,
                    )

        elif notification_object.event == WebhookNotificationEventType.PAYMENT_CANCELED:
            text = 'Ваш платеж был отменен. Пожалуйста, попробуйте снова.'
            async with sessionmanager.session() as session:
                user_data = await get_user(session, user_telegram_id)
                if user_data:
                    await bot.send_message(
                        chat_id=user_data.get('chat_id'),
                        text=text,
                    )

    except Exception as e:
        print(f'Ошибка обработки вебхука: {e}')
        raise HTTPException(
            status_code=500,
            detail='Внутренняя ошибка сервера',
        ) from e
