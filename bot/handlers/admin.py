from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.utils import log_user_action
from bot.database import get_db

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} вызвал команду /admin")
    await message.answer("Доступ к админ-панели")

@router.callback_query(lambda c: c.data.startswith('verify_payment_'))
async def handle_payment_verification(callback: types.CallbackQuery):
    log_user_action(callback.from_user, f"Админ {callback.from_user.id} подтвердил оплату")
    await callback.answer("Оплата подтверждена") 