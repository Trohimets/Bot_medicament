import os
import logging
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, ContentTypeFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup)
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageNotModified
from contextlib import suppress


from price_parser import get_json, get_package, get_producer, get_price
import tg_analytic


ID = None
chat_id = os.getenv('CHAT_ID')

# logging.basicConfig(
#     level=logging.DEBUG,
#     filename='main.log',
#     format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
#     filemode='w'
# )


async def setup_bot_commands(dp):
    commands = [
        BotCommand(command='/start', description='Начать работу бота'),
        BotCommand(command='/cancel', description='Прервать работу бота')
        ]
    await dp.bot.set_my_commands(commands)


storage = MemoryStorage()
bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot, storage=storage)

callback_produser_data = CallbackData('producer', 'action')

@dp.message_handler(commands=['moderator'], is_chat_admin=True)
async def take_statistics_command(message: types.Message):
    global ID
    ID =message.from_user.id
    await bot.send_message(message.from_user.id, 'Вы вошли в режим, который дает возможность ознакомиться со статистикой')
    await message.delete()


class FSMCheckPrice(StatesGroup):
    # check_name = State()
    get_producer = State()
    get_package = State()
    check_current_price = State()
    get_appeal_text = State()
    get_appeal_photo = State()


def make_inline_producer_keyboard(data_list: list, start: int) -> InlineKeyboardMarkup:
    inline_keyboard = InlineKeyboardMarkup(row_width=3)
    if start != 0:
        inline_keyboard.insert(
            InlineKeyboardButton(
                text='⬅️ Вернуться',
                callback_data=callback_produser_data.new(action='decr')
            )
        )
    inline_keyboard.insert(
        InlineKeyboardButton(
            text='Выбрать',
            callback_data=callback_produser_data.new(action=start)
        )
    )
    if start < len(data_list)-1:
        inline_keyboard.insert(
            InlineKeyboardButton(
                text='Другой ➡️',
                callback_data=callback_produser_data.new(action='incr')
            )
        )
    return inline_keyboard

async def update_producer_keyboard(message: types.Message, start: int, producers: list):
    with suppress(MessageNotModified):
        await message.edit_text(
            f'Выберите производителя\n\n{producers[start]}',
            reply_markup=make_inline_producer_keyboard(producers, start)
            )

def make_inline_package_keyboard(data_list: list, start: int) -> InlineKeyboardMarkup:
    producer_inline_keyboard = InlineKeyboardMarkup(row_width=1)
    if start != 0:
        producer_inline_keyboard.add(
            InlineKeyboardButton(
                text="⬅️ Вернуться",
                callback_data=callback_produser_data.new(action='decr')
            )
        )
    producer_inline_keyboard.add(
        InlineKeyboardButton(
            text='Выбрать',
            callback_data=callback_produser_data.new(action=start)
        )
    )
    if start < len(data_list)-1:
        producer_inline_keyboard.add(
            InlineKeyboardButton(
                text="Другая ➡️",
                callback_data=callback_produser_data.new(action='incr')
            )
        )
    return producer_inline_keyboard


async def update_package_keyboard(message: types.Message, start: int, packages: list):
    with suppress(MessageNotModified):
        await message.edit_text(
            f'Выберите упаковку\n\n{packages[start]}',
            reply_markup=make_inline_package_keyboard(packages, start)
        )


