from myFilters.user import IsCode
from data.db import get_films, get_AllChennel, get_error_link_complaint_unix, update_error_link_complaint_unix, get_text, add_user
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from time import time
from keybord_s.ohter import ikb_close, ikb_close_oikb
from keybord_s.user import sub_list, kb_films
from datetime import datetime, timedelta
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types
from aiogram.dispatcher import FSMContext
from loader import dp, bot
from aiogram.dispatcher.filters import CommandStart
from myFilters.admin import IsAdminM
from keybord_s import admin
from config import admin_ids


# Определение состояний
class FilmStates(StatesGroup):
    waiting_for_code = State()

@dp.callback_query_handler(text='close_text')
async def cancellation_state(call: types.CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
        # После удаления сообщения запускаем код аналогичный cmd_start
        await cmd_start(call.message, state)
    except Exception as e:
        await call.message.answer(f"Ошибка: {e}")

@dp.message_handler(CommandStart(), state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
            await add_user(user_id=message.from_user.id, user_menotion=message.from_user.id)
        except Exception as e:
            print(f"Error adding user: {e}")
        
        text_start = await get_text(type='text_text', text_type='wellcome')
        text_start = text_start[0][0]
        
        me = await bot.get_me()
        text_start = str(text_start).replace('{username_bot}', me.mention)
        text_start = str(text_start).replace('{bot_id}', str(me.id))
        text_start = str(text_start).replace('{username}', message.from_user.mention)
        text_start = str(text_start).replace('{full_name}', message.from_user.full_name)
        text_start = str(text_start).replace('{user_id}', str(message.from_user.id))
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text='RANDOM 🎲', callback_data='RANDOM'))
        keyboard.add(InlineKeyboardButton(text='Фильм по коду', callback_data='filmpokody'))
        
        await message.answer(text=text_start, parse_mode=types.ParseMode.MARKDOWN, reply_markup=keyboard)
        await FilmStates.waiting_for_code.set()


# Обработчик для callback_data='filmpokody'
@dp.callback_query_handler(lambda c: c.data == 'filmpokody', state='*')
async def process_filmpokody_callback(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        await bot.answer_callback_query(callback_query.id)
        
        # Создаем кнопку "Назад"
        back_button = InlineKeyboardButton("Назад", callback_data="BACK_TO_SELECTION")
        keyboard = InlineKeyboardMarkup().add(back_button)
        
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text="<b>Пожалуйста, пришлите код фильма.</b>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await FilmStates.waiting_for_code.set()
    except Exception as e:
        await bot.send_message(callback_query.from_user.id, f"Произошла ошибка: {e}")
        
# Обработчик для получения кода фильма
@dp.message_handler(IsCode(), state=FilmStates.waiting_for_code)
async def get_FimsWithCode(message: types.Message, state: FSMContext):
    await message.delete()
    data_chennel = await get_AllChennel()
    for i in data_chennel:
        try:
            status = await bot.get_chat_member(chat_id=i[0], user_id=message.from_user.id)
            if status.status == 'left':
                await message.answer('Вы не подписаны на канал(ы)❌\nПосле подписки повторите попытку👌', reply_markup=await sub_list())
                return
        except:
            await bot.send_message(chat_id=admin_ids, text=f'Похоже этот канал удалил нас запустите "Проверку каналов"\nЧто бы проверить меня на наличие прав\nИндификатор: {i[0]}\nНазвание: {i[1]}\nСыллка: {i[2]}', reply_markup=ikb_close.row(InlineKeyboardButton(text='Проверить каналы⚛️', callback_data='check_chennel_admin')))

    # Получаем данные фильма по коду
    film_data = await get_films(code=message.text)
    
    # Если данные фильма не найдены
    if not film_data:
        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(text='Назад', callback_data='filmpokody'))
        await message.answer("Код неправильный. Пожалуйста, попробуйте еще раз.", reply_markup=keyboard)
        return

    # Формируем сообщение с информацией о фильме
    text_film = await get_text(type='text_text', text_type='film')
    text_film = text_film[0][0]
    me = await bot.get_me()
    text_film = str(text_film).replace('{username_bot}', me.mention)
    text_film = str(text_film).replace('{bot_id}', str(me.id))
    text_film = str(text_film).replace('{username}', message.from_user.mention)
    text_film = str(text_film).replace('{full_name}', message.from_user.full_name)
    text_film = str(text_film).replace('{user_id}', str(message.from_user.id)) 
    text_film = str(text_film).replace('{film_name}', film_data[0][1]) 
    text_film = str(text_film).replace('{film_code}', message.text) 
    
    # Добавляем кнопку "Назад"
    ikb_films = await kb_films(name_films=film_data[0][1])
    ikb_films.add(InlineKeyboardButton(text='Назад', callback_data='filmpokody'))
    
    # Отправляем сообщение с фильмом
    await bot.send_photo(chat_id=message.from_user.id, photo=film_data[0][2], caption=text_film, reply_markup=ikb_films.row(ikb_close_oikb), parse_mode=types.ParseMode.HTML)
    
    # Завершаем состояние
    await state.finish()

# Обработчик для админ-команды /admin
@dp.message_handler(IsAdminM(), text='/admin')
async def cmd_admin(message: types.Message):
    await message.answer('*Админ меню*', reply_markup=admin.admin_menu_main, parse_mode=types.ParseMode.MARKDOWN)