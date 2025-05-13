import sqlite3
import logging

def get_db():
    logging.info("Подключение к базе данных...")
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    logging.info("Подключение к БД выполнено")
    return conn

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