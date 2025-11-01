from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import BOT_TOKEN, MINI_APP_URL
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔄 Открыть приложение обмена смен",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )]
    ])
    
    await message.answer(
        "👋 Добро пожаловать в приложение обмена смен!\n\n"
        "Здесь вы можете:\n"
        "• 📤 Отправить свою смену\n"
        "• 📋 Посмотреть доступные смены\n"
        "• 🔔 Получать уведомления о запросах\n\n"
        "Нажмите кнопку ниже, чтобы начать.",
        reply_markup=keyboard
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Справка"""
    await message.answer(
        "📚 <b>Справка</b>\n\n"
        "<b>Как использовать:</b>\n"
        "1. Откройте приложение\n"
        "2. Авторизуйтесь с вашим LDAP ником\n"
        "3. Отправьте свою смену или возьмите доступную\n\n"
        "<b>Типы смен:</b>\n"
        "🌅 <b>День:</b> 06:00-18:00\n"
        "🌙 <b>Ночь:</b> 18:00-06:00\n"
        "⏰ <b>Часы:</b> Произвольный период\n\n"
        "Вопросы? Свяжитесь с администратором.",
        parse_mode="HTML"
    )

async def main():
    logger.info("Bot started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
