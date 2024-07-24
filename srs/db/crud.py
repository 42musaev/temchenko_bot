from typing import Dict

from db.models import Payment
from db.models import User
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession


def result_to_dict(result):
    if result:
        return {field.name: getattr(result, field.name) for field in result.__table__.c}


async def create_user(session: AsyncSession, data: Dict):
    if not (await get_user(session, data['user_telegram_id'])):
        stmt = insert(User).values(**data)
        await session.execute(stmt)
        await session.commit()
    return await get_user(session, data['user_telegram_id'])


async def update_user(session: AsyncSession, user_telegram_id: int, data: Dict):
    stmt = update(User).where(User.user_telegram_id == user_telegram_id).values(**data)
    await session.execute(stmt)
    await session.commit()


async def get_user(session: AsyncSession, user_telegram_id: int) -> Dict:
    stmt = select(User).where(User.user_telegram_id == user_telegram_id)
    result = (await session.execute(stmt)).scalar_one_or_none()
    return result_to_dict(result)


async def create_payment(session: AsyncSession, data: Dict):
    stmt = insert(Payment).values(**data)
    await session.execute(stmt)
    await session.commit()


async def update_payment(session: AsyncSession, payment_id: int, data: Dict):
    stmt = update(Payment).where(Payment.payment_id == payment_id).values(**data)
    await session.execute(stmt)
    await session.commit()
