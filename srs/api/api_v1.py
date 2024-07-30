from api.webhooks import router as webhooks_router
from core.bot_config import get_bot
from core.bot_config import get_dispatcher
from fastapi import APIRouter
from tasks.main import scheduler

bot = get_bot()
dp = get_dispatcher()

router = APIRouter(prefix='/api/v1')


@router.get('/jobs')
def get_jobs():
    jobs = scheduler.get_jobs()
    return [
        {'id': job.id, 'next_run': job.next_run_time, 'trigger': str(job.trigger)}
        for job in jobs
    ]


router.include_router(webhooks_router)
