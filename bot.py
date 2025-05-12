from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import logging
import sqlite3
from datetime import datetime
import uuid
import qrcode
from io import BytesIO

# Настройки
API_TOKEN = '8124873152:AAELTs1pl1b6EFvVii7wKw9MlGEjHlfvecg'  # Ваш токен
ADMIN_ID = 977794402  # Ваш ID в Telegram

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_user_action(user: types.User, action: str):
    username = f"@{user.username}" if user.username else "(без username)"
    fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
    logging.info(f"[{user.id}] {username} ({fullname}) — {action}")


# Инициализация бота
logging.info("Инициализация бота...")
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
logging.info("Бот инициализирован")

# ================== ОПРЕДЕЛЕНИЕ СОСТОЯНИЙ ==================
class OrderStates(StatesGroup):
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

# ================== БАЗА ДАННЫХ ==================
def get_db():
    logging.info("Подключение к базе данных...")
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    logging.info("Подключение к БД выполнено")
    return conn

# Обновление схемы базы данных
def update_db_schema():
    logging.info("Обновление схемы базы данных...")
    try:
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute('PRAGMA table_info(orders)')
            columns = {row['name'] for row in cursor.fetchall()}
            
            if 'mode' not in columns:
                db.execute('ALTER TABLE orders ADD COLUMN mode TEXT DEFAULT NULL')
            
            if 'games' not in columns:
                db.execute('ALTER TABLE orders ADD COLUMN games INTEGER DEFAULT NULL')
            
            if 'doubles_used' not in columns:
                db.execute('ALTER TABLE orders ADD COLUMN doubles_used INTEGER DEFAULT 0')
            
            if 'tier' not in columns:
                db.execute('ALTER TABLE orders ADD COLUMN tier INTEGER DEFAULT NULL')
            
            if 'confidence' not in columns:
                db.execute('ALTER TABLE orders ADD COLUMN confidence INTEGER DEFAULT NULL')
            
            db.commit()
        logging.info("Схема базы данных обновлена успешно")
    except Exception as e:
        logging.error(f"Ошибка при обновлении схемы базы данных: {e}")

# Создание таблицы платежей
def update_payment_table():
    logging.info("Обновление таблицы платежей...")
    try:
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS payments
                     (id TEXT PRIMARY KEY,
                      order_id INTEGER,
                      user_id INTEGER,
                      amount REAL,
                      method TEXT,
                      status TEXT DEFAULT 'pending',
                      payment_data TEXT,
                      screenshot_file_id TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            db.commit()
        logging.info("Таблица платежей обновлена успешно")
    except Exception as e:
        logging.error(f"Ошибка при обновлении таблицы платежей: {e}")

# Создаем или обновляем таблицы при запуске
with get_db() as db:
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  mmr_from INTEGER,
                  mmr_to INTEGER,
                  mode TEXT,
                  games INTEGER,
                  doubles_used INTEGER DEFAULT 0,
                  price REAL,
                  status TEXT DEFAULT 'new',
                  payment_status TEXT DEFAULT 'pending',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  tier INTEGER DEFAULT NULL,
                  confidence INTEGER DEFAULT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  text TEXT,
                  rating INTEGER,
                  order_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    db.commit()
update_db_schema()
update_payment_table()

# ================== КЛАВИАТУРЫ ==================
start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🚀 Старт")]
    ],
    resize_keyboard=True
)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="🎯 Заказать буст"), types.KeyboardButton(text="⏱ Отыгрыш часов")],
        [types.KeyboardButton(text="🎓 Калибровка"), types.KeyboardButton(text="👨‍🏫 Коучинг")],
        [types.KeyboardButton(text="🏆 Боевой кубок"), types.KeyboardButton(text="💰 Цены")],
        [types.KeyboardButton(text="📞 Контакты"), types.KeyboardButton(text="⭐ Отзывы")],
        [types.KeyboardButton(text="📝 Оставить отзыв"), types.KeyboardButton(text="🛡️ Отмыва Порядочности")]
    ],
    resize_keyboard=True
)

mode_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Соло"), types.KeyboardButton(text="Пати")],
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

yes_no_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Да"), types.KeyboardButton(text="Нет")],
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

mmr_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

doubles_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

behavior_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

hours_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

coaching_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

tier_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="3"), types.KeyboardButton(text="4")],
        [types.KeyboardButton(text="5"), types.KeyboardButton(text="6")],
        [types.KeyboardButton(text="7"), types.KeyboardButton(text="8")],
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

confidence_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

confirm_battle_cup_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Подтвердить заказ")],
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

# Добавляем клавиатуру для этапа выбора оплаты с кнопкой "Назад"
payment_navigation_kb = ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="Назад"), types.KeyboardButton(text="Главное меню")]
    ],
    resize_keyboard=True
)

# Функция для получения клавиатуры с методами оплаты
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

# Функция для создания ID платежа
def generate_payment_id():
    return str(uuid.uuid4())

# Функция для расчета оставшихся игр и процента уверенности
def calculate_calibration_progress(confidence):
    initial_confidence = 7  # Минимальный процент уверенности
    target_confidence = 30  # Целевой процент уверенности
    total_games = 15  # Всего игр в калибровке
    
    if confidence < initial_confidence:
        confidence = initial_confidence
    
    games_played = round((confidence - initial_confidence) / 1.5)  # 1.5% за игру
    games_remaining = total_games - games_played
    current_confidence = confidence
    
    return games_remaining, current_confidence

# ================== ФУНКЦИЯ РАСЧЕТА ЦЕН ==================
def get_price_per_game(mmr):
    solo_prices = [
        (1, 2000, 95), (2000, 3000, 115), (3000, 3500, 135), (3500, 4000, 160), (4000, 4500, 180),
        (4500, 5000, 240), (5000, 5500, 290), (5500, 6000, 350), (6000, 6500, 530), (6500, 7000, 615),
        (7000, 7500, 700), (7500, 8000, 780), (8000, 8500, 880), (8500, 9000, 1050), (9000, 9500, 1250),
        (9500, 10000, 1390), (10000, 10500, 1690), (10500, 11000, 1990), (11000, 11500, 2390),
        (11500, 12000, 2790), (12000, 12500, 3390), (12500, 13000, 3990), (13000, float('inf'), 4990)
    ]
    
    solo_price_per_100_mmr = next(price for start, end, price in solo_prices if start <= mmr < end)
    solo_price_per_game = solo_price_per_100_mmr / 4  # Цена за 1 игру (соло)
    return solo_price_per_game

