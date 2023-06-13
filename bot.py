import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, ContentTypeFilter
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.types import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup)
from aiogram.utils.callback_data import CallbackData


from price_parser import get_json, get_package, get_producer, get_price


async def setup_bot_commands(dp):
    commands = [
        BotCommand(command='/start', description='Начать работу бота'),
        BotCommand(command='/cancel', description='Прервать работу бота')
        ]
    await dp.bot.set_my_commands(commands)


storage = MemoryStorage()
bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot, storage=storage)


load_button = KeyboardButton('Проверить цену')
custom_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
custom_keyboard.add(load_button)

collback_data = CallbackData('producer', 'id')



class FSMCheckPrice(StatesGroup):
    check_name = State()
    get_producer = State()
    get_package = State()
    check_current_price = State()

def make_inline_keyboard(data_list: list) -> InlineKeyboardMarkup:

    producer_inline_keyboard = InlineKeyboardMarkup(row_width=3)
    for number, producer in enumerate(data_list):
        producer_button = InlineKeyboardButton(
            text=number+1,
            callback_data=collback_data.new(id=number)
        )
        producer_inline_keyboard.insert(producer_button)
    return producer_inline_keyboard
    



@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Начинаем работу', reply_markup=custom_keyboard)



@dp.message_handler(Text(equals='Проверить цену'), state=None)
async def start_dialog_hendler(message: types.Message):
    await FSMCheckPrice.check_name.set()
    await message.reply('Какое лекарство будем проверять?')


@dp.message_handler(state=FSMCheckPrice.check_name)
async def get_price_handler(message: types.Message, state: FSMContext):
    data = get_json(message.text)
    if len(data) == 0:
        await message.reply('Название препарата указано неправильно либо он'
                            ' не входит в перечень ЖНВЛП')
        await state.finish()
    elif type(data) is str:
        await message.reply(data)
        await state.finish()
    else:
        producers = get_producer(data)
        
        message_string = ''
        for key_number, producer in enumerate(producers):
            message_string += str(key_number+1) + ')\n' + producer + ' \n \n'
        await message.reply(
            'выберите производителя \n\n' + message_string,
            reply_markup = make_inline_keyboard(producers)
        )
        await state.update_data(parsed_data=data)
        await state.update_data(producers=producers)
        await FSMCheckPrice.get_producer.set()

    


@dp.callback_query_handler(
    collback_data.filter(),
    state=FSMCheckPrice.get_producer
)
async def get_package_handler(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    current_produсer = data['producers'][int(callback_data['id'])]
    await state.update_data(current_produсer=current_produсer)
    packages = get_package(data['parsed_data'], current_produсer)
    await state.update_data(packeges=packages)
    message_string = ''
    for key_number, package in enumerate(packages):
        message_string += str(key_number+1) + ')\n' + package + ' \n \n'
    await callback.message.answer(
            'выберите упаковку \n\n' + message_string,
            reply_markup = make_inline_keyboard(packages)
        )
    await FSMCheckPrice.check_current_price.set()


@dp.callback_query_handler(
    collback_data.filter(),
    state=FSMCheckPrice.check_current_price
)
async def check_price_handler(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    parsed_data = data['parsed_data']
    current_produсer = data['current_produсer']
    packages = data['packeges']
    current_packege = packages[int(callback_data['id'])]
    final_price = get_price(parsed_data, current_produсer, current_packege)
    await callback.message.answer(
            f'Максимальная цена для данного преперата {final_price}'
        )
    await state.finish()


@dp.message_handler(commands=['cancel'], state='*')
async def cancel_dialog(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Проверка отменена')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=setup_bot_commands)