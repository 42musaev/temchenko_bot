from aiogram import Router
from aiogram import html
from aiogram.filters import CommandStart
from aiogram.types import Message
from db.crud import create_user
from db.db_helper import sessionmanager
from keyboards.menu import create_main_menu

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    async with sessionmanager.session() as session:
        data = {
            'user_telegram_id': message.from_user.id,
            'chat_id': message.chat.id,
        }
        user_db = await create_user(session, data)
    await message.answer(
        f'Здравствуйте, {html.bold(message.from_user.full_name)}!',
        reply_markup=create_main_menu(user_db),
    )
