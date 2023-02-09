import asyncio
import configparser
import traceback
from multiprocessing import Process
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
bot = Bot(token=config['k_league']['token'])
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
        await bot.send_message(user_id, 'Включено оповещение об обновлениях в таблице "K_League_2022 - schedule"')
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
        pass


def set_data():
    data_google = google.get_select_data()

    try:
        db.del_table('k_league_1')
        db.del_table('k_league_2')
    except:
        pass

    db.check(table='users', columns=['id INT'])
    db.check(table='k_league_1', columns=['match_id INT', 'date', 'time_MSK', 'time_difference',
                                          'time_KOR', 'team_1', 'team_2', 'link'])
    db.check(table='k_league_2', columns=['match_id INT', 'date', 'time_MSK', 'time_difference',
                                          'time_KOR', 'team_1', 'team_2', 'link'])

    for i in range(2):
        sheet = data_google[i]
        sheet_name = f'k_league_{i + 1}'
        strings = []
        for string in sheet:
            values = list(string.values())
            strings.append(values)
        db.add_elem(sheet_name, strings=strings)


def diff(list1, list2):
    res = []
    for i in list1:
        if i not in list2:
            res.append(i)
    return res


def main_loop(cfg):
    db = DB(file=cfg['k_league']['db'])
    google = GoogleSheets(cfg['k_league']['google_sheet'])
    while True:
        try:
            data_google_ = google.get_data()
            data_google = google.select_data(data_google_)

            data_db = [db.get_data(table='k_league_1'), db.get_data(table='k_league_2')]

            for i_sh in range(2):
                sheet_google = data_google[i_sh]
                sheet_db = data_db[i_sh]

                data_diff = diff(sheet_db, sheet_google)
                if data_diff:
                    for i in data_diff:
                        db.del_elem(f'k_league_{i_sh + 1}', key='match_id', value=i['match_id'])

                if not sheet_google:
                    continue

                data_diff = diff(sheet_google, sheet_db)
                for i in data_diff:
                    logger.info(f'Push message {i["match_id"]}')
                    string = data_google_[i_sh].index(i) + 2
                    asyncio.run(push_message(f'<b>Внимание!</b> Внесены новые ссылки для скачивания\n\n'
                                             f'<b>Table:</b> K League {i_sh + 1}   <b>String:</b> {string}\n\n'
                                             f'<b>Match ID:</b> {i["match_id"]}\n\n'
                                             f'<b>Home Team:</b> {i["team_1"]}\n'
                                             f'<b>Away Team:</b> {i["team_2"]}\n'
                                             f'<b>Date:</b> {i["date"]}\n\n'
                                             f'<b>Video Link:</b>\n{i["link"]}'))
                    db.add_elem(f'k_league_{i_sh + 1}', values=list(i.values()))

            sleep(3)
        except KeyboardInterrupt:
            pass
        except:
            logger.error(traceback.format_exc())
            sleep(10)


db = DB(file='server.db')
google = GoogleSheets(config['k_league']['google_sheet'])

if __name__ == '__main__':
    set_data()
    Process(target=main_loop, args=(config, )).start()
    executor.start_polling(dp)
