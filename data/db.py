import sqlite3
from time import time
import random

# connect к db
sql = sqlite3.connect('data/DataBase.db')
cs = sql.cursor()


# создания таблицы юзеров
cs.execute("""CREATE TABLE IF NOT EXISTS user_data(
    user_id INTEGER PRIMARY KEY,
    user_menotion TEXT,
    user_error_link_complaint_unix INTEGER,
    user_unix INTEGER
)""")

# создания таблицы с данными о кино
cs.execute("""CREATE TABLE IF NOT EXISTS films_data(
    films_code TEXT PRIMARY KEY,
    films_name TEXT,
    films_priv TEXT
)""")

# создания таблицы с данными о каналах
cs.execute("""CREATE TABLE IF NOT EXISTS chennel_data(
    chennel_identifier TEXT PRIMARY KEY,
    chennel_name TEXT,
    chennel_link TEXT
)""")

# создания таблицы с данными о плеерах
cs.execute("""CREATE TABLE IF NOT EXISTS player_data(
    player_web TEXT,
    player_name TEXT PRIMARY KEY,
    switch BOOL,
    kb_name TEXT
)""")

# создания таблицы с текстовыми данными
cs.execute("""CREATE TABLE IF NOT EXISTS text_data(
    text_type TEXT PRIMARY KEY,
    text_text TEXT
)""")

sql.commit()

# Вставка данных с проверкой на существование
def insert_data_with_check(table, data):
    try:
        cs.execute(f"INSERT INTO {table} VALUES({','.join(['?']*len(data))})", data)
        sql.commit()
    except sqlite3.IntegrityError:
        pass

# Примеры вставки данных с использованием функции
insert_data_with_check('player_data', ['https://ww5.frkp.lol', 'frkp', True, 'Смотреть #1▶️'])
insert_data_with_check('player_data', ['www.ggkinopoisk.ru', 'vavada', False, 'Смотреть #2▶️'])
insert_data_with_check('text_data', ['wellcome', '*Привет* [{full_name}](tg://user?id={user_id}) *ты в {username_bot} это самый лучший бот по фильмам веди код фильма и можешь даже посмотреть его бесплатно😉*'])
insert_data_with_check('text_data', ['film', '👤От: {username_bot}\n🎥Название: {film_name}'])

# Функция получения списка
async def only_list(kortage):
    return [i[0] for i in kortage]

# Добавление пользователя с проверкой на уникальность
async def add_user(user_id, user_menotion):
    cs.execute("SELECT * FROM user_data WHERE user_id = ?", (user_id,))
    if cs.fetchone() is None:
        data = [user_id, user_menotion, None, time()]
        cs.execute("INSERT INTO user_data VALUES(?, ?, ?, ?)", data)
        sql.commit()

# Получение всех пользователей
async def get_AllUser(type='*'):
    cs.execute(f"SELECT {type} FROM user_data")
    return cs.fetchall()

# Добавление фильма
async def add_film(code, name, priv):
    insert_data_with_check('films_data', [code, name, priv])

# Получение всех фильмов
async def get_AllFilms(type='*'):
    cs.execute(f"SELECT {type} FROM films_data")
    return cs.fetchall()

# Получение фильма по коду
async def get_films(code):
    cs.execute(f"SELECT * FROM films_data WHERE films_code = ?", (code,))
    return cs.fetchall()

# Удаление фильма по коду
async def delete_Film(code):
    cs.execute(f"SELECT films_code FROM films_data WHERE films_code = ?", (code,))
    if cs.fetchone() is None:
        return False 
    cs.execute(f"DELETE FROM films_data WHERE films_code = ?", (code,))
    sql.commit()
    return True

# Получение времени жалобы на ссылку
async def get_error_link_complaint_unix(user_id):
    cs.execute(f"SELECT user_error_link_complaint_unix FROM user_data WHERE user_id = ?", (user_id,))
    return cs.fetchone()[0]

# Обновление времени жалобы на ссылку
async def update_error_link_complaint_unix(user_id, time_ub):
    cs.execute(f"UPDATE user_data SET user_error_link_complaint_unix = ? WHERE user_id = ?", (time_ub, user_id))
    sql.commit()

# Добавление канала
async def add_Chennel(chennel_identifier, name, link):
    insert_data_with_check('chennel_data', [chennel_identifier, name, link])

# Получение всех каналов
async def get_AllChennel(type='*'):
    cs.execute(f"SELECT {type} FROM chennel_data")
    return cs.fetchall()

# Обновление имени канала
async def update_nameChennel(chennel_identifier, name):
    cs.execute(f"UPDATE chennel_data SET chennel_name = ? WHERE chennel_identifier = ?", (name, chennel_identifier))
    sql.commit()

# Удаление канала по идентификатору
async def delete_Chennel(chennel_identifier):
    cs.execute(f"SELECT * FROM chennel_data WHERE chennel_identifier = ?", (chennel_identifier,))
    if cs.fetchone() is None:
        return False 
    cs.execute(f"DELETE FROM chennel_data WHERE chennel_identifier = ?", (chennel_identifier,))
    sql.commit()
    return True

# Получение всех плееров
async def get_Allplayer(type='*'):
    cs.execute(f"SELECT {type} FROM player_data")
    return cs.fetchall()

# Переключение состояния плеера
async def swich_player(player_name):
    cs.execute(f"SELECT switch FROM player_data WHERE player_name = ?", (player_name,))
    data_swich = cs.fetchone()[0]
    edit = not data_swich
    cs.execute(f"UPDATE player_data SET switch = ? WHERE player_name = ?", (edit, player_name))
    sql.commit()

# Обновление кнопки плеера
async def update_kbname_player(player_name, kb):
    cs.execute(f"UPDATE player_data SET kb_name = ? WHERE player_name = ?", (kb, player_name))
    sql.commit()

# Получение текста по типу
async def get_text(type, text_type):
    cs.execute(f"SELECT {type} FROM text_data WHERE text_type = ?", (text_type,))
    return cs.fetchall()

# Обновление текста приветствия
async def update_wellcome_text(text, text_type):
    cs.execute(f"UPDATE text_data SET text_text = ? WHERE text_type = ?", (text, text_type))
    sql.commit()

# Получение случайного фильма
async def get_random_film():
    cs.execute("SELECT films_code, films_name FROM films_data")
    films = cs.fetchall()
    return random.choice(films) if films else None
