from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp, bot
from data.db import get_films, get_AllChennel, get_text, add_user
from config import admin_ids , API_KEY
import logging
import aiohttp
import random

# Определение состояний
class FilmStates(StatesGroup):
    waiting_for_code = State()
    selected_media_type = State()
# Обработчик для кнопки "Назад"
@dp.callback_query_handler(lambda c: c.data == 'BACK_TO_SELECTION', state=FilmStates.selected_media_type)
async def process_back_to_selection(callback_query: types.CallbackQuery, state: FSMContext):
    # Сбрасываем состояние
    await state.finish()

    # Формируем текст и клавиатуру для меню выбора
    text_start = "*Что выберите?*"
    keyboard = create_random_combined_keyboard()
    
    await bot.send_message(chat_id=callback_query.from_user.id, text=text_start, parse_mode=types.ParseMode.MARKDOWN, reply_markup=keyboard)
    
    await bot.answer_callback_query(callback_query.id)

# Обработчик для кнопки "Ещё"
@dp.callback_query_handler(lambda c: c.data == 'MORE', state=FilmStates.selected_media_type)
async def process_more_button(callback_query: types.CallbackQuery, state: FSMContext):
    media_type = await state.get_data()
    media_type = media_type.get('media_type', 'movie')  # Default to movie
    
    if media_type == 'movie':
        await process_random_movie(callback_query, state)
    elif media_type == 'series':
        await process_random_series(callback_query, state)
    elif media_type == 'anime':
        await process_random_anime(callback_query, state)

    await bot.answer_callback_query(callback_query.id)

# Обработчик для кнопки RandomMovie
@dp.callback_query_handler(lambda c: c.data == 'BUTTON_1', state='*')
async def process_random_movie(callback_query: types.CallbackQuery, state: FSMContext):
    random_film = await get_random_film_from_tmdb()
    if random_film:
        try:
            film_name = random_film['title']
            film_year = random_film.get('release_date', 'Неизвестно')[:4]
            poster_path = random_film.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            response_text = f"Фильм: {film_name}\nГод: {film_year}"

            if poster_url:
                await bot.send_photo(callback_query.from_user.id, poster_url, caption=response_text, reply_markup=create_back_and_more_keyboard())
            else:
                await bot.send_message(callback_query.from_user.id, response_text, reply_markup=create_back_and_more_keyboard())

            await FilmStates.selected_media_type.set()
            await state.update_data(media_type='movie')

        except KeyError as e:
            response_text = f"Ошибка: ключ {e} отсутствует в данных фильма."
            await bot.send_message(callback_query.from_user.id, response_text)
    else:
        await bot.send_message(callback_query.from_user.id, "Не удалось получить случайный фильм.")

    await bot.answer_callback_query(callback_query.id)

# Обработчик для кнопки "Случайный сериал"
@dp.callback_query_handler(lambda c: c.data == 'BUTTON_2', state='*')
async def process_random_series(callback_query: types.CallbackQuery, state: FSMContext):
    random_series = await get_random_series_from_tmdb()
    if random_series:
        try:
            series_name = random_series['name']
            series_year = random_series.get('first_air_date', 'Неизвестно')[:4]
            poster_path = random_series.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

            response_text = f"Сериал: {series_name}\nГод: {series_year}"

            if poster_url:
                await bot.send_photo(callback_query.from_user.id, poster_url, caption=response_text, reply_markup=create_back_and_more_keyboard())
            else:
                await bot.send_message(callback_query.from_user.id, response_text, reply_markup=create_back_and_more_keyboard())

            await FilmStates.selected_media_type.set()
            await state.update_data(media_type='series')

        except KeyError as e:
            response_text = f"Ошибка: ключ {e} отсутствует в данных сериала."
            await bot.send_message(callback_query.from_user.id, response_text)
    else:
        await bot.send_message(callback_query.from_user.id, "Не удалось получить случайный сериал.")

    await bot.answer_callback_query(callback_query.id)

# Обработчик для кнопки RandomAnime


