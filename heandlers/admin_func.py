from loader import bot, dp
from aiogram import types
from aiogram.dispatcher import FSMContext
from myFilters.admin import IsAdminM
from fsm_state_ import admin as astate
from data.db import (
    add_film, 
    only_list, 
    get_AllUser, 
    delete_Film, 
    add_Chennel, 
    delete_Chennel, 
    update_kbname_player, 
    update_wellcome_text
)
from keybord_s.admin import get_Player_menu
from keybord_s.ohter import ikb_back, ikb_close

@dp.channel_post_handler()
async def get_id(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text=message.chat.id)

# Рассылка
@dp.message_handler(IsAdminM(), state=astate.Admin_State.myling_list.text, content_types=types.ContentTypes.ANY)
async def myling_list(message: types.Message, state: FSMContext):
    msg_myling = message.message_id
    async with state.proxy() as data:
        data_user = await only_list(await get_AllUser(type='user_id'))
        count_accept = 0
        count_error = 0
        await bot.edit_message_text(
            chat_id=message.from_user.id, 
            message_id=data['message_id'], 
            text=f'*Данные о рассылки\nТекст: "{message.text}"\n✅Успешно: {count_accept}\n❌Ошибки: {count_error}*', 
            parse_mode=types.ParseMode.MARKDOWN
        )
        
        for user_id in data_user:
            try:
                await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=msg_myling, parse_mode=types.ParseMode.MARKDOWN)
                count_accept += 1
            except Exception as e:
                count_error += 1
                print(f"Error sending message to {user_id}: {e}")

            await bot.edit_message_text(
                chat_id=message.from_user.id, 
                message_id=data['message_id'], 
                text=f'*Данные о рассылки\nТекст: "{message.text}"\n✅Успешно: {count_accept}\n❌Ошибки: {count_error}*', 
                parse_mode=types.ParseMode.MARKDOWN
            )
        
        await message.delete()
        await bot.edit_message_text(
            chat_id=message.from_user.id, 
            message_id=data['message_id'], 
            text=f'*Данные о рассылки\nТекст: "{message.text}"\n✅Успешно: {count_accept}\n❌Ошибки: {count_error}\nРассылка завершена🔔*', 
            parse_mode=types.ParseMode.MARKDOWN, 
            reply_markup=ikb_close
        )
        
    await state.finish()

