import asyncio
import configparser
import traceback
from multiprocessing import Process
from pprint import pprint
from sqlite3 import OperationalError
from time import sleep
from DB import DB
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from loguru import logger
from google_sheets import GoogleSheets

config = configparser.ConfigParser()
config.read("config.ini")
bot = Bot(token=config['app']['token'])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


def get_users():
    users = []
    data = db.get_data(table='users')
    for i in data:
        users.append(i['id'])
    return users


@dp.message_handler()
async def start(msg: types.Message):
    try:
        user_id = msg.from_user.id
        users = get_users()
        if not users or not (user_id in users):
            db.add_elem(table='users', values=[user_id])
            logger.debug(f'User {user_id} added to database')
        await bot.send_message(user_id, 'Включено оповещение об обновлениях в таблице "Календарь"')
    except Exception as ex:
        logger.error(traceback.format_exc())


async def push_message(message):
    try:
        users = get_users()
        tasks = []
        for user in users:
            tasks.append(asyncio.create_task(bot.send_message(int(user), message, parse_mode='html')))
        [await task for task in tasks]
    except Exception as ex:
        logger.error(traceback.format_exc())


def set_data():
    # data_google = google.sheets[1].get_all_records()

    try:
        db.del_table(table_name)
    except:
        pass

    db.check(table='users', columns=['id INT'])

    def get_column_names(sheet):
        return sheet.row_values(1)

    column_data_types = {
        "id": "INTEGER",
        "tournament": "TEXT",
        "date": "TEXT",
        "time": "TEXT",
        "t1": "INTEGER",
        "t1_name": "TEXT",
        "t2": "INTEGER",
        "t2_name": "TEXT",
        "uploaded_video": "TEXT",
        "uploaded_tech": "TEXT",
        "analysis": "TEXT",
        "match_status": "TEXT",
        "reviewer_comment": "TEXT",
        "tech_link": "TEXT",
        "report": "TEXT",
        "platform": "TEXT"
    }

    # Создание таблицы с той же структурой, что и в Google Sheets
    column_names = get_column_names(google.sheet)
    column_definitions = [f"{col} {column_data_types[col]}" for col in column_names]

    try:
        db.check(table_name, columns=column_definitions)
    except OperationalError as e:
        print(f"Ошибка при создании таблицы: {e}")
    #
    # sheet = data_google
    # strings = []
    # for string in sheet:
    #     strings.append({k: string[k] for k in columns_other if k in string})
    # db.add_elem(table_name, strings=strings)


def copy_data_to_db(sheet):
    all_data = sheet.get_all_records()
    for row in all_data:
        values = list(row.values())
        db.add_elem(table_name, values=values)


def diff(list1, list2):
    res = []
    for i in list1:
        if i not in list2:
            res.append(i)
    return res


def main_loop(cfg):
    db = DB(file=cfg['app']['db'])
    google = GoogleSheets(cfg['app']['google_sheet'])
    logger.info('Запуск прошел успешно')
    while True:
        try:
            data_google = google.sheet.get_all_records()
            data_db = db.get_data(table_name)

            for match in data_google:
                if match in data_db or (match['uploaded_video'] != 'да' and
                                        match['uploaded_tech'] != 'да'):
                    continue

                message = f'''
<b>Внимание!</b> обновление в таблице "Календарь"
<b>Table:</b> остальное(оффлайн)

<b>Match ID:</b> {match['id']}

<b>Home Team:</b> {match['t1_name']}
<b>Away Team:</b> {match['t2_name']}
<b>Date:</b> {match['date']}

<b>Видео:</b> {match['uploaded_video']}
<b>Техничка:</b> {match['uploaded_tech']}
'''

                asyncio.run(push_message(message=message))
                db.add_or_replace_elem(table=table_name, row_data=match)
                logger.success(f'Отработал матч {match}')

            sleep(3)

        except KeyboardInterrupt:
            pass
        except:
            logger.error(traceback.format_exc())
            sleep(10)


db = DB(file='server.db')
google = GoogleSheets(config['app']['google_sheet'])
table_name = 'other'
columns_rpl = ['id', 'tournament', 'date', 't1_name', 't2_name', 'залита техничка на диск']
columns_other = ['id', 'tournament', 'date', 't1_name', 't2_name', 'Залито видео', 'залита техничка']

if __name__ == '__main__':
    # pprint(google.sheets[0].get_all_records()[10:13])
    set_data()
    copy_data_to_db(google.sheet, )
    Process(target=main_loop, args=(config,)).start()
    executor.start_polling(dp)