# Функция для создания клавиатуры с кнопками каналов и кнопкой "Сделано ✅"
async def sub_list():
    data_channel = await get_AllChennel()
    sub_list = InlineKeyboardMarkup(row_width=1)
    for i in data_channel:
        sub_list.add(InlineKeyboardButton(text=i[1], url=i[2]))
    sub_list.add(InlineKeyboardButton(text='Сделано ✅', callback_data='done'))
    return sub_list

# Функция для создания клавиатуры с выбором медиа
def create_random_combined_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='🎬 Случайный фильм', callback_data='BUTTON_1'))
    keyboard.add(InlineKeyboardButton(text='📺 Случайный сериал', callback_data='BUTTON_2'))
    keyboard.add(InlineKeyboardButton(text='🎌 Случайное аниме', callback_data='BUTTON_3'))
    keyboard.add(InlineKeyboardButton(text='🔙 Назад', callback_data='BACK_TO_SELECTION'))
    return keyboard
# Функция для безопасного редактирования сообщения
async def edit_message_safe(callback_query: types.CallbackQuery, new_text: str, new_keyboard: InlineKeyboardMarkup):
    try:
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=new_text,
            reply_markup=new_keyboard,
            parse_mode=types.ParseMode.MARKDOWN
        )
    except types.MessageNotModified:
        logging.info("Message not modified: new content is the same as current.")
    except Exception as e:
        logging.error(f"Error editing message: {e}")

# Функция для получения случайного фильма




import aiohttp
import random
import logging

  # Убедитесь, что у вас есть ключ API

# Прокси данные
proxy_user = 'wQAoWQ'
proxy_password = 'j64FcG'
proxy_url = f'http://{proxy_user}:{proxy_password}@185.239.136.147:8000'

async def get_random_film_from_tmdb():
    page = random.randint(1, 500)  # выбираем случайную страницу
    url = f'https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&page={page}'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy_url) as response:
            if response.status == 200:
                data = await response.json()
                if data['results']:
                    # Фильтрация фильмов без жанра "Анимация"
                    filtered_movies = [movie for movie in data['results'] 
                                       if 16 not in movie['genre_ids']]  # 16 - это ID жанра "Анимация"
                    if filtered_movies:
                        return random.choice(filtered_movies)
                    else:
                        logging.error("No non-animation movies available.")
                        return None
                else:
                    logging.error("No results for movies.")
                    return None
            else:
                logging.error(f"Error getting movie data: {response.status} - {await response.text()}")
                return None

async def get_random_series_from_tmdb():
    page = random.randint(1, 500)  # выбираем случайную страницу
    url = f'https://api.themoviedb.org/3/tv/popular?api_key={API_KEY}&page={page}'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, proxy=proxy_url) as response:
            if response.status == 200:
                data = await response.json()
                if data['results']:
                    # Фильтрация сериалов без жанра "Аниме" (согласно TMDB, используем только идентификаторы)
                    animation_genre_id = 16  # ID жанра "Анимация"
                    filtered_series = [series for series in data['results'] 
                                       if animation_genre_id not in series['genre_ids']]
                    if filtered_series:
                        return random.choice(filtered_series)
                    else:
                        logging.error("No non-anime series available.")
                        return None
                else:
                    logging.error("No results for series.")
                    return None
            else:
                logging.error(f"Error getting series data: {response.status} - {await response.text()}")
                return None
# Функция для получения случайного аниме
import aiohttp
import logging
import random
from aiogram import types
from aiogram.dispatcher import FSMContext

# Set to keep track of recently sent anime
recently_sent_anime = set()

async def get_random_anime():
    async with aiohttp.ClientSession() as session:
        page = random.randint(1, 100)  # Adjust the upper limit as necessary
        async with session.get(f'https://kitsu.io/api/edge/anime?page[limit]=20&page[offset]={page*20}') as response:
            if response.status == 200:
                data = await response.json()
                if data['data']:
                    anime_list = [anime for anime in data['data'] if anime['attributes']['canonicalTitle'] not in recently_sent_anime]
                    if anime_list:
                        return random.choice(anime_list)
                    else:
                        logging.warning("All anime from the selected page have been recently sent.")
                        return None
                else:
                    logging.error("No anime data found in the response.")
                    return None
            else:
                logging.error(f"Error getting anime data: {response.status} - {await response.text()}")
                return None

