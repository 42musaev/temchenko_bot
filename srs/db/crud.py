from typing import Dict
from typing import Type

from db.db_helper import Base
from db.models import Payment
from db.models import Subscription
from db.models import User
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


def result_to_dict(result) -> dict:
    if result:
        return {field.name: getattr(result, field.name) for field in result.__table__.c}


async def get_object_by_id(
    session: AsyncSession, model: Type[Base], object_id: int
) -> Dict:
    stmt = select(model).where(model.id == object_id)
    result = (await session.execute(stmt)).scalar_one_or_none()
    return result_to_dict(result)


async def get_user_with_subscription(
    session: AsyncSession, user_telegram_id: int
) -> Dict | None:
    stmt = (
        select(User)
        .options(joinedload(User.subscription))
        .where(User.user_telegram_id == user_telegram_id)
    )

    result = (await session.execute(stmt)).scalar_one_or_none()

    if result:
        user_dict = result_to_dict(result)
        if result.subscription:
            user_dict['subscription'] = result_to_dict(result.subscription)
        else:
            user_dict['subscription'] = None
        return user_dict
    return None


async def get_user_with_subscription_by_user_id(
    session: AsyncSession, user_id: int
) -> Dict | None:
    stmt = select(User).options(joinedload(User.subscription)).where(User.id == user_id)

    result = (await session.execute(stmt)).scalar_one_or_none()

    if result:
        user_dict = result_to_dict(result)
        if result.subscription:
            user_dict['subscription'] = result_to_dict(result.subscription)
        else:
            user_dict['subscription'] = None
        return user_dict
    return None


async def create_user(session: AsyncSession, data: Dict) -> Dict:
    stmt = insert(User).values(**data).returning(User.id)
    user_id = (await session.execute(stmt)).scalar()
    await session.commit()
    return await get_object_by_id(session, User, user_id)


async def get_user(session: AsyncSession, user_id: int) -> Dict:
    return await get_object_by_id(session, User, user_id)


async def update_user(session: AsyncSession, user_telegram_id: int, data: Dict):
    stmt = update(User).where(User.user_telegram_id == user_telegram_id).values(**data)
    await session.execute(stmt)
    await session.commit()


async def create_payment(session: AsyncSession, data: Dict):
    stmt = insert(Payment).values(**data).returning(Payment.id)
    payment_id = (await session.execute(stmt)).scalar()
    await session.commit()
    return await get_object_by_id(session, User, payment_id)


async def update_payment(session: AsyncSession, payment_id: int, data: Dict):
    stmt = update(Payment).where(Payment.payment_id == payment_id).values(**data)
    await session.execute(stmt)
    await session.commit()


async def create_subscription(session: AsyncSession, data: Dict) -> Dict:
    stmt = insert(Subscription).values(**data).returning(Subscription.id)
    subscription_id = (await session.execute(stmt)).scalar()
    await session.commit()
    return await get_object_by_id(session, Subscription, subscription_id)


async def update_subscription(session: AsyncSession, user_id: int, data: Dict):
    stmt = update(Subscription).where(Subscription.user_id == user_id).values(**data)
    await session.execute(stmt)
    await session.commit()
