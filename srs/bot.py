import logging
from contextlib import asynccontextmanager

import uvicorn
from aiogram import Dispatcher
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from callbacks.menu import router as callback_menu_router
from core.bot_config import get_bot
from core.config import settings
from fastapi import FastAPI
from fastapi.requests import Request
from handlers.new_member import router as new_member_router
from handlers.start import router as start_handler_router
from tasks.main import handle_expired_subscriptions_task
from tasks.main import renew_subscriptions_task
from webhooks.aprove_payment import router as aprove_payment_router

bot = get_bot()
dp = Dispatcher()

scheduler = AsyncIOScheduler()
scheduler.add_job(renew_subscriptions_task, IntervalTrigger(hours=6))
scheduler.add_job(handle_expired_subscriptions_task, IntervalTrigger(hours=6))


@asynccontextmanager
async def lifespan(app: FastAPI):
    dp.include_router(start_handler_router)
    dp.include_router(callback_menu_router)
    dp.include_router(new_member_router)

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
app.include_router(aprove_payment_router)

# Set up logging


@app.post('/webhook')
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={'bot': bot})
    await dp.feed_update(bot, update)


@app.get('/jobs')
def get_jobs():
    jobs = scheduler.get_jobs()
    return [
        {'id': job.id, 'next_run': job.next_run_time, 'trigger': str(job.trigger)}
        for job in jobs
    ]


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,  # Adjust this level to capture more detailed logs
        format='%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )

    uvicorn.run('bot:app', host='0.0.0.0', port=8000, reload=True, log_level='debug')
