from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from bot.utils import log_user_action
from bot.keyboards import get_main_kb

router = Router()

@router.message(lambda message: message.text == "📝 Оставить отзыв")
async def handle_review_button(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} нажал кнопку Оставить отзыв")
    await message.answer("Пожалуйста, напишите ваш отзыв:")
    await state.set_state("waiting_for_review")

@router.message(lambda message: state.get_state() == "waiting_for_review")
async def handle_review_text(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} отправил отзыв: {message.text}")
    await message.answer("Спасибо за ваш отзыв!", reply_markup=get_main_kb())
    await state.clear() 