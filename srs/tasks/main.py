from datetime import datetime
from datetime import timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from core.bot_config import get_bot
from core.config import settings
from db.db_helper import sessionmanager
from db.models import Subscription
from db.models import SubscriptionType
from db.models import User
from services.yookassa_service import YookassaService
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.orm import joinedload

bot = get_bot()
scheduler = AsyncIOScheduler()


async def renew_subscriptions_task():
    now = datetime.now(pytz.utc)
    twenty_four_hours_later = now + timedelta(hours=24)

    async with sessionmanager.session() as session:
        stmt = (
            select(User)
            .join(Subscription)
            .options(joinedload(User.subscription))
            .where(
                Subscription.subscription_expiry.isnot(None),
                Subscription.active == True,  # noqa: E712
                Subscription.subscription_expiry > now,
                Subscription.subscription_expiry <= twenty_four_hours_later,
            )
        )
        result = await session.execute(stmt)
        users_to_renew = result.scalars().all()

    for user in users_to_renew:
        subscription = user.subscription
        if subscription:
            YookassaService.create_payment(
                SubscriptionType.get_price(subscription.subscription_type),
                user.id,
                is_subscription=True,
                payment_method_id=subscription.payment_method_id,
            )


async def handle_expired_subscriptions_task():
    now = datetime.now(pytz.utc)

    async with sessionmanager.session() as session:
        stmt = (
            select(User)
            .join(Subscription)
            .where(
                Subscription.subscription_expiry.isnot(None),
                Subscription.subscription_expiry <= now,
            )
        )
        result = await session.execute(stmt)
        users_to_expire = result.scalars().all()

        for user in users_to_expire:
            await bot.ban_chat_member(settings.CHANEL_CHAT_ID, user.user_telegram_id)
            await bot.unban_chat_member(settings.CHANEL_CHAT_ID, user.user_telegram_id)
            await deactivate_user_subscription(user.id)


async def deactivate_user_subscription(user_id):
    async with sessionmanager.session() as session:
        stmt = (
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(
                active=False,
                card_info='',
                subscription_expiry=None,
            )
        )
        await session.execute(stmt)
        await session.commit()


scheduler.add_job(renew_subscriptions_task, IntervalTrigger(hours=6))
scheduler.add_job(handle_expired_subscriptions_task, IntervalTrigger(hours=6))