# Получение кода от фильма
@dp.message_handler(IsAdminM(), state=astate.Admin_State.add_film.code)
async def state_add_film_code(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['code'] = message.text
        await bot.edit_message_text(
            chat_id=message.from_user.id, 
            message_id=data['message_id'], 
            text='Хорошо, теперь отправь мне название🎫', 
            reply_markup=ikb_back
        )
    await astate.Admin_State.add_film.name.set()

# Получение названия от фильма
@dp.message_handler(IsAdminM(), state=astate.Admin_State.add_film.name)
async def state_add_film_name(message: types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        data['name'] = message.text
    await bot.edit_message_text(
        chat_id=message.from_user.id, 
        message_id=data['message_id'], 
        text='Отлично, теперь отправь мне фотографии для обложки📌'
    )
    await astate.Admin_State.add_film.priew.set()

# Получение обложки и сохранение данных
@dp.message_handler(IsAdminM(), state=astate.Admin_State.add_film.priew, content_types=types.ContentTypes.PHOTO)
async def state_add_film_priew(message: types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        await bot.delete_message(chat_id=message.chat.id, message_id=data['message_id'])
        try:
            await add_film(code=data['code'], name=data['name'], priv=message.photo[-1].file_id)
            await message.answer_photo(
                photo=message.photo[-1].file_id, 
                caption=f'📌Фильм добавлен\n🔑Код: {data["code"]}\n🎫Название: {data["name"]}', 
                reply_markup=ikb_close
            )
        except Exception as e:
            await message.answer('Скорее всего, этот код уже добавлен. Ошибка: ' + str(e))
    await state.finish()

# Если не фотография
@dp.message_handler(IsAdminM(), state=astate.Admin_State.add_film.priew)
async def state_add_film_priew_no_photo(message: types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        await bot.edit_message_text(
            chat_id=message.from_user.id, 
            message_id=data['message_id'], 
            text='Жду фотографию😡\nОтлично, теперь отправь мне фотографии для обложки📌', 
            reply_markup=ikb_back
        )

# Удаление фильма
@dp.message_handler(IsAdminM(), state=astate.Admin_State.delete_film.code)
async def delete_film(message: types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        chennel_identifier = message.text.strip()
        
        if await delete_Film(code=chennel_identifier):
            await bot.edit_message_text(
                chat_id=message.from_user.id, 
                message_id=data['message_id'], 
                text='Успешно удалено❎', 
                reply_markup=ikb_close
            )
        else:
            await bot.edit_message_text(
                chat_id=message.from_user.id, 
                message_id=data['message_id'], 
                text='Нет такого кода❌', 
                reply_markup=ikb_back
            )
        
        await state.finish()

@dp.message_handler(IsAdminM(), state=astate.Admin_State.add_chennel.username)
async def add_chennel(message: types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        chennel_identifier = message.text.strip()
        try:
            await bot.get_chat_member(chat_id=chennel_identifier, user_id=message.from_user.id)
            chat = await bot.get_chat(chat_id=chennel_identifier)
            me = await bot.get_me()
            link_chat = await bot.create_chat_invite_link(chat_id=chennel_identifier, name=f'Вход от {me.mention}')
            try:
                await add_Chennel(chennel_identifier=chennel_identifier, name=chat.full_name, link=link_chat.invite_link)
                await bot.edit_message_text(
                    chat_id=message.from_user.id, 
                    message_id=data['message_id'], 
                    text='Канал успешно добавлен✅', 
                    reply_markup=ikb_close
                )
                await state.finish()
            except Exception as e:
                await bot.edit_message_text(
                    chat_id=message.from_user.id, 
                    message_id=data['message_id'], 
                    text='Этот канал уже был добавлен🫤', 
                    reply_markup=ikb_back
                )
        except Exception as e:
            await bot.edit_message_text(
                chat_id=message.from_user.id, 
                message_id=data['message_id'], 
                text='Извините, у меня там нет прав "просматривать участников" и "управления ссылками"❌', 
                reply_markup=ikb_back
            )

@dp.message_handler(IsAdminM(), state=astate.Admin_State.delete_chennel.username)
async def delete_chennel(message: types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        if await delete_Chennel(chennel_identifier=message.text.strip()):
            await bot.edit_message_text(
                chat_id=message.from_user.id, 
                message_id=data['message_id'], 
                text='Канал удален успешно✅', 
                reply_markup=ikb_close
            )
        else:
            await bot.edit_message_text(
                chat_id=message.from_user.id, 
                message_id=data['message_id'], 
                text='Извините, вы не добавляли такого канала❌', 
                reply_markup=ikb_back
            )
        
        await state.finish()

@dp.message_handler(IsAdminM(), state=astate.Admin_State.chennger_kbname_player.text)
async def chennger_kbname_player(message: types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        await update_kbname_player(player_name=data['name_kb'], kb=message.text)
        await bot.edit_message_text(
            chat_id=message.from_user.id, 
            message_id=data['message_id1'], 
            text='Кнопка изменена успешно✅', 
            reply_markup=ikb_close
        )
        await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=data['message_id2'], reply_markup=await get_Player_menu())
        await state.finish()

@dp.message_handler(IsAdminM(), state=astate.Admin_State.chennger_wellcome_text.text)
async def chennger_wellcome_text(message: types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        try:
            await bot.edit_message_text(chat_id=message.from_user.id, message_id=data['message_id'], text=message.text, parse_mode=types.ParseMode.MARKDOWN)
            await bot.edit_message_text(
                chat_id=message.from_user.id, 
                message_id=data['message_id'], 
                text='Успешно изменил текст приветствия✅', 
                reply_markup=ikb_close
            )
            await update_wellcome_text(text_type='wellcome', text=message.text)
            await state.finish()
        except Exception as e:
            await bot.edit_message_text(
                chat_id=message.from_user.id, 
                message_id=data['message_id'], 
                text='Не правильная разметка MARKDOWN✂️', 
                reply_markup=ikb_back
            )

@dp.message_handler(IsAdminM(), state=astate.Admin_State.chennger_film_text.text)
async def chennger_film_text(message: types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        try:
            await bot.edit_message_text(chat_id=message.from_user.id, message_id=data['message_id'], text=message.text, parse_mode=types.ParseMode.MARKDOWN)
            await bot.edit_message_text(
                chat_id=message.from_user.id, 
                message_id=data['message_id'], 
                text='Успешно изменил текст фильма✅', 
                reply_markup=ikb_close
            )
            await update_wellcome_text(text_type='film', text=message.text)
            await state.finish()
        except Exception as e:
            await bot.edit_message_text(
                chat_id=message.from_user.id, 
                message_id=data['message_id'], 
                text='Не правильная разметка MARKDOWN✂️', 
                reply_markup=ikb_back
            )
from aiogram import types  # Перемещаем импорт в начало файла
from aiogram.dispatcher import FSMContext
from myFilters.admin import IsAdminC, IsAdminM
from myFilters.admin import IsAdminCAndChenneger_swich_player, IsAdminCAndChenneger_kbname_player_admin
from fsm_state_ import admin as astate
from data.db import get_AllUser, only_list
from random import randint
from keybord_s.ohter import ikb_back_oikb, ikb_back, ikb_close
from keybord_s.admin import admin_menu_list, admin_menu_main, get_Player_menu, admin_menu_text
from loader import bot, dp
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.dispatcher.filters.state import State, StatesGroup

# Определение состояний для процесса создания и рассылки сообщений
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
        sent_message = await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo,
            caption=text,  # Используем текст как подпись к фото
            reply_markup=keyboard
        )
    else:
        sent_message = await bot.send_message(
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

    # Сохраняем ID сообщения для последующей рассылки
    async with state.proxy() as data:
        data['message_id_to_send'] = sent_message.message_id

    await astate.Admin_State.myling_list.text.set()

@dp.callback_query_handler(IsAdminC(), text='distribute', state=astate.Admin_State.myling_list.text)
async def distribute_message(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        msg_myling = data['message_id_to_send']
        text = data.get('text', '')
        photo = data.get('photo')
        button_text = data.get('button_text', '')
        button_url = data.get('button_url', '')
        
        data_user = await only_list(await get_AllUser(type='user_id'))
        count_accept = 0
        count_error = 0
        
        keyboard = InlineKeyboardMarkup()
        if button_text and button_url:
            url_button = InlineKeyboardButton(button_text, url=button_url)
            keyboard.add(url_button)
        
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

            if photo:
                await bot.edit_message_caption(
                    chat_id=call.from_user.id,
                    message_id=msg_myling,
                    caption=f'*Данные о рассылки\nТекст: "{text}"\n✅Успешно: {count_accept}\n❌Ошибки: {count_error}*',
                    parse_mode=types.ParseMode.MARKDOWN
                )
            elif text:
                await bot.edit_message_text(
                    chat_id=call.from_user.id,
                    message_id=msg_myling,
                    text=f'*Данные о рассылки\nТекст: "{text}"\n✅Успешно: {count_accept}\n❌Ошибки: {count_error}*',
                    parse_mode=types.ParseMode.MARKDOWN
                )
        
        if photo:
            await bot.edit_message_caption(
                chat_id=call.from_user.id,
                message_id=msg_myling,
                caption=f'*Данные о рассылки\nТекст: "{text}"\n✅Успешно: {count_accept}\n❌Ошибки: {count_error}\nРассылка завершена🔔*',
                parse_mode=types.ParseMode.MARKDOWN,
                reply_markup=ikb_close
            )
        elif text:
            await bot.edit_message_text(
                chat_id=call.from_user.id,
                message_id=msg_myling,
                text=f'*Данные о рассылки\nТекст: "{text}"\n✅Успешно: {count_accept}\n❌Ошибки: {count_error}\nРассылка завершена🔔*',
                parse_mode=types.ParseMode.MARKDOWN,
                reply_markup=ikb_close
            )
        
    await state.finish()