@dp.callback_query_handler(callback_produser_data.filter(action=['incr', 'decr']), state=FSMCheckPrice.get_producer)
async def callbacks_produser_paginated_handler(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    action = callback_data["action"]
    data = await state.get_data()
    if action == "incr":
        start = data['current_item'] + 1
        await state.update_data(current_item=start)
        await update_producer_keyboard(call.message, start, data['producers'])
    elif action == "decr":
        start = data['current_item'] - 1
        await state.update_data(current_item=0)
        await update_producer_keyboard(call.message, start, data['producers'])
    await call.answer()


@dp.callback_query_handler(callback_produser_data.filter(action=['incr', 'decr']), state=FSMCheckPrice.check_current_price)
async def callbacks_price_paginated_handler(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    action = callback_data["action"]
    data = await state.get_data()
    if action == "incr":
        start = data['current_item'] + 1
        await state.update_data(current_item=start)
        await update_package_keyboard(call.message, start, data['packages'])
    elif action == "decr":
        start = data['current_item'] - 1
        await state.update_data(current_item=0)
        await update_package_keyboard(call.message, start, data['packages'])
    await call.answer()

# @dp.message_handler()
# async def get_chat_id(message):
#     print(message)

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    tg_analytic.statistics(message.chat.id, message.text)
    await message.reply('Приступим. Введите название лекарства с учетом регистра')


@dp.message_handler(commands=['cancel'], state='*')
async def cancel_dialog(message: types.Message, state: FSMContext):
    tg_analytic.statistics(message.chat.id, message.text)
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Текущая проверка отменена. Вы можете ввести новое название для поиска')



@dp.message_handler(commands=['статистика'], state='*')
async def analitics_command(message: types.Message, state: FSMContext):
    if message.chat.id > 0:
        pass
    else:
        current_state = await state.get_state()
    # if message.text[:10] == 'статистика' or message.text[:10] == 'Cтатистика':
        st = message.text.split(' ')
        messages = tg_analytic.analysis(st,message.chat.id)
        await bot.send_message(message.chat.id, messages)


@dp.message_handler(state=None)
async def get_price_handler(message: types.Message, state: FSMContext):
    tg_analytic.statistics(message.chat.id, message.text)
    data = get_json(message.text)
    if len(data) == 0:
        await message.reply('Название препарата указано неправильно либо он'
                            ' не входит в перечень ЖНВЛП. Проверьте правильность написания, включая наличие заглавных букв')
        await state.finish()
        await message.answer('Какое лекарство будем проверять?')
    elif type(data) is str:
        await message.reply(data)
        state.finish()
        await message.answer('Какое лекарство будем проверять?')
    else:
        producers = get_producer(data)
        
        message_string = ''
        for key_number, producer in enumerate(producers):
            message_string += str(key_number+1) + ')\n' + producer + ' \n \n'
        await message.reply(
            f'Выберите производителя\n\n{producers[0]}',
            reply_markup=make_inline_producer_keyboard(producers, 0) # 0 - начало списка
        )
        await state.update_data(current_item=0)
        await state.update_data(parsed_data=data)
        await state.update_data(producers=producers)
        await FSMCheckPrice.get_producer.set()

    
@dp.callback_query_handler(
    callback_produser_data.filter(),
    state=FSMCheckPrice.get_producer
)
async def get_package_handler(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    current_produсer = data['producers'][int(callback_data['action'])]
    await state.update_data(current_produсer=current_produсer)
    packages = get_package(data['parsed_data'], current_produсer)
    await state.update_data(packages=packages)
    # for key_number, package in enumerate(packages):
    #     message_string += str(key_number+1) + ')\n' + package + ' \n \n'
    await state.update_data(current_item=0)
    await update_package_keyboard(call.message, 0, packages)
    # await callback.message.answer(
    #         packages[0],
    #         reply_markup = make_inline_keyboard(packages, 0) # 0 - начало списка
    #     )
    await FSMCheckPrice.check_current_price.set()


@dp.callback_query_handler(
    callback_produser_data.filter(),
    state=FSMCheckPrice.check_current_price
)
async def check_price_handler(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    parsed_data = data['parsed_data']
    current_produсer = data['current_produсer']
    packages = data['packages']
    current_packege = packages[int(callback_data['action'])]
    final_price = get_price(parsed_data, current_produсer, current_packege)
    await callback.message.answer(
            f'Максимальная цена для данного преперата {final_price} руб. \n\n' +
            f'Если вы купили препарат дороже, то в ответном сообщении ' +
            f'отправьте следующие данные:\n1) Адрес аптеки, в которой вы ' +
            f'приобрели препарат.\n2) Ваши фамилию, имя и отчество. \n3) Ваш ' +
            f'контактный телефон. \n\nИли нажмите синюю кнопку "Menu" и прервите работу бота,' +
            f' если хотите начать проверку другого препарата.'
        )
    
    await FSMCheckPrice.get_appeal_text.set()

@dp.message_handler(
        state=FSMCheckPrice.get_appeal_text
)
async def get_appeal_text(message: types.Message, state: FSMContext):
    # appeal_text = message.text
    await state.update_data(appeal_text = message.text)
    await message.reply(
        'В следующем сообщении отправьте фото на котором разборчиво видны:' +
        ' чек, наименование производителя и дозировка препарата.'
    )
    await FSMCheckPrice.get_appeal_photo.set()


@dp.message_handler(
    content_types=types.ContentType.PHOTO,
    state=FSMCheckPrice.get_appeal_photo
)
async def get_appeal(message: types.Message, state: FSMContext):
    await bot.send_photo(chat_id, message.photo[-1].file_id)
    data = await state.get_data()
    await bot.send_message(chat_id, data['appeal_text'])
    await state.finish()
    await message.reply('Спасибо за обращение. '
                        'Ваша жалоба отправлена на рассмотрение')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=setup_bot_commands)
