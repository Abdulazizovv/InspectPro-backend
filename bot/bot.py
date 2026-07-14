from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from environs import Env

env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN", default=None)

# bot = None when BOT_TOKEN is not configured (webhook endpoint handles this gracefully)
bot = (
    Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    if BOT_TOKEN
    else None
)