def calculate_boost_price(mmr_from, mmr_to, mode, doubles_available):
    mmr_gain = mmr_to - mmr_from
    if mmr_gain <= 0:
        return 0, 0, 0, "MMR должен увеличиваться"
    
    games_without_doubles = mmr_gain // 25
    if mmr_gain % 25 != 0:
        games_without_doubles += 1
    
    games_with_doubles = mmr_gain // 50
    if mmr_gain % 50 != 0:
        games_with_doubles += 1
    
    doubles_used = min(doubles_available, games_with_doubles)
    remaining_mmr = mmr_gain - (doubles_used * 50)
    additional_games = remaining_mmr // 25 if remaining_mmr > 0 else 0
    if remaining_mmr % 25 != 0:
        additional_games += 1
    
    total_games = doubles_used + additional_games
    
    base_price_per_game = get_price_per_game(mmr_from)
    
    if mode == "solo":
        price_with_doubles = doubles_used * base_price_per_game * 0.75
        price_without_doubles = additional_games * base_price_per_game
        total_price = price_with_doubles + price_without_doubles
    else:  # mode == "party"
        party_base_price = base_price_per_game * 1.5
        price_with_doubles = doubles_used * party_base_price * 1.5
        price_without_doubles = additional_games * party_base_price
        total_price = price_with_doubles + price_without_doubles
    
    return total_price, total_games, doubles_used, None

def get_behavior_price(behavior_score):
    price_ranges = [
        (0, 3000, {('all_pick', False): 50, ('turbo', False): 25}),
        (3000, 9000, {('all_pick', False): 25, ('turbo', False): 12}),
        (9000, 12000, {('all_pick', False): 15, ('turbo', False): 7})
    ]
    base_increase = next(increase for start, end, increases in price_ranges if start <= behavior_score < end)
    return base_increase.get(('all_pick', False), 0) * 100  # Примерная базовая цена

def get_hours_price(hours):
    return hours * 300  # 300 руб/час

def get_coaching_price(hours):
    return hours * 500  # 500 руб/час

def get_battle_cup_price(tier, mode):
    base_prices = {
        8: 1375,  # Титаны
        7: 700,   # Божество
        6: 600,   # Властелины
        5: 500,   # Легенды
        4: 400,   # Герои
        3: 300    # Выдари и ниже
    }
    base_price = base_prices.get(tier, 300)  # Минимальная цена для тира 3
    return base_price if mode == "solo" else base_price * 1.5  # Пати х1.5

def determine_tier(mmr):
    if mmr <= 3000:
        return 3  # Выдари и ниже
    elif mmr <= 4000:
        return 4  # Герои
    elif mmr <= 5000:
        return 5  # Легенды
    elif mmr <= 6000:
        return 6  # Властелины
    elif mmr <= 9000:
        return 7  # Божество
    else:
        return 8  # Титаны

# ================== ОСНОВНЫЕ КОМАНДЫ ==================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    log_user_action(message.from_user, f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}! 👋 Это твой личный помощник для заказа услуг по Dota 2! 🚀 Хочешь прокачать свой аккаунт, поднять MMR или получить крутые советы от профи? Я здесь, чтобы помочь! 😎\n\nОзнакомься с отзывами наших довольных клиентов:\n\n🔗 https://funpay.com/users/3140450/\n\n🔗 https://t.me/dotalevin729\n\nВыбирай услугу, пиши мне, и мы сделаем твою игру незабываемой! 💪 Готов к победам? 😏",
        reply_markup=start_kb
    )

@dp.message(F.text == "🚀 Старт")
async def handle_start_button(message: types.Message):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} нажал кнопку Старт")
    await message.answer(
        "Выберите действие:",
        reply_markup=main_kb
    )

@dp.message(F.text == "💰 Цены")
async def show_prices(message: types.Message):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} запросил цены")
    prices_text = (
        "💎 <b>Цены за 1 игру (средний прирост +25 MMR):</b>\n\n"
        "📌 <b>Соло (без даблов):</b>\n"
        "1-2000 MMR: 23.75 руб\n"
        "2000-3000 MMR: 28.75 руб\n"
        "3000-3500 MMR: 33.75 руб\n"
        "3500-4000 MMR: 40 руб\n"
        "4000-4500 MMR: 45 руб\n"
        "4500-5000 MMR: 60 руб\n"
        "5000-5500 MMR: 72.5 руб\n"
        "5500-6000 MMR: 87.5 руб\n"
        "6000-6500 MMR: 132.5 руб\n"
        "6500-7000 MMR: 153.75 руб\n"
        "7000-7500 MMR: 175 руб\n"
        "7500-8000 MMR: 195 руб\n"
        "8000-8500 MMR: 220 руб\n"
        "8500-9000 MMR: 262.5 руб\n"
        "9000-9500 MMR: 312.5 руб\n"
        "9500-10000 MMR: 347.5 руб\n"
        "10000-10500 MMR: 422.5 руб\n"
        "10500-11000 MMR: 497.5 руб\n"
        "11000-11500 MMR: 597.5 руб\n"
        "11500-12000 MMR: 697.5 руб\n"
        "12000-12500 MMR: 847.5 руб\n"
        "12500-13000 MMR: 997.5 руб\n"
        "13000+ MMR: 1247.5 руб\n\n"
        "📌 <b>Соло с даблами:</b> Скидка 25% на игры с даблами.\n\n"
        "📌 <b>Пати (без даблов):</b>\n"
        "1-2000 MMR: 35.625 руб\n"
        "2000-3000 MMR: 43.125 руб\n"
        "3000-3500 MMR: 50.625 руб\n"
        "3500-4000 MMR: 60 руб\n"
        "4000-4500 MMR: 67.5 руб\n"
        "4500-5000 MMR: 90 руб\n"
        "5000-5500 MMR: 108.75 руб\n"
        "5500-6000 MMR: 131.25 руб\n"
        "6000-6500 MMR: 198.75 руб\n"
        "6500-7000 MMR: 230.625 руб\n"
        "7000-7500 MMR: 262.5 руб\n"
        "7500-8000 MMR: 292.5 руб\n"
        "8000-8500 MMR: 330 руб\n"
        "8500-9000 MMR: 393.75 руб\n"
        "9000-9500 MMR: 468.75 руб\n"
        "9500-10000 MMR: 521.25 руб\n"
        "10000-10500 MMR: 633.75 руб\n"
        "10500-11000 MMR: 746.25 руб\n"
        "11000-11500 MMR: 896.25 руб\n"
        "11500-12000 MMR: 1046.25 руб\n"
        "12000-12500 MMR: 1271.25 руб\n"
        "12500-13000 MMR: 1496.25 руб\n"
        "13000+ MMR: 1871.25 руб\n\n"
        "📌 <b>Пати с даблами:</b> +50% к цене пати на игры с даблами.\n\n"
        "🛡️ <b>Отмыва Порядочности:</b>\n"
        "1-3000 MMR: +5000 (All Pick), +2500 (Turbo)\n"
        "3000-9000 MMR: +2500 (All Pick), +1200 (Turbo)\n"
        "9000-12000 MMR: +1500 (All Pick), +700 (Turbo)\n\n"
        "⏱ <b>Отыгрыш часов:</b>\n"
        "1 час: 300 руб\n\n"
        "🎓 <b>Калибровка:</b>\n"
        "Полный цикл (15 игр): 1500 руб\n\n"
        "👨‍🏫 <b>Коучинг:</b>\n"
        "1 час: 500 руб\n\n"
        "🏆 <b>Боевой кубок:</b>\n"
        "Соло:\n"
        "Тир 3: 300 руб\n"
        "Тир 4: 400 руб\n"
        "Тир 5: 500 руб\n"
        "Тир 6: 600 руб\n"
        "Тир 7: 700 руб\n"
        "Тир 8: 1375 руб\n"
        "Пати (х1.5 от соло):\n"
        "Тир 3: 450 руб\n"
        "Тир 4: 600 руб\n"
        "Тир 5: 750 руб\n"
        "Тир 6: 900 руб\n"
        "Тир 7: 1050 руб\n"
        "Тир 8: 2062.50 руб\n\n"
        "📩 Узнай точную цену, выбрав режим буста!"
    )
    await message.answer(prices_text, reply_markup=main_kb)

