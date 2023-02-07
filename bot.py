import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from price_parser import get_json
TOKEN='5002789883:AAHyYXw4E7ayfpRYbQhQbs5ZfplmX306o-4'
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)


load_button = KeyboardButton('/Проверить_цену')
cancel_button = KeyboardButton('/Отмена')
custom_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
custom_keyboard.add(load_button).add(cancel_button)


class FSMCheckPrice(StatesGroup):
    hello = State()
    check_name = State()


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Начинаем работу', reply_markup=custom_keyboard)



@dp.message_handler(commands='Проверить_цену', state=None)
async def start_dialog(message: types.Message):
    await FSMCheckPrice.hello.set()
    await message.reply('Какое лекарство будем проверять?')


@dp.message_handler(state=FSMCheckPrice.hello)
async def get_price(message: types.Message, state: FSMContext):
    data = get_json(message.text)
    print(data)
    await message.reply(data)

    await state.finish()


@dp.message_handler(state="*", commands='Отмена')
async def cancel_dialog(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Проверка отменена')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)