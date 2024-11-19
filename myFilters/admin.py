from aiogram.dispatcher.filters import BoundFilter
from aiogram import types
from loader import admin_ids

# Фильтр на администратора в сообщениях
class IsAdminM(BoundFilter):
    async def check(self, message: types.Message):
        return message.chat.id in admin_ids

# Фильтр на администратора в callback
class IsAdminC(BoundFilter):
    async def check(self, message: types.CallbackQuery):
        return message.from_user.id in admin_ids

class IsAdminCAndChenneger_swich_player(BoundFilter):
    async def check(self, message: types.CallbackQuery):
        return message.from_user.id in admin_ids and message.data[0:28] == 'chenneger_swich_player_admin'

class IsAdminCAndChenneger_kbname_player_admin(BoundFilter):
    async def check(self, message: types.CallbackQuery):
        return message.from_user.id in admin_ids and message.data[0:29] == 'chenneger_kbname_player_admin'