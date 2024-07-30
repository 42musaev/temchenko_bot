from aiogram.types import Update
from core.bot_config import get_bot
from core.bot_config import get_dispatcher
from fastapi import APIRouter
from fastapi.requests import Request
from services.yookassa_service import WebhookService

bot = get_bot()
dp = get_dispatcher()

router = APIRouter(prefix='/webhook', tags=['webhooks'])


@router.post('')
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={'bot': bot})
    await dp.feed_update(bot, update)


@router.post('/pay')
async def webhook_pay(request: Request) -> None:
    await WebhookService.process_webhook(request)
