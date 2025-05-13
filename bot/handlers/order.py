from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from bot.utils import log_user_action
from bot.keyboards import (
    get_mode_kb, get_yes_no_kb, get_mmr_kb, get_doubles_kb, 
    get_behavior_kb, get_hours_kb, get_coaching_kb, get_tier_kb, 
    get_confidence_kb, get_confirm_battle_cup_kb, get_service_kb,
    get_main_kb
)
from bot.states import OrderStates
from bot.price import (
    calculate_boost_price, get_behavior_price, get_hours_price, 
    get_coaching_price, get_battle_cup_price, determine_tier, 
    calculate_calibration_progress, calculate_calibration_price
)

router = Router()

@router.message(lambda message: message.text == "🎯 Заказать буст")
async def handle_order_boost(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} нажал кнопку Заказать буст")
    await message.answer(
        "Выберите услугу:",
        reply_markup=get_service_kb()
    )
    await state.set_state(OrderStates.waiting_for_service)

@router.message(OrderStates.waiting_for_service)
async def handle_service_selection(message: types.Message, state: FSMContext):
    service = message.text
    if service not in ["MMR Boost", "Behavior Score", "Hours Played", "Calibration", "Coaching", "Battle Cup"]:
        await message.answer("Пожалуйста, выберите услугу из предложенных вариантов.")
        return
    
    await state.update_data(service=service)
    
    if service == "MMR Boost":
        await message.answer("Выберите режим буста:", reply_markup=get_mode_kb())
        await state.set_state(OrderStates.waiting_for_mode)
    elif service == "Behavior Score":
        await message.answer("Введите текущий Behavior Score:", reply_markup=get_behavior_kb())
        await state.set_state(OrderStates.waiting_for_behavior_score)
    elif service == "Hours Played":
        await message.answer("Введите количество часов для отыгрыша:", reply_markup=get_hours_kb())
        await state.set_state(OrderStates.waiting_for_hours)
    elif service == "Calibration":
        await message.answer("Введите текущий MMR:", reply_markup=get_mmr_kb())
        await state.set_state(OrderStates.waiting_for_calibration_mmr)
    elif service == "Coaching":
        await message.answer("Введите количество часов для коучинга:", reply_markup=get_coaching_kb())
        await state.set_state(OrderStates.waiting_for_coaching_hours)
    elif service == "Battle Cup":
        await message.answer("Выберите режим боевого кубка:", reply_markup=get_mode_kb())
        await state.set_state(OrderStates.waiting_for_battle_cup_mode)

# MMR Boost Flow
@router.message(OrderStates.waiting_for_mode)
async def handle_mode(message: types.Message, state: FSMContext):
    if message.text not in ["Соло", "Пати"]:
        await message.answer("Пожалуйста, выберите режим из предложенных вариантов.")
        return
    await state.update_data(mode=message.text)
    await message.answer("Введите текущий MMR:", reply_markup=get_mmr_kb())
    await state.set_state(OrderStates.waiting_for_mmr_from)

@router.message(OrderStates.waiting_for_mmr_from)
async def handle_mmr_from(message: types.Message, state: FSMContext):
    try:
        mmr = int(message.text)
        if mmr < 1:
            await message.answer("MMR должен быть положительным числом.")
            return
        await state.update_data(mmr_from=mmr)
        await message.answer("Введите желаемый MMR:", reply_markup=get_mmr_kb())
        await state.set_state(OrderStates.waiting_for_mmr_to)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

@router.message(OrderStates.waiting_for_mmr_to)
async def handle_mmr_to(message: types.Message, state: FSMContext):
    try:
        mmr = int(message.text)
        data = await state.get_data()
        if mmr <= data['mmr_from']:
            await message.answer("Желаемый MMR должен быть больше текущего.")
            return
        await state.update_data(mmr_to=mmr)
        await message.answer("Хотите использовать двойные звезды?", reply_markup=get_yes_no_kb())
        await state.set_state(OrderStates.waiting_for_doubles_choice)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

