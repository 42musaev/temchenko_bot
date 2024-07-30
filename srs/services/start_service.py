import logging
from typing import Dict

from aiogram.types import Message
from db.crud import create_subscription
from db.crud import create_user
from db.crud import get_user_with_subscription
from db.db_helper import sessionmanager

logger = logging.getLogger(__name__)


async def process_user_start(message: Message) -> Dict:
    async with sessionmanager.session() as session:
        user_db = await get_user_with_subscription(session, message.from_user.id)
        if not user_db:
            user_db = await create_user(
                session, {'user_telegram_id': message.from_user.id}
            )
            await create_subscription(
                session, {'user_id': user_db.get('id'), 'active': False}
            )
    return user_db
