from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    waiting_for_service = State()
    waiting_for_mode = State()
    waiting_for_mmr_from = State()
    waiting_for_mmr_to = State()
    waiting_for_doubles_choice = State()
    waiting_for_doubles = State()
    waiting_for_behavior_score = State()
    waiting_for_hours = State()
    waiting_for_coaching_hours = State()
    waiting_for_battle_cup_mode = State()
    waiting_for_battle_cup_tier = State()
    waiting_for_battle_cup_confirmation = State()
    waiting_for_calibration_mmr = State()
    waiting_for_calibration_confidence = State()

class PaymentStates(StatesGroup):
    waiting_for_payment_method = State()
    waiting_for_confirmation = State()
    waiting_for_screenshot = State() 