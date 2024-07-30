from datetime import datetime

import pytz
from aiogram import Router
from aiogram.types import ChatJoinRequest
from db.crud import get_user_with_subscription
from db.db_helper import sessionmanager

router = Router()


@router.chat_join_request()
async def chat_join_request_handler(chat_join_request: ChatJoinRequest):
    async with sessionmanager.session() as session:
        user_db = await get_user_with_subscription(
            session, chat_join_request.from_user.id
        )
        subscription = user_db.get('subscription')
        subscription_expiry = subscription.get('subscription_expiry')
        if (
            not chat_join_request.from_user.is_bot
            and subscription_expiry
            and subscription_expiry > datetime.now(tz=pytz.UTC)
        ):
            await chat_join_request.approve()
        else:
            await chat_join_request.decline()