@dp.callback_query_handler(lambda c: c.data == 'BUTTON_3', state='*')
async def process_random_anime(callback_query: types.CallbackQuery, state: FSMContext):
    random_anime = await get_random_anime()
    if random_anime:
        try:
            anime_name = random_anime['attributes']['canonicalTitle']
            aired_from = random_anime['attributes'].get('startDate')
            anime_year = aired_from[:4] if aired_from else 'Неизвестно'
            poster_path = random_anime['attributes']['posterImage']['medium']
    
            response_text = f"Аниме: {anime_name}\nГод: {anime_year}"

            if poster_path:
                await bot.send_photo(callback_query.from_user.id, poster_path, caption=response_text, reply_markup=create_back_and_more_keyboard())
            else:
                await bot.send_message(callback_query.from_user.id, response_text, reply_markup=create_back_and_more_keyboard())

            await FilmStates.selected_media_type.set()
            await state.update_data(media_type='anime')

            # Add the anime title to the recently sent set
            recently_sent_anime.add(anime_name)

            # Optionally, clear the cache after a certain number of sent anime
            if len(recently_sent_anime) > 20:  # Adjust the limit as needed
                recently_sent_anime.pop()  # Remove an older entry

        except KeyError as e:
            response_text = f"Ошибка: ключ {e} отсутствует в данных аниме."
            await bot.send_message(callback_query.from_user.id, response_text)
    else:
        await bot.send_message(callback_query.from_user.id, "Не удалось получить случайное аниме.")

    await bot.answer_callback_query(callback_query.id)



# Обработчик команды /start
@dp.message_handler(CommandStart(), state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        try:
            await add_user(user_id=message.from_user.id, user_menotion=message.from_user.id)
        except Exception as e:
            logging.error(f"Error adding user: {e}")

        text_start = await get_text(type='text_text', text_type='wellcome')
        text_start = text_start[0][0]
        
        me = await bot.get_me()
        text_start = text_start.format(
            username_bot=me.mention,
            bot_id=me.id,
            username=message.from_user.mention,
            full_name=message.from_user.full_name,
            user_id=message.from_user.id
        )
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(text='RANDOM 🎲', callback_data='RANDOM'))
        keyboard.add(InlineKeyboardButton(text='🎥 Фильм по коду', callback_data='filmpokody'))
        await message.answer(text=text_start, parse_mode=types.ParseMode.MARKDOWN, reply_markup=keyboard)
        await FilmStates.waiting_for_code.set()

# Обработчик нажатия на кнопку RANDOM
@dp.callback_query_handler(lambda c: c.data == 'RANDOM', state='*')
async def process_random_button(callback_query: types.CallbackQuery, state: FSMContext):
    data_channel = await get_AllChennel()
    
    for i in data_channel:
        try:
            status = await bot.get_chat_member(chat_id=i[0], user_id=callback_query.from_user.id)
            if status.status == 'left':
                await callback_query.message.answer(
                    'Вы не подписаны на канал(ы)❌\nПосле подписки повторите попытку👌',
                    reply_markup=await sub_list()
                )
                await bot.answer_callback_query(callback_query.id)
                return
        except Exception as e:
            logging.error(f"Error checking subscription for channel {i[0]}: {e}")
            await bot.send_message(chat_id=admin_ids, text=f'Похоже, этот канал удалил нас. Запустите "Проверку каналов", чтобы проверить наличие прав.\nИндификатор: {i[0]}\nНазвание: {i[1]}\nСсылка: {i[2]}')
            await bot.answer_callback_query(callback_query.id)
            return

    new_text = "*Что выберите?*"
    new_keyboard = create_random_combined_keyboard()
    await edit_message_safe(callback_query, new_text, new_keyboard)

    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'RESTART', state='*')
