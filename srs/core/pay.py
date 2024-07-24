from core.config import settings
from yookassa import Configuration
from yookassa import Payment

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def create_yookassa_payment(
    price: float,
    user_telegram_id: int,
):
    price_value = f'{price:.2f}'

    payment = Payment.create(
        {
            'amount': {'value': f'{price_value}', 'currency': 'RUB'},
            'payment_method_data': {'type': 'bank_card'},
            'confirmation': {
                'type': 'redirect',
                'return_url': 'https://t.me/Temchenko58Bot',
            },
            'capture': True,
            'description': 'Оплата подписки 1% by TEMCHENKO',
            'save_payment_method': True,
            'metadata': {'user_telegram_id': user_telegram_id, 'type_sub': 'first'},
        }
    )
    return payment


def create_yookassa_sub_payment(
    price: float,
    payment_method_id: str,
    user_telegram_id: int,
):
    price_value = f'{price:.2f}'
    payment = Payment.create(
        {
            'amount': {'value': f'{price_value}', 'currency': 'RUB'},
            'capture': True,
            'payment_method_id': f'{payment_method_id}',
            'description': 'Оплата подписки 1% by TEMCHENKO',
            'metadata': {'user_telegram_id': user_telegram_id, 'type_sub': 'continue'},
        }
    )
    return payment
