import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Mini App
MINI_APP_URL = os.getenv('MINI_APP_URL', 'http://localhost:5000')

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///shifts.db')

# App Settings
SHIFTS_FORWARD_DAYS = 30  # На сколько дней вперед можно добавлять смены
