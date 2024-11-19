from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import token, admin_ids

# Connect к боту
storage = MemoryStorage()
bot = Bot(token)
dp = Dispatcher(bot, storage=storage)
admin_ids=admin_ids