import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from api.api_v1 import router as api_v1_router
from callbacks.menu import router as callback_menu_router
from core.bot_config import get_bot
from core.bot_config import get_dispatcher
from core.config import settings
from fastapi import FastAPI
from handlers.new_member import router as new_member_router
from handlers.start import router as start_handler_router
from tasks.main import scheduler

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

logger = logging.getLogger(__name__)

bot = get_bot()
dp = get_dispatcher()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.include_router(api_v1_router)
    dp.include_router(new_member_router)
    dp.include_router(start_handler_router)
    dp.include_router(callback_menu_router)

    scheduler.start()

    await bot.set_webhook(
        url=settings.WEBHOOK_URL,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )
    yield
    await bot.delete_webhook()
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

if __name__ == '__main__':
    uvicorn.run('bot:app', host='0.0.0.0', port=8000)
