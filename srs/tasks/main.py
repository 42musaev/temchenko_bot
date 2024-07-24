from datetime import datetime
from datetime import timedelta

import pytz
from core.bot_config import get_bot
from core.config import settings
from core.pay import create_yookassa_sub_payment
from db.db_helper import sessionmanager
from db.models import SubscriptionType
from db.models import User
from sqlalchemy import select
from sqlalchemy import update

bot = get_bot()


async def renew_subscriptions_task():
    now = datetime.now(pytz.utc)
    twenty_four_hours_later = now + timedelta(hours=24)

    async with sessionmanager.session() as session:
        stmt = select(User).where(
            User.subscription_expiry.isnot(None),
            User.active == True,  # noqa: E712
            User.subscription_expiry > now,
            User.subscription_expiry <= twenty_four_hours_later,
        )
        result = await session.execute(stmt)
        users_to_renew = result.scalars().all()

    for user in users_to_renew:
        create_yookassa_sub_payment(
            SubscriptionType.get_price(user.subscription_type),
            user.payment_method_id,
            user.user_telegram_id,
        )


async def handle_expired_subscriptions_task():
    now = datetime.now(pytz.utc)

    async with sessionmanager.session() as session:
        stmt = select(User).where(
            User.subscription_expiry.isnot(None),
            User.subscription_expiry <= now,
        )
        result = await session.execute(stmt)
        users_to_expire = result.scalars().all()

        for user in users_to_expire:
            await bot.ban_chat_member(settings.CHANEL_CHAT_ID, user.user_telegram_id)
            await bot.unban_chat_member(settings.CHANEL_CHAT_ID, user.user_telegram_id)
            await deactivate_user_subscription(user.user_telegram_id)


async def deactivate_user_subscription(user_telegram_id):
    async with sessionmanager.session() as session:
        stmt = (
            update(User)
            .where(User.user_telegram_id == user_telegram_id)
            .values(
                active=False,
                card_info='',
                subscription_expiry=None,
            )
        )
        await session.execute(stmt)
        await session.commit()
