from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton

def get_start_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Старт")]],
        resize_keyboard=True
    )

def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Заказать буст"), KeyboardButton(text="⏱ Отыгрыш часов")],
            [KeyboardButton(text="🎓 Калибровка"), KeyboardButton(text="👨‍🏫 Коучинг")],
            [KeyboardButton(text="🏆 Боевой кубок"), KeyboardButton(text="💰 Цены")],
            [KeyboardButton(text="📞 Контакты"), KeyboardButton(text="⭐ Отзывы")],
            [KeyboardButton(text="📝 Оставить отзыв"), KeyboardButton(text="🛡️ Отмыва Порядочности")],
        ],
        resize_keyboard=True
    )

def get_mode_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Соло"), KeyboardButton(text="Пати")],
            [KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")],
        ],
        resize_keyboard=True
    )

def get_yes_no_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")],
            [KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")],
        ],
        resize_keyboard=True
    )

def get_mmr_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")]],
        resize_keyboard=True
    )

def get_doubles_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")]],
        resize_keyboard=True
    )

def get_behavior_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")]],
        resize_keyboard=True
    )

def get_hours_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")]],
        resize_keyboard=True
    )

def get_coaching_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")]],
        resize_keyboard=True
    )

def get_tier_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="3"), KeyboardButton(text="4")],
            [KeyboardButton(text="5"), KeyboardButton(text="6")],
            [KeyboardButton(text="7"), KeyboardButton(text="8")],
            [KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")],
        ],
        resize_keyboard=True
    )

def get_confidence_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")]],
        resize_keyboard=True
    )

def get_confirm_battle_cup_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подтвердить заказ")],
            [KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")],
        ],
        resize_keyboard=True
    )

def get_payment_navigation_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад"), KeyboardButton(text="Главное меню")]],
        resize_keyboard=True
    )

def get_payment_methods_keyboard(order_id, total_price):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌟 Telegram Stars", callback_data=f"pay_stars_{order_id}_{total_price}")],
            [InlineKeyboardButton(text="💳 Перевод на карту", callback_data=f"pay_card_{order_id}_{total_price}")],
            [InlineKeyboardButton(text="💰 Криптовалюта (USDT)", callback_data=f"pay_crypto_{order_id}_{total_price}")],
            [InlineKeyboardButton(text="📱 QIWI", callback_data=f"pay_qiwi_{order_id}_{total_price}")],
            [InlineKeyboardButton(text="🤝 Другой способ", callback_data=f"pay_other_{order_id}_{total_price}")],
        ]
    )
    return keyboard

def get_service_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="MMR Boost")],
        [KeyboardButton(text="Behavior Score")],
        [KeyboardButton(text="Hours Played")],
        [KeyboardButton(text="Calibration")],
        [KeyboardButton(text="Coaching")],
        [KeyboardButton(text="Battle Cup")],
        [KeyboardButton(text="🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True) 