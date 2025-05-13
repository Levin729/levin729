import logging
from aiogram import types

def log_user_action(user: types.User, action: str):
    username = f"@{user.username}" if user.username else "(без username)"
    fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
    logging.info(f"[{user.id}] {username} ({fullname}) — {action}") 