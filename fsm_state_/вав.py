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