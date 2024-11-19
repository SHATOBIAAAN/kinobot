from aiogram import types  # Перемещаем импорт в начало файла
from aiogram.dispatcher import FSMContext
from myFilters.admin import IsAdminC
from myFilters.admin import IsAdminCAndChenneger_swich_player, IsAdminCAndChenneger_kbname_player_admin
from fsm_state_ import admin as astate
from data.db import get_AllFilms, only_list, get_AllChennel, delete_Chennel, update_nameChennel, swich_player
from random import randint
from keybord_s.ohter import ikb_back_oikb, ikb_back, ikb_close
from keybord_s.admin import admin_menu_list, admin_menu_main, get_Player_menu, admin_menu_text
from loader import bot, dp
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

class MailingStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_photo = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()
@dp.message_handler(state=MailingStates.waiting_for_text, content_types=types.ContentType.TEXT)
async def process_text_message(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await MailingStates.waiting_for_photo.set()

    skip_photo_button = InlineKeyboardButton("Пропустить", callback_data="add_link")
    back_button = InlineKeyboardButton("отмена", callback_data="cancellation_state")
    keyboard = InlineKeyboardMarkup().add(skip_photo_button).add(back_button)

    await message.answer('Отправь фотографию или нажми "Пропустить", чтобы продолжить без фото', reply_markup=keyboard)



@dp.callback_query_handler(IsAdminC(), text='myling_list_start_admin')
async def myling_list_start_admin(call: types.CallbackQuery, state: FSMContext):
    skip_text_button = InlineKeyboardButton("Пропустить", callback_data="skip_text")
    back_button = InlineKeyboardButton("отмена", callback_data="cancellation_state")
    keyboard = InlineKeyboardMarkup().add(skip_text_button).add(back_button)

    await MailingStates.waiting_for_text.set()
    await bot.send_message(
        chat_id=call.from_user.id,
        text='Хорошо, отправь текст для рассылки ✒️\nМожно использовать стандартную разметку ✂️',
        reply_markup=keyboard
    )

@dp.callback_query_handler(IsAdminC(), state=MailingStates.waiting_for_text, text='skip_text')
async def skip_text(call: types.CallbackQuery, state: FSMContext):
    await MailingStates.waiting_for_photo.set()
    skip_photo_button = InlineKeyboardButton("Пропустить", callback_data="add_link")
    back_button = InlineKeyboardButton("отмена", callback_data="cancellation_state")
    keyboard = InlineKeyboardMarkup().add(skip_photo_button).add(back_button)

    await bot.send_message(
        chat_id=call.from_user.id,
        text='Отправь фотографию или нажми "Пропустить", чтобы продолжить без фото',
        reply_markup=keyboard
    )


@dp.message_handler(state=MailingStates.waiting_for_photo, content_types=types.ContentType.PHOTO)
async def process_photo_message(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await MailingStates.waiting_for_button_text.set()

    await message.answer('Теперь отправь текст для кнопки URL')

@dp.callback_query_handler(IsAdminC(), state=MailingStates.waiting_for_photo, text='add_link')
async def skip_photo(call: types.CallbackQuery, state: FSMContext):
    await MailingStates.waiting_for_button_text.set()

    await bot.send_message(
        chat_id=call.from_user.id,
        text='Теперь отправь текст для кнопки URL'
    )

@dp.message_handler(state=MailingStates.waiting_for_button_text, content_types=types.ContentType.TEXT)
async def process_button_text_message(message: types.Message, state: FSMContext):
    await state.update_data(button_text=message.text)
    await MailingStates.waiting_for_button_url.set()

    skip_url_button = InlineKeyboardButton("Пропустить", callback_data="skip_url")
    back_button = InlineKeyboardButton("отмена", callback_data="cancellation_state")
    keyboard = InlineKeyboardMarkup().add(skip_url_button).add(back_button)

    await message.answer('Теперь отправь URL для кнопки или нажми "Пропустить"', reply_markup=keyboard)

@dp.message_handler(state=MailingStates.waiting_for_button_url, content_types=types.ContentType.TEXT)
async def process_button_url_message(message: types.Message, state: FSMContext):
    await state.update_data(button_url=message.text)
    await send_final_message(message, state)

@dp.callback_query_handler(IsAdminC(), state=MailingStates.waiting_for_button_url, text='skip_url')
async def skip_url(call: types.CallbackQuery, state: FSMContext):
    await send_final_message(call.message, state)

async def send_final_message(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    text = user_data.get('text', '')  # Получаем текст из FSM данных
    photo = user_data.get('photo')
    button_text = user_data.get('button_text', '')
    button_url = user_data.get('button_url', '')

    keyboard = InlineKeyboardMarkup()

    if button_text and button_url:
        url_button = InlineKeyboardButton(button_text, url=button_url)
        keyboard.add(url_button)

    if photo:
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo,
            caption=text,  # Используем текст как подпись к фото
            reply_markup=keyboard
        )
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=text,  # Используем текст в сообщении
            reply_markup=keyboard
        )

    # Добавляем кнопку "Рассылка"
    distribute_button = InlineKeyboardButton("Рассылка", callback_data="distribute")
    keyboard.add(distribute_button)

    await bot.send_message(
        chat_id=message.chat.id,
        text="Нажмите 'Рассылка', чтобы отправить пост",
        reply_markup=keyboard,
    )

    await astate.Admin_State.myling_list.text.set()





@dp.callback_query_handler(text='back')
async def handle_back_button(call: types.CallbackQuery):
    print("Back button pressed")  # Отладочное сообщение
    await cmd_admin(call.message)

async def cmd_admin(message: types.Message):
    print("cmd_admin called")  # Отладочное сообщение
    await message.answer('*Админ меню*', reply_markup=admin_menu_main, parse_mode=types.ParseMode.MARKDOWN)
@dp.callback_query_handler(IsAdminC(), text='back_main_menu_admin')
async def list_data_check(call: types.Message):
    await call.message.edit_reply_markup(admin_menu_main)
    

#обработка запроса на рассылк
#списки#
@dp.callback_query_handler(IsAdminC(), text='list_data_admin')
async def list_data_check(call: types.Message):
    await call.message.edit_reply_markup(admin_menu_list)

@dp.callback_query_handler(IsAdminC(), text='list_films_admin')
async def list_data_films(call: types.Message):
    file_films=open(file='data//films_data.txt', mode='w+', encoding='UTF-8')
    for i in await get_AllFilms():
        file_films.write(f'Код: {i[0]}, название: {i[1]}\n')
    file_films.close()
    try:
        await bot.send_document(chat_id=call.from_user.id, document=open(file='data//films_data.txt', mode='rb'), reply_markup=ikb_close)
    except:
        await call.answer('У вас нет фильмов❌')
    
@dp.callback_query_handler(IsAdminC(), text='list_chennel_admin')
async def list_data_films(call: types.Message):
    file_films=open(file='data//chennal_data.txt', mode='w+', encoding='UTF-8')
    for i in await get_AllChennel():
        file_films.write(f'Индификатор(вводить при удалении): {i[0]}, Отображение: {i[1]}, Сыллка: {i[2]}\n')
    file_films.close()
    try:
        await bot.send_document(chat_id=call.from_user.id, document=open(file='data//chennal_data.txt', mode='rb'), reply_markup=ikb_close)
    except:
        await call.answer('У вас нет каналов❌')

#Принятие каллбека о добавления фильма в базу данных#
@dp.callback_query_handler(IsAdminC(), text='add_film_admin')
async def add_film_admin(call: types.Message, state: FSMContext):
    message_data=await bot.send_message(chat_id=call.from_user.id, text='Хорошо отправь мне код🔑', reply_markup=types.InlineKeyboardMarkup(row_width=1).\
        add(types.InlineKeyboardButton(text='Сгенирировать♻️', callback_data='generetion_fims_code_admin'), ikb_back_oikb))
    async with state.proxy() as data:
        data['message_id']=message_data.message_id
    await astate.Admin_State.add_film.code.set()

#обработка кнопки сгенирировать#
@dp.callback_query_handler(IsAdminC(), text='generetion_fims_code_admin', state=astate.Admin_State.add_film.code)
async def add_film_generetion_fims_code(call: types.Message, state: FSMContext):
    list_id=await only_list(kortage=await get_AllFilms(type='films_code'))
    while True:
        code=randint(0, 999)
        if code not in list_id:
            break
    async with state.proxy() as data:
        data['code']=code
    await call.message.edit_text('Хорошо теперь отправь мне название🎫')
    await call.message.edit_reply_markup(ikb_back)
    await astate.Admin_State.add_film.name.set()

#удаления канала#
@dp.callback_query_handler(IsAdminC(), text='delete_film_admin')
async def delete_film_admin(message: types.Message, state: FSMContext):
    message_data=await bot.send_message(chat_id=message.from_user.id, text='Хорошо отправь мне код фильма которго хочешь удалить🗑', reply_markup=ikb_back)
    async with state.proxy() as data:
        data['message_id']=message_data.message_id
    await astate.Admin_State.delete_film.code.set()

#добавления канала#
@dp.callback_query_handler(IsAdminC(), text='add_chennel_admin')
async def add_chennel_admin(message: types.Message, state: FSMContext):
    message_data=await bot.send_message(chat_id=message.from_user.id, text='Хорошо дайте в канале права мне "просматривать участников" и "пригласительные сыллками", после отправь мне @username или id канала которго хотите добавить➕', reply_markup=ikb_back)
    async with state.proxy() as data:
        data['message_id']=message_data.message_id
    await astate.Admin_State.add_chennel.username.set()

#удаления канала#
@dp.callback_query_handler(IsAdminC(), text='delete_chennel_admin')
async def add_chennel_admin(message: types.Message, state: FSMContext):
    message_data=await bot.send_message(chat_id=message.from_user.id, text='Хорошо дайте канал который удалить➖', reply_markup=ikb_back)
    async with state.proxy() as data:
        data['message_id']=message_data.message_id
    await astate.Admin_State.delete_chennel.username.set()

@dp.callback_query_handler(IsAdminC(), text='check_chennel_admin')
async def check_chennel_admin(message: types.Message, state: FSMContext):
    text=''
    message_data=await bot.send_message(chat_id=message.from_user.id, text='Хорошо я проверяю подождите♻️')
    me=await bot.get_me()
    me_username=me.username
    for i in await get_AllChennel():
        try:
            me_chat_status=await bot.get_chat_administrators(chat_id=i[0])
            chat_status=await bot.get_chat(chat_id=i[0])
            await bot.get_chat_member(chat_id=i[0], user_id=message.from_user.id)
            await update_nameChennel(chennel_identifier=i[0], name=chat_status.full_name)
            for e in me_chat_status:
                if e['user']['username'] == me_username:
                    if e['can_invite_users']:
                        text+=f'Канал: {i[1]} прошел проверку✅\n\n'
                    else:
                        text+=f'Канал: {i[1]} не имею доступ к сыллкам❗️\n\n'
                    await bot.edit_message_text(chat_id=message.from_user.id, message_id=message_data.message_id, text=f'Хорошо я проверяю подождите♻️\n\n{text}')
                    break
        except:
            await delete_Chennel(chennel_identifier=i[0])
            text+=f'Был удален {i[1]}🗑\n\n'
            await bot.edit_message_text(chat_id=message.from_user.id, message_id=message_data.message_id, text=f'Хорошо я проверяю подождите♻️\n\n{text}')
    await bot.edit_message_text(chat_id=message.from_user.id, message_id=message_data.message_id, text=f'Проверка закончена❇️\n\n{text}\n\nТак же если изменились название каналов то в кнопке они тоже поменяются🔰', reply_markup=ikb_close)

@dp.callback_query_handler(IsAdminC(), text='player_settings_admin')
async def settings_player(call: types.CallbackQuery):
    await call.message.edit_reply_markup(await get_Player_menu())

#вкл./выкл. плееров#
@dp.callback_query_handler(IsAdminCAndChenneger_kbname_player_admin())
async def chennger_kbname_player_admin(call: types.CallbackQuery, state: FSMContext):
    message_data1=await bot.send_message(chat_id=call.from_user.id, text='Хорошо отправь мне новое название кнопки📌', reply_markup=ikb_back)
    message_data2=call.message
    async with state.proxy() as data:
        data['message_id1']=message_data1.message_id
        data['message_id2']=message_data2.message_id
        data['name_kb']=call.data[29:]
    await astate.Admin_State.chennger_kbname_player.text.set()

@dp.callback_query_handler(IsAdminCAndChenneger_swich_player())
async def swich_player_admin(call: types.CallbackQuery):
    await swich_player(player_name=call.data[28:])
    await call.message.edit_reply_markup(await get_Player_menu())
    
@dp.callback_query_handler(IsAdminC(), text='text_settings_admin')
async def text_settings_admin(call: types.CallbackQuery):
    await call.message.edit_reply_markup(admin_menu_text)

@dp.callback_query_handler(IsAdminC(), text='chenneger_wellcome_text_settings_admin')
async def chennger_wellcome_text_settings_admin(call: types.CallbackQuery, state: FSMContext):
    message_data=await bot.send_message(chat_id=call.from_user.id, text='{username_bot}-username бота\n{bot_id}-id бота\n{username}-username пользователя\n{full_name}-полное имя пользователя\n{user_id}-id пользователя\n\nМожно ипользовать разметку MARKDOWN✂️\n\nХорошо отправь мне новое приветствие🖊', reply_markup=ikb_back)
    async with state.proxy() as data:
        data['message_id']=message_data.message_id
    await astate.Admin_State.chennger_wellcome_text.text.set()

@dp.callback_query_handler(IsAdminC(), text='chenneger_film_text_settings_admin')
async def chennger_wellcome_text_settings_admin(call: types.CallbackQuery, state: FSMContext):
    message_data=await bot.send_message(chat_id=call.from_user.id, text='{username_bot}-username бота\n{bot_id}-id бота\n{username}-username пользователя\n{full_name}-полное имя пользователя\n{user_id}-id пользователя\n{film_name}-название фильма\n{film_code}-код от фильма\n\nМожно ипользовать разметку HTML✂️\n\nХорошо отправь мне новый текст для фильмов🖊', reply_markup=ikb_back)
    async with state.proxy() as data:
        data['message_id']=message_data.message_id
    await astate.Admin_State.chennger_film_text.text.set()

# Добавляем финальную функцию для рассылки
@dp.callback_query_handler(IsAdminC(), text='distribute', state=MailingStates.waiting_for_button_url)
async def start_distribution(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    text = user_data.get('text', '')
    photo = user_data.get('photo')
    button_text = user_data.get('button_text', '')
    button_url = user_data.get('button_url', '')

    keyboard = InlineKeyboardMarkup()

    if button_text and button_url:
        url_button = InlineKeyboardButton(button_text, url=button_url)
        keyboard.add(url_button)

    # Получаем всех пользователей для рассылки
    data_user = await only_list(await get_AllUser(type='user_id'))
    count_accept = 0
    count_error = 0

    # Редактируем сообщение для отображения процесса рассылки
    await bot.edit_message_text(
        chat_id=call.from_user.id, 
        message_id=call.message.message_id, 
        text=f'*Данные о рассылке\nТекст: "{text}"\n✅Успешно: {count_accept}\n❌Ошибки: {count_error}*', 
        parse_mode=types.ParseMode.MARKDOWN
    )

    # Отправляем сообщение всем пользователям
    for user_id in data_user:
        try:
            if photo:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=photo,
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=keyboard
                )
            count_accept += 1
        except Exception as e:
            count_error += 1
            print(f"Error sending message to {user_id}: {e}")

        # Обновляем сообщение о статусе рассылки
        await bot.edit_message_text(
            chat_id=call.from_user.id, 
            message_id=call.message.message_id, 
            text=f'*Данные о рассылке\nТекст: "{text}"\n✅Успешно: {count_accept}\n❌Ошибки: {count_error}*', 
            parse_mode=types.ParseMode.MARKDOWN
        )

    # Завершаем рассылку и выводим финальное сообщение
    await bot.edit_message_text(
        chat_id=call.from_user.id, 
        message_id=call.message.message_id, 
        text=f'*Данные о рассылке\nТекст: "{text}"\n✅Успешно: {count_accept}\n❌Ошибки: {count_error}\nРассылка завершена🔔*', 
        parse_mode=types.ParseMode.MARKDOWN, 
        reply_markup=ikb_close
    )

    # Завершаем состояние
    await state.finish()