@dp.message(F.text == "📞 Контакты")
async def show_contacts(message: types.Message):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} запросил контакты")
    await message.answer(
        "📩 По всем вопросам:\n"
        "@levin729\n\n"
        "⏱ Режим работы: 10:00 - 22:00 (МСК)",
        reply_markup=main_kb
    )

@dp.message(F.text == "⭐ Отзывы")
async def show_reviews(message: types.Message):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} запросил отзывы")
    await message.answer(
        "⭐ <b>Отзывы</b>\n\n"
        "Посмотрите отзывы о нашей работе в нашем Telegram-канале:\n"
        "<a href='https://t.me/dotalevin729'>@dotalevin729</a>\n\n"
        "Также вы можете оставить свой отзыв, выбрав «📝 Оставить отзыв».",
        reply_markup=main_kb
    )

# Обработчик для кнопки "Главное меню" на всех этапах
@dp.message(F.text == "Главное меню")
async def return_to_main_menu(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} вернулся в главное меню")
    await state.clear()
    await message.answer("Возвращаемся в главное меню.", reply_markup=main_kb)

# ================== СИСТЕМА ЗАКАЗОВ ==================
@dp.message(F.text == "🎯 Заказать буст")
async def order_start(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Начат процесс заказа буста пользователем {message.from_user.id}")
    mmr_image_url = "https://ru.files.fm/down.php?i=dxrjb59nkv"
    logging.info(f"Попытка загрузки изображения для Заказать буст: {mmr_image_url}")
    try:
        await message.answer_photo(
            photo=mmr_image_url,
            caption="📊 Вот таблица с диапазонами MMR, чтобы вам было проще выбрать желаемый рейтинг.\n\nВыбери режим буста:",
            reply_markup=mode_kb
        )
        await state.set_state(OrderStates.waiting_for_mode)
    except Exception as e:
        logging.error(f"Ошибка при загрузке изображения для Заказать буст: {e}")
        await message.answer(
            "📊 Не удалось загрузить таблицу с диапазонами MMR. Вы можете посмотреть её по ссылке: https://ru.files.fm/down.php?i=dxrjb59nkv\n\nВыбери режим буста:",
            reply_markup=mode_kb
        )
        await state.set_state(OrderStates.waiting_for_mode)

@dp.message(StateFilter(OrderStates.waiting_for_mode))
async def select_mode(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} выбрал режим: {message.text}")
    if message.text == "Назад":
        log_user_action(message.from_user, f"Пользователь {message.from_user.id} нажал Назад на этапе выбора режима")
        await state.clear()
        await message.answer("Возвращаемся в главное меню.", reply_markup=main_kb)
        return
    if message.text not in ["Соло", "Пати"]:
        await message.answer("❌ Пожалуйста, выберите режим (Соло/Пати) или нажмите Назад.", reply_markup=mode_kb)
        return
    mode = "solo" if message.text.lower() == "соло" else "party"  # Приводим к стандартным значениям
    await state.update_data(mode=mode)
    if mode == "party":
        await message.answer("Хотите использовать дабл дауны? (Да/Нет)", reply_markup=yes_no_kb)
        await state.set_state(OrderStates.waiting_for_doubles_choice)
    else:
        await message.answer("Введите текущий MMR (например, 3500):", reply_markup=mmr_kb)
        await state.set_state(OrderStates.waiting_for_mmr_from)

@dp.message(StateFilter(OrderStates.waiting_for_doubles_choice))
async def process_doubles_choice(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} выбрал использование даблов: {message.text}")
    if message.text == "Назад":
        log_user_action(message.from_user, f"Пользователь {message.from_user.id} нажал Назад на этапе выбора даблов")
        await message.answer("Выбери режим буста:", reply_markup=mode_kb)
        await state.set_state(OrderStates.waiting_for_mode)
        return
    if message.text not in ["Да", "Нет"]:
        await message.answer("❌ Пожалуйста, выберите Да или Нет, или нажмите Назад.", reply_markup=yes_no_kb)
        return
    if message.text == "Да":
        await message.answer("Сколько у вас дабл даунов? (например, 5, введите 0, если нет):", reply_markup=doubles_kb)
        await state.set_state(OrderStates.waiting_for_doubles)
    else:
        await message.answer("Введите текущий MMR (например, 3500):", reply_markup=mmr_kb)
        await state.set_state(OrderStates.waiting_for_mmr_from)

@dp.message(StateFilter(OrderStates.waiting_for_mmr_from), F.text.regexp(r'^\d{1,5}$'))
async def process_mmr_from(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получен начальный MMR от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Назад":
        data = await state.get_data()
        if data.get("mode") == "пати":
            await message.answer("Хотите использовать дабл дауны? (Да/Нет)", reply_markup=yes_no_kb)
            await state.set_state(OrderStates.waiting_for_doubles_choice)
        else:
            await message.answer("Выбери режим буста:", reply_markup=mode_kb)
            await state.set_state(OrderStates.waiting_for_mode)
        return
    try:
        mmr_from = int(message.text)
        if mmr_from < 1 or mmr_from > 13000:
            raise ValueError
        await message.answer("Введите желаемый MMR (например, 4000):", reply_markup=mmr_kb)
        await state.set_state(OrderStates.waiting_for_mmr_to)
        await state.update_data(mmr_from=mmr_from)
    except ValueError:
        await message.answer("❌ Введите корректный MMR (число от 1 до 13000).", reply_markup=mmr_kb)
        return

@dp.message(StateFilter(OrderStates.waiting_for_mmr_to), F.text.regexp(r'^\d{1,5}$'))
async def process_mmr_to(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получен конечный MMR от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Назад":
        await message.answer("Введите текущий MMR (например, 3500):", reply_markup=mmr_kb)
        await state.set_state(OrderStates.waiting_for_mmr_from)
        return
    try:
        mmr_to = int(message.text)
        data = await state.get_data()
        mmr_from = data["mmr_from"]
        mode = data["mode"]
        if mmr_to <= mmr_from:
            await message.answer("❌ Желаемый MMR должен быть больше текущего.", reply_markup=mmr_kb)
            return

        # Расчёт цены и игр
        total_price, total_games, doubles_used, error = calculate_boost_price(mmr_from, mmr_to, mode, 0)
        if error:
            await message.answer(f"❌ {error}", reply_markup=mmr_kb)
            return

        # Сохранение заказа в базе данных
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO orders (user_id, username, mmr_from, mmr_to, mode, games, doubles_used, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (message.from_user.id, message.from_user.username, mmr_from, mmr_to, mode, total_games, doubles_used, total_price)
            )
            db.commit()
            order_id = cursor.lastrowid

        # Формирование итогового сообщения
        await message.answer(
            f"🛒 <b>Заказ #{order_id} создан</b>\n\n"
            f"MMR: {mmr_from} → {mmr_to}\n"
            f"Режим: {'Соло' if mode == 'solo' else 'Пати'}\n"
            f"Всего игр: {total_games}\n\n"
            f"Общая стоимость: <b>{total_price:.2f} руб.</b>\n\n"
            f"Выберите способ оплаты или нажмите «Назад», чтобы отменить заказ:",
            reply_markup=get_payment_methods_keyboard(order_id, total_price)
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите корректный MMR (число от 1 до 13000).", reply_markup=mmr_kb)
        return

@dp.message(StateFilter(OrderStates.waiting_for_doubles), F.text.regexp(r'^\d+$'))
async def process_doubles(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получено количество даблов от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Назад":
        if (await state.get_data()).get("mode") == "пати":
            await message.answer("Хотите использовать дабл дауны? (Да/Нет)", reply_markup=yes_no_kb)
            await state.set_state(OrderStates.waiting_for_doubles_choice)
        else:
            await message.answer("Введите желаемый MMR (например, 4000):", reply_markup=mmr_kb)
            await state.set_state(OrderStates.waiting_for_mmr_to)
        return
    try:
        doubles = int(message.text)
        if doubles < 0:
            raise ValueError
        data = await state.get_data()
        mmr_from, mmr_to, mode = data["mmr_from"], data["mmr_to"], data["mode"]
        
        total_price, total_games, doubles_used, error = calculate_boost_price(mmr_from, mmr_to, mode, doubles)
        if error:
            await message.answer(f"❌ {error}", reply_markup=doubles_kb)
            return
        
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO orders (user_id, username, mmr_from, mmr_to, mode, games, doubles_used, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (message.from_user.id, message.from_user.username, mmr_from, mmr_to, mode, total_games, doubles_used, total_price)
            )
            db.commit()
            order_id = cursor.lastrowid
        
        doubles_text = f"\nИспользовано даблов: {doubles_used}" if doubles_used > 0 else ""
        await message.answer(
            f"🛒 <b>Заказ #{order_id} создан</b>\n\n"
            f"MMR: {mmr_from} → {mmr_to}\n"
            f"Режим: {'Соло' if mode == 'solo' else 'Пати'}\n"
            f"Всего игр: {total_games}{doubles_text}\n\n"
            f"Общая стоимость: <b>{total_price:.2f} руб.</b>\n\n"
            f"Выберите способ оплаты или нажмите «Назад», чтобы отменить заказ:",
            reply_markup=get_payment_methods_keyboard(order_id, total_price),
            reply_markup_keyboard=payment_navigation_kb
        )
        
        await state.update_data(order_id=order_id, doubles=doubles)
        await state.set_state(PaymentStates.waiting_for_payment_method)
    except ValueError:
        await message.answer("❌ Введите корректное количество даблов (число >= 0).", reply_markup=doubles_kb)
        return

# ================== ОТМЫВА ПОРЯДОЧНОСТИ ==================
@dp.message(F.text == "🛡️ Отмыва Порядочности")
async def order_behavior_score(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} начал заказ отмывки порядочности")
    behavior_image_url = "https://ru.files.fm/down.php?i=njkuubrw4z"
    logging.info(f"Попытка загрузки изображения для Отмыва порядочности: {behavior_image_url}")
    try:
        await message.answer_photo(
            photo=behavior_image_url,
            caption=(
                "📋 <b>Поднимаем порядочность</b>\n\n"
                "Посмотрите таблицу выше, чтобы понять, сколько порядочности вы получите.\n"
                "• После завершения заказа отмывания порядочности будет предложено оставить отзыв (аналогично другим услугам).\n\n"
                "Введите текущий уровень порядочности (например, 3000):"
            ),
            reply_markup=behavior_kb
        )
        await state.set_state(OrderStates.waiting_for_behavior_score)
    except Exception as e:
        logging.error(f"Ошибка при загрузке изображения для Отмыва порядочности: {e}")
        await message.answer(
            "📋 <b>Поднимаем порядочность</b>\n\n"
            "Не удалось загрузить таблицу. Вы можете посмотреть её по ссылке: https://ru.files.fm/down.php?i=njkuubrw4z\n"
            "• После завершения заказа отмывания порядочности будет предложено оставить отзыв (аналогично другим услугам).\n\n"
            "Введите текущий уровень порядочности (например, 3000):",
            reply_markup=behavior_kb
        )
        await state.set_state(OrderStates.waiting_for_behavior_score)

@dp.message(StateFilter(OrderStates.waiting_for_behavior_score))
async def process_behavior_score(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получен уровень порядочности от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Назад":
        log_user_action(message.from_user, f"Пользователь {message.from_user.id} нажал Назад на этапе ввода порядочности")
        await state.clear()
        await message.answer("Возвращаемся в главное меню.", reply_markup=main_kb)
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите корректный уровень порядочности (число от 0 до 12000).", reply_markup=behavior_kb)
        return
    try:
        behavior_score = int(message.text)
        if behavior_score < 0 or behavior_score > 12000:
            raise ValueError
        total_price = get_behavior_price(behavior_score)
        
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO orders (user_id, username, mmr_from, mmr_to, mode, price) VALUES (?, ?, ?, ?, ?, ?)",
                (message.from_user.id, message.from_user.username, behavior_score, 10000, "behavior_score", total_price)
            )
            db.commit()
            order_id = cursor.lastrowid
        
        await message.answer(
            f"🛒 <b>Заказ #{order_id} создан</b>\n\n"
            f"Порядочность: {behavior_score} → 10000\n"
            f"Общая стоимость: <b>{total_price:.2f} руб.</b>\n\n"
            f"Выберите способ оплаты или нажмите «Назад», чтобы отменить заказ:",
            reply_markup=get_payment_methods_keyboard(order_id, total_price),
            reply_markup_keyboard=payment_navigation_kb
        )
        
        await state.update_data(order_id=order_id)
        await state.set_state(PaymentStates.waiting_for_payment_method)
    except ValueError:
        await message.answer("❌ Введите корректный уровень порядочности (число от 0 до 12000).", reply_markup=behavior_kb)
        return

# ================== ОТЫГРЫШ ЧАСОВ ==================
@dp.message(F.text == "⏱ Отыгрыш часов")
async def order_hours(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} начал заказ отыгрыша часов")
    await message.answer("Сколько часов нужно отыграть? (например, 5):", reply_markup=hours_kb)
    await state.set_state(OrderStates.waiting_for_hours)

@dp.message(StateFilter(OrderStates.waiting_for_hours))
async def process_hours(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получено количество часов от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Назад":
        await state.clear()
        await message.answer("Возвращаемся в главное меню.", reply_markup=main_kb)
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите корректное количество часов (число больше 0).", reply_markup=hours_kb)
        return
    try:
        hours = int(message.text)
        if hours < 1:
            raise ValueError
        total_price = get_hours_price(hours)
        
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO orders (user_id, username, mode, games, price) VALUES (?, ?, ?, ?, ?)",
                (message.from_user.id, message.from_user.username, "hours", hours, total_price)
            )
            db.commit()
            order_id = cursor.lastrowid
        
        await message.answer(
            f"🛒 <b>Заказ #{order_id} создан</b>\n\n"
            f"Отыгрыш часов: {hours} ч\n"
            f"Общая стоимость: <b>{total_price:.2f} руб.</b>\n\n"
            f"Выберите способ оплаты или нажмите «Назад», чтобы отменить заказ:",
            reply_markup=get_payment_methods_keyboard(order_id, total_price),
            reply_markup_keyboard=payment_navigation_kb
        )
        
        await state.update_data(order_id=order_id)
        await state.set_state(PaymentStates.waiting_for_payment_method)
    except ValueError:
        await message.answer("❌ Введите корректное количество часов (число больше 0).", reply_markup=hours_kb)
        return

# ================== КАЛИБРОВКА ==================
@dp.message(F.text == "🎓 Калибровка")
async def order_calibration(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} начал заказ калибровки")
    await message.answer("Введите ваш текущий MMR (например, 3500):", reply_markup=mmr_kb)
    await state.set_state(OrderStates.waiting_for_calibration_mmr)

@dp.message(StateFilter(OrderStates.waiting_for_calibration_mmr))
async def process_calibration_mmr(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получен MMR для калибровки от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Назад":
        await state.clear()
        await message.answer("Возвращаемся в главное меню.", reply_markup=main_kb)
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите корректный MMR (число от 1 до 13000).", reply_markup=mmr_kb)
        return
    try:
        mmr = int(message.text)
        if mmr < 1 or mmr > 13000:
            raise ValueError
        await state.update_data(mmr_from=mmr)
        await message.answer("Введите текущий процент уверенности (например, 50):", reply_markup=confidence_kb)
        await state.set_state(OrderStates.waiting_for_calibration_confidence)
    except ValueError:
        await message.answer("❌ Введите корректный MMR (число от 1 до 13000).", reply_markup=mmr_kb)
        return

@dp.message(StateFilter(OrderStates.waiting_for_calibration_confidence))
async def process_calibration_confidence(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получен процент уверенности от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Назад":
        await message.answer("Введите ваш текущий MMR (например, 3500):", reply_markup=mmr_kb)
        await state.set_state(OrderStates.waiting_for_calibration_mmr)
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите корректный процент уверенности (число от 0 до 100).", reply_markup=confidence_kb)
        return
    try:
        confidence = int(message.text)
        if confidence < 0 or confidence > 100:
            raise ValueError
        
        total_games = 15  # Калибровка всегда 15 игр
        total_price = 1500  # Фиксированная цена за калибровку
        initial_confidence = 7  # Процент уверенности падает до 7%
        
        data = await state.get_data()
        mmr = data["mmr_from"]
        
        # Рассчитываем прогресс калибровки
        games_remaining, current_confidence = calculate_calibration_progress(confidence)
        
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO orders (user_id, username, mode, mmr_from, games, price, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (message.from_user.id, message.from_user.username, "calibration", mmr, total_games, total_price, confidence)
            )
            db.commit()
            order_id = cursor.lastrowid
        
        progress_text = (
            f"Ваш процент уверенности снизится до {initial_confidence}%.\n"
            f"Калибровка завершится, когда процент достигнет 30%.\n"
            f"Текущий процент: {current_confidence}%\n"
            f"Осталось игр: {games_remaining}\n"
        )
        
        await message.answer(
            f"🛒 <b>Заказ #{order_id} создан</b>\n\n"
            f"Калибровка: 15 игр\n"
            f"MMR: {mmr}\n"
            f"{progress_text}\n"
            f"Общая стоимость: <b>{total_price:.2f} руб.</b>\n\n"
            f"Выберите способ оплаты или нажмите «Назад», чтобы отменить заказ:",
            reply_markup=get_payment_methods_keyboard(order_id, total_price),
            reply_markup_keyboard=payment_navigation_kb
        )
        
        await state.update_data(order_id=order_id)
        await state.set_state(PaymentStates.waiting_for_payment_method)
    except ValueError:
        await message.answer("❌ Введите корректный процент уверенности (число от 0 до 100).", reply_markup=confidence_kb)
        return

# ================== КОУЧИНГ ==================
@dp.message(F.text == "👨‍🏫 Коучинг")
async def order_coaching(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} начал заказ коучинга")
    await message.answer("Сколько часов коучинга нужно? (например, 2):", reply_markup=coaching_kb)
    await state.set_state(OrderStates.waiting_for_coaching_hours)

@dp.message(StateFilter(OrderStates.waiting_for_coaching_hours))
async def process_coaching_hours(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получено количество часов коучинга от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Назад":
        await state.clear()
        await message.answer("Возвращаемся в главное меню.", reply_markup=main_kb)
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите корректное количество часов (число больше 0).", reply_markup=coaching_kb)
        return
    try:
        hours = int(message.text)
        if hours < 1:
            raise ValueError
        total_price = get_coaching_price(hours)
        
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO orders (user_id, username, mode, games, price) VALUES (?, ?, ?, ?, ?)",
                (message.from_user.id, message.from_user.username, "coaching", hours, total_price)
            )
            db.commit()
            order_id = cursor.lastrowid
        
        await message.answer(
            f"🛒 <b>Заказ #{order_id} создан</b>\n\n"
            f"Коучинг: {hours} ч\n"
            f"Общая стоимость: <b>{total_price:.2f} руб.</b>\n\n"
            f"Выберите способ оплаты или нажмите «Назад», чтобы отменить заказ:",
            reply_markup=get_payment_methods_keyboard(order_id, total_price),
            reply_markup_keyboard=payment_navigation_kb
        )
        
        await state.update_data(order_id=order_id)
        await state.set_state(PaymentStates.waiting_for_payment_method)
    except ValueError:
        await message.answer("❌ Введите корректное количество часов (число больше 0).", reply_markup=coaching_kb)
        return

# ================== БОЕВОЙ КУБОК ==================
@dp.message(F.text == "🏆 Боевой кубок")
async def order_battle_cup(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} начал заказ боевого кубка")
    await message.answer("Выберите режим для боевого кубка:", reply_markup=mode_kb)
    await state.set_state(OrderStates.waiting_for_battle_cup_mode)

@dp.message(StateFilter(OrderStates.waiting_for_battle_cup_mode))
async def process_battle_cup_mode(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} выбрал режим для боевого кубка: {message.text}")
    if message.text == "Назад":
        await state.clear()
        await message.answer("Возвращаемся в главное меню.", reply_markup=main_kb)
        return
    if message.text not in ["Соло", "Пати"]:
        await message.answer("❌ Пожалуйста, выберите режим (Соло/Пати) или нажмите Назад.", reply_markup=mode_kb)
        return
    mode = message.text.lower()
    await state.update_data(mode=mode)
    await message.answer("Укажите ваш текущий тир (3-8) или введите ваш текущий MMR (например, 3500):", reply_markup=tier_kb)
    await state.set_state(OrderStates.waiting_for_battle_cup_tier)

@dp.message(StateFilter(OrderStates.waiting_for_battle_cup_tier))
async def process_battle_cup_tier_by_mmr(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получен MMR для определения тира от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Назад":
        await message.answer("Выберите режим для боевого кубка:", reply_markup=mode_kb)
        await state.set_state(OrderStates.waiting_for_battle_cup_mode)
        return
    if not message.text.isdigit():
        await message.answer("❌ Введите корректный MMR (число от 1 до 13000) или выберите тир (3-8).", reply_markup=tier_kb)
        return
    try:
        mmr = int(message.text)
        if mmr < 1 or mmr > 13000:
            raise ValueError
        tier = determine_tier(mmr)
        data = await state.get_data()
        mode = data["mode"]
        total_price = get_battle_cup_price(tier, mode)
        
        await state.update_data(mmr=mmr, tier=tier, total_price=total_price)
        
        await message.answer(
            f"📋 <b>Подтверждение заказа</b>\n\n"
            f"Боевой кубок: участие\n"
            f"Режим: {'Соло' if mode == 'solo' else 'Пати'}\n"
            f"Тир: {tier}\n"
            f"MMR: {mmr}\n"
            f"Общая стоимость: <b>{total_price:.2f} руб.</b>\n\n"
            f"Подтвердите заказ или вернитесь назад:",
            reply_markup=confirm_battle_cup_kb
        )
        await state.set_state(OrderStates.waiting_for_battle_cup_confirmation)
    except ValueError:
        await message.answer("❌ Введите корректный MMR (число от 1 до 13000).", reply_markup=tier_kb)
        return

@dp.message(StateFilter(OrderStates.waiting_for_battle_cup_tier), F.text.regexp(r'^(3|4|5|6|7|8)$'))
async def process_battle_cup_tier_direct(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получен тир для боевого кубка от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Назад":
        await message.answer("Выберите режим для боевого кубка:", reply_markup=mode_kb)
        await state.set_state(OrderStates.waiting_for_battle_cup_mode)
        return
    try:
        tier = int(message.text)
        if tier < 3 or tier > 8:
            raise ValueError
        data = await state.get_data()
        mode = data["mode"]
        total_price = get_battle_cup_price(tier, mode)
        
        await state.update_data(tier=tier, total_price=total_price)
        
        await message.answer(
            f"📋 <b>Подтверждение заказа</b>\n\n"
            f"Боевой кубок: участие\n"
            f"Режим: {'Соло' if mode == 'solo' else 'Пати'}\n"
            f"Тир: {tier}\n"
            f"Общая стоимость: <b>{total_price:.2f} руб.</b>\n\n"
            f"Подтвердите заказ или вернитесь назад:",
            reply_markup=confirm_battle_cup_kb
        )
        await state.set_state(OrderStates.waiting_for_battle_cup_confirmation)
    except ValueError:
        await message.answer("❌ Введите корректный тир (число от 3 до 8).", reply_markup=tier_kb)
        return

@dp.message(StateFilter(OrderStates.waiting_for_battle_cup_confirmation))
async def confirm_battle_cup_order(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} подтвердил заказ боевого кубка: {message.text}")
    if message.text == "Назад":
        await message.answer("Укажите ваш текущий тир (3-8) или введите ваш текущий MMR (например, 3500):", reply_markup=tier_kb)
        await state.set_state(OrderStates.waiting_for_battle_cup_tier)
        return
    
    if message.text != "Подтвердить заказ":
        await message.answer("Пожалуйста, подтвердите заказ или вернитесь назад.", reply_markup=confirm_battle_cup_kb)
        return
    
    data = await state.get_data()
    mode = data["mode"]
    tier = data["tier"]
    total_price = data["total_price"]
    mmr = data.get("mmr", None)
    
    with get_db() as db:
        cursor = db.cursor()
        if mmr:
            cursor.execute(
                "INSERT INTO orders (user_id, username, mode, mmr_from, price, tier) VALUES (?, ?, ?, ?, ?, ?)",
                (message.from_user.id, message.from_user.username, f"battle_cup_{mode}", mmr, total_price, tier)
            )
        else:
            cursor.execute(
                "INSERT INTO orders (user_id, username, mode, price, tier) VALUES (?, ?, ?, ?, ?)",
                (message.from_user.id, message.from_user.username, f"battle_cup_{mode}", total_price, tier)
            )
        db.commit()
        order_id = cursor.lastrowid
    
    mmr_text = f"MMR: {mmr}\n" if mmr else ""
    await message.answer(
        f"🛒 <b>Заказ #{order_id} создан</b>\n\n"
        f"Боевой кубок: участие\n"
        f"Режим: {'Соло' if mode == 'solo' else 'Пати'}\n"
        f"Тир: {tier}\n"
        f"{mmr_text}"
        f"Общая стоимость: <b>{total_price:.2f} руб.</b>\n\n"
        f"Выберите способ оплаты или нажмите «Назад», чтобы отменить заказ:",
        reply_markup=get_payment_methods_keyboard(order_id, total_price),
        reply_markup_keyboard=payment_navigation_kb
    )
    
    await state.update_data(order_id=order_id)
    await state.set_state(PaymentStates.waiting_for_payment_method)

# ================== Обработка кнопки "Назад" на этапе выбора оплаты ==================
@dp.message(StateFilter(PaymentStates.waiting_for_payment_method), F.text == "Назад")
async def cancel_order_on_payment(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} нажал Назад на этапе выбора оплаты")
    data = await state.get_data()
    order_id = data.get("order_id")
    
    # Удаляем заказ из базы данных
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        db.commit()
    
    # Определяем, откуда пользователь пришел, и возвращаем его на предыдущий шаг
    mode = data.get("mode") or ""  # <-- теперь mode всегда строка
    
    if "battle_cup" in mode:
        await message.answer(
            "Заказ отменен. Укажите ваш текущий тир (3-8) или введите ваш текущий MMR (например, 3500):",
            reply_markup=tier_kb
        )
        await state.set_state(OrderStates.waiting_for_battle_cup_tier)
    elif mode == "behavior_score":
        await message.answer(
            "Заказ отменен. Введите текущий уровень порядочности (например, 3000):",
            reply_markup=behavior_kb
        )
        await state.set_state(OrderStates.waiting_for_behavior_score)
    elif mode == "hours":
        await message.answer(
            "Заказ отменен. Сколько часов нужно отыграть? (например, 5):",
            reply_markup=hours_kb
        )
        await state.set_state(OrderStates.waiting_for_hours)
    elif mode == "calibration":
        await message.answer(
            "Заказ отменен. Введите текущий процент уверенности (например, 50):",
            reply_markup=confidence_kb
        )
        await state.set_state(OrderStates.waiting_for_calibration_confidence)
    elif mode == "coaching":
        await message.answer(
            "Заказ отменен. Сколько часов коучинга нужно? (например, 2):",
            reply_markup=coaching_kb
        )
        await state.set_state(OrderStates.waiting_for_coaching_hours)
    elif mode == "solo":
        await message.answer(
            "Заказ отменен. Сколько у вас дабл даунов? (например, 5, введите 0, если нет):",
            reply_markup=doubles_kb
        )
        await state.set_state(OrderStates.waiting_for_doubles)
    elif mode == "party":
        mmr_to = data.get("mmr_to")
        if mmr_to:  # Если пользователь уже ввел mmr_to, возвращаем на шаг ввода даблов
            await message.answer(
                "Заказ отменен. Сколько у вас дабл даунов? (например, 5, введите 0, если нет):",
                reply_markup=doubles_kb
            )
            await state.set_state(OrderStates.waiting_for_doubles)
        else:  # Иначе возвращаем на выбор использования даблов
            await message.answer(
                "Заказ отменен. Хотите использовать дабл дауны? (Да/Нет)",
                reply_markup=yes_no_kb
            )
            await state.set_state(OrderStates.waiting_for_doubles_choice)
    else:
        await message.answer(
            "Заказ отменен. Выберите действие:",
            reply_markup=main_kb
        )
        await state.clear()

# ================== СИСТЕМА ОПЛАТЫ ==================
@dp.callback_query(F.data.startswith("pay_"))
async def process_payment_method(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Обработка выбора метода оплаты: {callback.data}")
    method = callback.data.split("_")[1]
    order_id = callback.data.split("_")[2]
    total_price = float(callback.data.split("_")[3])
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
    
    await state.update_data(order_id=order_id, amount=total_price)
    
    if method == "stars":
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Буст MMR #{order_id}",
            description=f"MMR: {order['mmr_from']} → {order['mmr_to']}\nРежим: {'Соло' if order['mode'] == 'solo' else 'Пати'}\nИгры: {order['games']}",
            payload=f"order_{order_id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Буст", amount=int(total_price))],
            need_email=False,
            need_phone_number=False,
            send_email_to_provider=False,
            send_phone_number_to_provider=False
        )
        await callback.message.delete()
    
    else:
        payment_id = generate_payment_id()
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO payments (id, order_id, user_id, amount, method) VALUES (?, ?, ?, ?, ?)",
                (payment_id, order_id, callback.from_user.id, total_price, method)
            )
            db.commit()
        
        if method == "card":
            card_number = "2200 7017 2578 8654"
            card_holder = "Данил"
            payment_data = f"{card_number}|{card_holder}"
            
            with get_db() as db:
                cursor = db.cursor()
                cursor.execute("UPDATE payments SET payment_data = ? WHERE id = ?", (payment_data, payment_id))
                db.commit()
            
            confirm_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"confirm_{payment_id}")],
                    [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_{payment_id}")],
                ]
            )
            
            await callback.message.edit_text(
                f"💳 <b>Оплата переводом на карту</b>\n\n"
                f"Номер карты: <code>{card_number}</code>\n"
                f"Получатель: {card_holder}\n\n"
                f"Сумма к оплате: <b>{total_price} руб.</b>\n\n"
                f"После оплаты нажмите кнопку «✅ Я оплатил»",
                reply_markup=confirm_kb
            )
        
        elif method == "crypto":
            wallet_address = "TS8JHytwXpsS2NZ1TRVnkqFxQqCZUkLQPP"
            payment_data = wallet_address
            
            with get_db() as db:
                cursor = db.cursor()
                cursor.execute("UPDATE payments SET payment_data = ? WHERE id = ?", (payment_data, payment_id))
                db.commit()
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(wallet_address)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            bio = BytesIO()
            bio.name = 'qr.png'
            img.save(bio, 'PNG')
            bio.seek(0)
            
            qr_message = await callback.message.answer_photo(
                photo=types.BufferedInputFile(bio.getvalue(), filename='qr.png'),
                caption=f"💰 <b>Оплата криптовалютой (USDT TRC20)</b>\n\n"
                       f"Адрес: <code>{wallet_address}</code>\n\n"
                       f"Сумма: <b>{total_price} руб.</b> (эквивалент в USDT)\n\n"
                       f"После оплаты нажмите кнопку «✅ Я оплатил»"
            )
            
            confirm_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"confirm_{payment_id}")],
                    [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_{payment_id}")],
                ]
            )
            
            await callback.message.edit_text(
                f"💰 <b>Оплата криптовалютой (USDT TRC20)</b>\n\n"
                f"QR-код отправлен выше.\n"
                f"Адрес: <code>{wallet_address}</code>\n\n"
                f"Сумма: <b>{total_price} руб.</b> (эквивалент в USDT)\n\n"
                f"После оплаты нажмите кнопку «✅ Я оплатил»",
                reply_markup=confirm_kb
            )
        
        elif method == "qiwi":
            qiwi_number = "+79123456789"
            payment_data = qiwi_number
            
            with get_db() as db:
                cursor = db.cursor()
                cursor.execute("UPDATE payments SET payment_data = ? WHERE id = ?", (payment_data, payment_id))
                db.commit()
            
            confirm_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"confirm_{payment_id}")],
                    [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_{payment_id}")],
                ]
            )
            
            await callback.message.edit_text(
                f"📱 <b>Оплата через QIWI</b>\n\n"
                f"Номер QIWI: <code>{qiwi_number}</code>\n\n"
                f"Сумма к оплате: <b>{total_price} руб.</b>\n\n"
                f"После оплаты нажмите кнопку «✅ Я оплатил»",
                reply_markup=confirm_kb
            )
        
        elif method == "other":
            admin_username = "levin729"
            await callback.message.edit_text(
                f"🤝 <b>Другие способы оплаты</b>\n\n"
                f"Напишите администратору @{admin_username} для обсуждения других способов оплаты.\n\n"
                f"Укажите номер заказа: <b>#{order_id}</b>\n"
                f"Сумма к оплате: <b>{total_price} руб.</b>"
            )
    
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Обработка подтверждения оплаты: {callback.data}")
    payment_id = callback.data.split("_")[1]
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        payment = cursor.fetchone()
    
    await callback.message.edit_text(
        "📸 <b>Загрузите скриншот подтверждения оплаты</b>\n\n"
        "Пожалуйста, отправьте скриншот вашей оплаты для проверки."
    )
    
    await state.set_state(PaymentStates.waiting_for_screenshot)
    await state.update_data(payment_id=payment_id)
    await callback.answer()

