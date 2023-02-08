import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from price_parser import get_json, get_package

storage = MemoryStorage()
bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot, storage=storage)


load_button = KeyboardButton('/Проверить_цену')
cancel_button = KeyboardButton('/Отмена')
custom_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
custom_keyboard.add(load_button).add(cancel_button)


class FSMCheckPrice(StatesGroup):
    check_name = State()
    get_package = State()
    


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply('Начинаем работу', reply_markup=custom_keyboard)



@dp.message_handler(commands='Проверить_цену', state=None)
async def start_dialog(message: types.Message):
    await FSMCheckPrice.check_name.set()
    await message.reply('Какое лекарство будем проверять?')


@dp.message_handler(state=FSMCheckPrice.check_name)
async def get_price(message: types.Message, state: FSMContext):
    data = get_json(message.text)
    if len(data) == 0:
        await message.reply('Вы допустили ошибку в названии препарата, либо он'
                            'не входит в перечень ЖНВЛП')
        await state.finish()
    else:
        packages = get_package(data)
        message_string = ''
        for key_number, package in enumerate(packages):
            message_string += str(key_number) + '. ' + package + ' \n '
        print(message_string)
        await message.reply(message_string)
        # отправить клавиатуру или инлайн клавиатуру с номерами вариантов
        # лекарственных форм дозиоровок и упаковок

        await FSMCheckPrice.get_package.set()


# @dp.message_handler(state=FSMCheckPrice.get_package)
# async def get_produser(message: types.Message, state: FSMCheckPrice):



@dp.message_handler(state="*", commands='Отмена')
async def cancel_dialog(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Проверка отменена')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)