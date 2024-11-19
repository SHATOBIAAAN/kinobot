from loader import dp, bot
from aiogram import types
from keybord_s import admin
from myFilters.admin import IsAdminM
from aiogram.dispatcher import FSMContext
#вызов admin меню#
@dp.message_handler(IsAdminM(), commands=['admin'], state='*')
async def cmd_admin(message: types.Message, state: FSMContext):
    await state.finish()  # Сброс состояния
    await message.answer('*Админ меню*', reply_markup=admin.admin_menu_main, parse_mode=types.ParseMode.MARKDOWN)