@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    logging.info(f"Обработка отмены оплаты: {callback.data}")
    payment_id = callback.data.split("_")[1]
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        payment = cursor.fetchone()
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        payment = cursor.fetchone()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (payment['order_id'],))
        order = cursor.fetchone()
        
        cursor.execute("UPDATE payments SET status = 'cancelled' WHERE id = ?", (payment_id,))
        cursor.execute("DELETE FROM orders WHERE id = ?", (order['id'],))
        db.commit()
    
    await callback.message.edit_text(
        "❌ <b>Оплата отменена</b>\n\n"
        f"Заказ №{order['id']} удален.\n"
        "Вы можете создать новый заказ, выбрав «Заказать буст»."
    )
    
    await state.clear()
    await callback.answer()

@dp.message(F.photo, PaymentStates.waiting_for_screenshot)
async def process_screenshot(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Получен скриншот от пользователя {message.from_user.id}")
    data = await state.get_data()
    payment_id = data.get("payment_id")
    order_id = data.get("order_id")
    
    file_id = message.photo[-1].file_id
    
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE payments SET screenshot_file_id = ?, status = 'verification' WHERE id = ?", 
                      (file_id, payment_id))
        cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        payment = cursor.fetchone()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (payment['order_id'],))
        order = cursor.fetchone()
        db.commit()
    
    await message.answer(
        "✅ <b>Скриншот получен</b>\n\n"
        "Ваш платеж находится на проверке. "
        "Мы уведомим вас, как только проверка будет завершена.\n\n"
        "Хотите оставить отзыв? (Да/Нет)",
        reply_markup=yes_no_kb
    )
    
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=file_id,
        caption=f"🆕 <b>Новый платеж на проверку</b>\n\n"
                f"ID платежа: <code>{payment_id}</code>\n"
                f"Заказ: #{order['id']}\n"
                f"Пользователь: @{message.from_user.username} ({message.from_user.id})\n"
                f"Метод: {payment['method']}\n"
                f"Сумма: {payment['amount']} руб.\n"
                f"Дата: {payment['created_at']}"
    )
    
    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_confirm_{payment_id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{payment_id}")],
        ]
    )
    
    await bot.send_message(
        chat_id=ADMIN_ID,
        text="Пожалуйста, проверьте платеж и подтвердите или отклоните его.",
        reply_markup=admin_kb
    )
    
    await state.set_state(None)

