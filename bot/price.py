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

def calculate_calibration_price(games_remaining: int, target_mmr: int) -> int:
    """
    Calculate the price for calibration service based on remaining games and target MMR.
    
    Args:
        games_remaining (int): Number of calibration games remaining
        target_mmr (int): Target MMR for calibration
        
    Returns:
        int: Price in rubles
    """
    base_price = 500  # Base price per game
    mmr_multiplier = 1.0
    
    # Adjust price based on target MMR
    if target_mmr >= 5000:
        mmr_multiplier = 1.5
    elif target_mmr >= 4000:
        mmr_multiplier = 1.3
    elif target_mmr >= 3000:
        mmr_multiplier = 1.2
    elif target_mmr >= 2000:
        mmr_multiplier = 1.1
    
    total_price = int(base_price * games_remaining * mmr_multiplier)
    return total_price 