@router.message(OrderStates.waiting_for_doubles_choice)
async def handle_doubles_choice(message: types.Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        await message.answer("Пожалуйста, выберите 'Да' или 'Нет'.")
        return
    if message.text == "Да":
        await message.answer("Введите количество доступных двойных звезд:", reply_markup=get_doubles_kb())
        await state.set_state(OrderStates.waiting_for_doubles)
    else:
        await state.update_data(doubles_available=0)
        await handle_mmr_boost_completion(message, state)

@router.message(OrderStates.waiting_for_doubles)
async def handle_doubles(message: types.Message, state: FSMContext):
    try:
        doubles = int(message.text)
        if doubles < 0:
            await message.answer("Количество двойных звезд должно быть неотрицательным.")
            return
        await state.update_data(doubles_available=doubles)
        await handle_mmr_boost_completion(message, state)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

async def handle_mmr_boost_completion(message: types.Message, state: FSMContext):
    data = await state.get_data()
    price = calculate_boost_price(
        data['mmr_from'],
        data['mmr_to'],
        data['mode'],
        data.get('doubles_available', 0)
    )
    await message.answer(
        f"Заказ MMR буста подтвержден:\n"
        f"Режим: {data['mode']}\n"
        f"От {data['mmr_from']} до {data['mmr_to']} MMR\n"
        f"Двойные звезды: {data.get('doubles_available', 0)}\n"
        f"Цена: {price} руб."
    )
    await state.clear()

# Behavior Score Flow
@router.message(OrderStates.waiting_for_behavior_score)
async def handle_behavior_score(message: types.Message, state: FSMContext):
    try:
        score = int(message.text)
        if score < 0 or score > 10000:
            await message.answer("Behavior Score должен быть от 0 до 10000.")
            return
        price = get_behavior_price(score)
        await message.answer(
            f"Заказ улучшения Behavior Score подтвержден:\n"
            f"Текущий BS: {score}\n"
            f"Цена: {price} руб."
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

# Hours Played Flow
@router.message(OrderStates.waiting_for_hours)
async def handle_hours(message: types.Message, state: FSMContext):
    try:
        hours = int(message.text)
        if hours <= 0:
            await message.answer("Количество часов должно быть положительным числом.")
            return
        price = get_hours_price(hours)
        await message.answer(
            f"Заказ отыгрыша часов подтвержден:\n"
            f"Количество часов: {hours}\n"
            f"Цена: {price} руб."
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

# Coaching Flow
@router.message(OrderStates.waiting_for_coaching_hours)
async def handle_coaching_hours(message: types.Message, state: FSMContext):
    try:
        hours = int(message.text)
        if hours < 0:
            await message.answer("Количество часов должно быть неотрицательным.")
            return
        price = get_coaching_price(hours)
        await message.answer(
            f"Заказ коучинга подтвержден:\n"
            f"Количество часов: {hours}\n"
            f"Цена: {price} руб."
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

# Battle Cup Flow
@router.message(OrderStates.waiting_for_battle_cup_mode)
async def handle_battle_cup_mode(message: types.Message, state: FSMContext):
    if message.text not in ["Соло", "Пати"]:
        await message.answer("Пожалуйста, выберите режим из предложенных вариантов.")
        return
    await state.update_data(battle_cup_mode=message.text)
    await message.answer("Выберите тир боевого кубка:", reply_markup=get_tier_kb())
    await state.set_state(OrderStates.waiting_for_battle_cup_tier)

@router.message(OrderStates.waiting_for_battle_cup_tier)
async def handle_battle_cup_tier(message: types.Message, state: FSMContext):
    try:
        tier = int(message.text)
        if tier not in [3, 4, 5, 6, 7, 8]:
            await message.answer("Пожалуйста, выберите тир из предложенных вариантов.")
            return
        data = await state.get_data()
        price = get_battle_cup_price(tier, data['battle_cup_mode'])
        await message.answer(
            f"Заказ боевого кубка подтвержден:\n"
            f"Режим: {data['battle_cup_mode']}\n"
            f"Тир: {tier}\n"
            f"Цена: {price} руб."
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

# Calibration Flow
@router.message(OrderStates.waiting_for_calibration_mmr)
async def handle_calibration_mmr(message: types.Message, state: FSMContext):
    try:
        mmr = int(message.text)
        if mmr < 1:
            await message.answer("MMR должен быть положительным числом.")
            return
        await state.update_data(calibration_mmr=mmr)
        await message.answer("Введите текущий процент уверенности:", reply_markup=get_confidence_kb())
        await state.set_state(OrderStates.waiting_for_calibration_confidence)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

@router.message(OrderStates.waiting_for_calibration_confidence)
async def handle_calibration_confidence(message: types.Message, state: FSMContext):
    try:
        confidence = int(message.text)
        if confidence < 0 or confidence > 100:
            await message.answer("Процент уверенности должен быть от 0 до 100.")
            return
        data = await state.get_data()
        mmr = data['calibration_mmr']
        games_remaining, current_confidence = calculate_calibration_progress(confidence)
        price = calculate_calibration_price(games_remaining, mmr)
        await message.answer(
            f"Заказ калибровки подтвержден:\n"
            f"MMR: {mmr}\n"
            f"Осталось игр: {games_remaining}\n"
            f"Текущий процент уверенности: {current_confidence}%\n"
            f"Цена: {price} руб."
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

async def handle_back_button(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    
    if current_state == OrderStates.waiting_for_service.state:
        await message.answer("Выберите действие:", reply_markup=get_main_kb())
        await state.clear()
        return True
    
    if current_state == OrderStates.waiting_for_mode.state:
        await message.answer("Выберите услугу:", reply_markup=get_service_kb())
        await state.set_state(OrderStates.waiting_for_service)
        return True
    
    if current_state == OrderStates.waiting_for_mmr_from.state:
        await message.answer("Выберите режим буста:", reply_markup=get_mode_kb())
        await state.set_state(OrderStates.waiting_for_mode)
        return True
    
    if current_state == OrderStates.waiting_for_mmr_to.state:
        await message.answer("Введите текущий MMR:", reply_markup=get_mmr_kb())
        await state.set_state(OrderStates.waiting_for_mmr_from)
        return True
    
    if current_state == OrderStates.waiting_for_doubles_choice.state:
        await message.answer("Введите желаемый MMR:", reply_markup=get_mmr_kb())
        await state.set_state(OrderStates.waiting_for_mmr_to)
        return True
    
    if current_state == OrderStates.waiting_for_doubles.state:
        await message.answer("Хотите использовать двойные звезды?", reply_markup=get_yes_no_kb())
        await state.set_state(OrderStates.waiting_for_doubles_choice)
        return True
    
    if current_state == OrderStates.waiting_for_behavior_score.state:
        await message.answer("Выберите услугу:", reply_markup=get_service_kb())
        await state.set_state(OrderStates.waiting_for_service)
        return True
    
    if current_state == OrderStates.waiting_for_hours.state:
        await message.answer("Выберите услугу:", reply_markup=get_service_kb())
        await state.set_state(OrderStates.waiting_for_service)
        return True
    
    if current_state == OrderStates.waiting_for_coaching_hours.state:
        await message.answer("Выберите услугу:", reply_markup=get_service_kb())
        await state.set_state(OrderStates.waiting_for_service)
        return True
    
    if current_state == OrderStates.waiting_for_battle_cup_mode.state:
        await message.answer("Выберите услугу:", reply_markup=get_service_kb())
        await state.set_state(OrderStates.waiting_for_service)
        return True
    
    if current_state == OrderStates.waiting_for_battle_cup_tier.state:
        await message.answer("Выберите режим боевого кубка:", reply_markup=get_mode_kb())
        await state.set_state(OrderStates.waiting_for_battle_cup_mode)
        return True
    
    if current_state == OrderStates.waiting_for_calibration_mmr.state:
        await message.answer("Выберите услугу:", reply_markup=get_service_kb())
        await state.set_state(OrderStates.waiting_for_service)
        return True
    
    if current_state == OrderStates.waiting_for_calibration_confidence.state:
        await message.answer("Введите текущий MMR:", reply_markup=get_mmr_kb())
        await state.set_state(OrderStates.waiting_for_calibration_mmr)
        return True
    
    return False

async def handle_main_menu_button(message: types.Message, state: FSMContext):
    await message.answer("Выберите действие:", reply_markup=get_main_kb())
    await state.clear()
    return True

@router.message(lambda message: message.text in ["Назад", "Главное меню"])
async def handle_navigation(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        if await handle_back_button(message, state):
            return
    elif message.text == "Главное меню":
        if await handle_main_menu_button(message, state):
            return 