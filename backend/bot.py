import os
from aiogram import Bot, types, executor
from aiogram.dispatcher import Dispatcher
from dotenv import load_dotenv, find_dotenv
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters import Text
from db import insert_record
from gpx_parser import Track
from utils import check_user_from_telegram

load_dotenv(find_dotenv())


main_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) \
            .add(KeyboardButton('Добавить')).add(KeyboardButton('Отменить'))


bot = Bot(os.environ.get('BOT_TOKEN'))
dp = Dispatcher(bot)
memory = dict()

async def input_gpx(msg: types.Message):
    try:
        file = msg.document.file_name
        suffix = file.split('.')[-1]
        if suffix == 'gpx':
            memory['file'] = file
            memory['msg_file'] = msg
            await msg.reply('Добавить трек в базу?', reply_markup=main_kb)
    except:
        await msg.reply('Файл не выбран, идите нахер')
    

async def load_record(msg: types.Message):
    user_id = msg.from_user.id #956363314
    if check_user_from_telegram(user_id):
        try:
            file_path = 'C:/data/geo_data/' + memory['file']
            await memory['msg_file'].document.download(file_path)
            if (insert_record(Track(file_path))):
                await msg.reply('The record was added')
            else:
                await msg.reply('Such record was already added earlier')    
        except Exception as err:
            await msg.reply('Something gone wrong')
            await msg.reply(err.args)
        
    else:
        await msg.reply('The user is not authentificated')


dp.register_message_handler(input_gpx, content_types=[ContentType.DOCUMENT])
dp.register_message_handler(load_record, Text('Добавить'))


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp, skip_updates=True)