async def process_restart_button(callback_query: types.CallbackQuery, state: FSMContext):
    await cmd_start(callback_query, state)
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'BACK_TO_SELECTION', state='*')
async def cmd_start(callback_query: types.CallbackQuery, state: FSMContext):
    # Сбрасываем состояние
    await state.finish()

    # Формируем текст и клавиатуру для меню выбора
    text_start = await get_text(type='text_text', text_type='wellcome')
    text_start = text_start[0][0]
        
    me = await bot.get_me()
    user = callback_query.from_user

    # Проверка, что пользователь не является ботом
    if user.is_bot:
        await bot.answer_callback_query(callback_query.id, text="Ошибка: нельзя отправить сообщение боту.")
        return

    text_start = text_start.format(
        username_bot=me.mention,
        bot_id=me.id,
        username=user.mention,
        full_name=user.full_name,
        user_id=user.id
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='RANDOM 🎲', callback_data='RANDOM'))
    keyboard.add(InlineKeyboardButton(text='Фильм по коду', callback_data='filmpokody'))
    
    await bot.send_message(chat_id=user.id, text=text_start, parse_mode=types.ParseMode.MARKDOWN, reply_markup=keyboard)
    await FilmStates.waiting_for_code.set()
    
# Обработчик для кнопки "Сделано ✅"
@dp.callback_query_handler(lambda c: c.data == 'done', state='*')
async def process_done_button(callback_query: types.CallbackQuery, state: FSMContext):
    data_channel = await get_AllChennel()
    
    subscribed = True  # Флаг для проверки подписки

    for i in data_channel:
        try:
            status = await bot.get_chat_member(chat_id=i[0], user_id=callback_query.from_user.id)
            if status.status == 'left':
                subscribed = False
                break
        except Exception as e:
            logging.error(f"Error checking subscription for channel {i[0]}: {e}")
            subscribed = False
            break

    if subscribed:
            restart_keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("Рестарт", callback_data='RESTART'))
            await bot.send_message(callback_query.from_user.id, "Спасибо, что подписались на каналы! 🎉", reply_markup=restart_keyboard)
    else:
        await callback_query.message.answer(
            'Вы не подписаны на канал(ы)❌\nПосле подписки повторите попытку👌',
            reply_markup=await sub_list()
        )

    await bot.answer_callback_query(callback_query.id)
    
    
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    start_text = "Добро пожаловать! Это стартовое сообщение."
    start_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_keyboard.add(types.KeyboardButton("Кнопка 1"))
    start_keyboard.add(types.KeyboardButton("Кнопка 2"))
    await message.answer(start_text, reply_markup=start_keyboard)

# Обработчик нажатия на кнопку "Назад"
@dp.callback_query_handler(lambda c: c.data == 'BACK_TO_SELECTIONDSA', state='*')
async def process_back_button(callback_query: types.CallbackQuery, state: FSMContext):
    # Сбрасываем состояние
    await state.finish()
    
    # Вызов обработчика команды /start
    await start_command(callback_query.message)
    
    await bot.answer_callback_query(callback_query.id)

@dp.callback_query_handler(lambda c: c.data == 'BACK_TO_SELECTION', state='*')
async def cmd_start(callback_query: types.CallbackQuery, state: FSMContext):
    # Сбрасываем состояние
    await state.finish()

    # Формируем текст и клавиатуру для меню выбора
    text_start = await get_text(type='text_text', text_type='wellcome')
    text_start = text_start[0][0]
        
    me = await bot.get_me()
    text_start = text_start.format(
        username_bot=me.mention,
        bot_id=me.id,
        username=callback_query.from_user.mention,
        full_name=callback_query.from_user.full_name,
        user_id=callback_query.from_user.id
    )
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='RANDOM 🎲', callback_data='RANDOM'))
    keyboard.add(InlineKeyboardButton(text='Фильм по коду', callback_data='filmpokody'))
    
    await bot.send_message(chat_id=callback_query.from_user.id, text=text_start, parse_mode=types.ParseMode.MARKDOWN, reply_markup=keyboard)
    await FilmStates.waiting_for_code.set()

  

# Функция для создания клавиатуры "Назад и еще"
def create_back_and_more_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text='Ещё 🎲', callback_data='MORE'))
    keyboard.add(InlineKeyboardButton(text='Назад', callback_data='BACK_TO_SELECTION'))
    return keyboard
