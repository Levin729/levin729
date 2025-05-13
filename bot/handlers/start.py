from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.utils import log_user_action
from bot.keyboards import get_start_kb, get_main_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    log_user_action(message.from_user, f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}! 👋 Это твой личный помощник для заказа услуг по Dota 2! 🚀 Хочешь прокачать свой аккаунт, поднять MMR или получить крутые советы от профи? Я здесь, чтобы помочь! 😎\n\nОзнакомься с отзывами наших довольных клиентов:\n\n🔗 https://funpay.com/users/3140450/\n\n🔗 https://t.me/dotalevin729\n\nВыбирай услугу, пиши мне, и мы сделаем твою игру незабываемой! 💪 Готов к победам? 😏",
        reply_markup=get_start_kb()
    )

@router.message(lambda message: message.text == "🚀 Старт")
async def handle_start_button(message: types.Message):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} нажал кнопку Старт")
    await message.answer(
        "Выберите действие:",
        reply_markup=get_main_kb()
    ) 