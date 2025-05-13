from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from bot.utils import log_user_action
from bot.keyboards import get_payment_navigation_kb
from bot.states import PaymentStates
from bot.database import get_db

router = Router()

@router.callback_query(lambda c: c.data.startswith('payment_'))
async def handle_payment_method(callback: types.CallbackQuery, state: FSMContext):
    log_user_action(callback.from_user, f"Пользователь {callback.from_user.id} выбрал метод оплаты: {callback.data}")
    await callback.answer()
    await callback.message.answer("Пожалуйста, подтвердите оплату:", reply_markup=get_payment_navigation_kb())
    await state.set_state(PaymentStates.waiting_for_confirmation)

@router.message(PaymentStates.waiting_for_confirmation)
async def handle_payment_confirmation(message: types.Message, state: FSMContext):
    if message.text != "Подтвердить":
        await message.answer("Пожалуйста, подтвердите оплату.")
        return
    await message.answer("Пожалуйста, отправьте скриншот оплаты.")
    await state.set_state(PaymentStates.waiting_for_screenshot)

@router.message(PaymentStates.waiting_for_screenshot)
async def handle_screenshot(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, отправьте скриншот.")
        return
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} отправил скриншот оплаты")
    await message.answer("Скриншот получен. Ожидайте подтверждения от администратора.")
    await state.clear() 