from datetime import datetime
from datetime import timedelta
from typing import List
from typing import Optional
from typing import Tuple

import pytz
from db.db_helper import Base
from sqlalchemy import UUID
from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class SubscriptionType:
    _PRICES = {
        'one_month': 990.00,
        'six_months': 4990.00,
        'one_year': 7990.00,
    }
    _SUB_TYPE = {
        'one_month': 'месячная',
        'six_months': 'полугодовая',
        'one_year': 'годовая',
    }

    @classmethod
    def _get_expiration_date(cls, subscription_name):
        now = datetime.now(tz=pytz.UTC)
        if subscription_name == 'one_month':
            return now + timedelta(days=30)
        elif subscription_name == 'six_months':
            return now + timedelta(days=180)
        elif subscription_name == 'one_year':
            return now + timedelta(days=365)
        return None

    @classmethod
    def get_price(cls, subscription_name) -> float:
        return cls._PRICES.get(subscription_name)

    @classmethod
    def get_sub_type(cls, subscription_name: str) -> str:
        return cls._SUB_TYPE.get(subscription_name)

    @classmethod
    def get_subscription_name_by_price(cls, price) -> Tuple[str, datetime]:
        for name, p in cls._PRICES.items():
            if p == price:
                return name, cls._get_expiration_date(name)


class User(Base):
    user_telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    payments: Mapped[List['Payment']] = relationship('Payment', back_populates='user')
    subscription: Mapped[Optional['Subscription']] = relationship(
        'Subscription', uselist=False, back_populates='user'
    )


class Subscription(Base):
    payment_method_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('users.id'), unique=True
    )
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_expiry: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    subscription_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    card_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped['User'] = relationship('User', back_populates='subscription')


class Payment(Base):
    payment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    price: Mapped[float]
    status: Mapped[Optional[str]]
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user: Mapped['User'] = relationship('User', back_populates='payments')
