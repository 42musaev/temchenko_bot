from aiogram import Router
from aiogram import html
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards.menu import create_main_menu
from services.start_service import process_user_start

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_db = await process_user_start(message)
    await message.answer(
        f'Здравствуйте, {html.bold(message.from_user.full_name)}!',
        reply_markup=create_main_menu(user_db),
    )
