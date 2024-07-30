from aiogram import F
from aiogram import Router
from aiogram.types import CallbackQuery
from services.menu_service import process_back_button
from services.menu_service import process_cancel_sub_confirmation
from services.menu_service import process_confirm_cancel_sub
from services.menu_service import process_keep_subscription
from services.menu_service import process_pay_sub
from services.menu_service import process_subscription_selection

router = Router()


@router.callback_query(F.data == 'pay_sub')
async def callback_puy_sub(callback_query: CallbackQuery) -> None:
    await process_pay_sub(callback_query)


@router.callback_query(F.data.in_({'one_month', 'six_months', 'one_year'}))
async def callback_query_subscription_selection(callback_query: CallbackQuery) -> None:
    await process_subscription_selection(callback_query)


@router.callback_query(F.data == 'back')
async def process_back(callback_query: CallbackQuery) -> None:
    await process_back_button(callback_query)


@router.callback_query(F.data == 'cancel_sub')
async def callback_query_cancel_sub_confirmation(callback_query: CallbackQuery) -> None:
    await process_cancel_sub_confirmation(callback_query)


@router.callback_query(F.data == 'confirm_cancel_sub')
async def callback_query_confirm_cancel_sub(callback_query: CallbackQuery) -> None:
    await process_confirm_cancel_sub(callback_query)


@router.callback_query(F.data == 'keep_subscription')
async def callback_query_keep_subscription(callback_query: CallbackQuery) -> None:
    await process_keep_subscription(callback_query)