@dp.message(PaymentStates.waiting_for_screenshot, F.text.in_(["Да", "Нет"]))
async def process_review_option(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Выбор оставления отзыва от пользователя {message.from_user.id}: {message.text}")
    if message.text == "Да":
        await message.answer("Введите ваш отзыв в формате:\n<code>Рейтинг (1-5) | Текст отзыва</code>\nПример: <code>5 | Отличный буст, быстро и качественно!</code>")
        await state.set_state(None)
    else:
        await message.answer("Спасибо! Вы можете вернуться в главное меню.", reply_markup=main_kb)
        await state.clear()

@dp.message(F.text.regexp(r'^\d\s*\|\s*.+'))
async def process_review(message: types.Message, state: FSMContext):
    log_user_action(message.from_user, f"Пользователь {message.from_user.id} отправил отзыв")
    try:
        user_id = message.from_user.id
        rating, text = message.text.split("|", 1)
        rating = int(rating.strip())
        text = text.strip()
        
        if not 1 <= rating <= 5:
            await message.answer("❌ Рейтинг должен быть от 1 до 5.")
            return
        
        with get_db() as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM orders WHERE user_id = ? AND payment_status = 'paid' ORDER BY created_at DESC LIMIT 1", (user_id,))
            order = cursor.fetchone()
            if not order:
                await message.answer("❌ У вас нет оплаченных заказов.")
                return
            
            cursor.execute(
                "INSERT INTO reviews (user_id, username, text, rating, order_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, message.from_user.username, text, rating, order['id'])
            )
            db.commit()
        
        await message.answer("✅ Ваш отзыв успешно сохранен!", reply_markup=main_kb)
        await bot.send_message(
            ADMIN_ID,
            f"🆕 Новый отзыв от @{message.from_user.username}:\n"
            f"Рейтинг: {rating}/5\n"
            f"Текст: {text}"
        )
    except Exception as e:
        logging.error(f"Error processing review: {e}")
        await message.answer("❌ Ошибка. Попробуйте еще раз.")

# ================== ОТЛАДКА НЕОБРАБОТАННЫХ СООБЩЕНИЙ ==================
@dp.message()
async def catch_all(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    log_user_action(message.from_user, f"Catch-all: Message '{message.text}' from user {message.from_user.id}, current state: {current_state}")
    await message.answer("Неизвестная команда или ввод. Попробуйте снова.")

# ================== ЗАПУСК БОТА ==================
async def main():
    logging.info("Запуск функции main()...")
    try:
        update_db_schema()
        update_payment_table()
        logging.info("Запуск поллинга...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    logging.info("Запуск скрипта...")
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Критическая ошибка при запуске: {e}")