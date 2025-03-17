from TBot import TBot
from private.config import bot_token


start_message = """Привет!
Я аггрегатор чеков.

Присылай мне фотографии с QR-кодом с чеков и я буду вытягивать с них информацию о списке покупок, сохранять её для тебя и отдавать в виде удобной таблицы (или таблиц)

Доступные команды:
/start
/help
/get_sheet - не реализовано
/get_analysis - не реализовано
"""

help_message = """Команда не реализована"""


def main():
    bot = TBot(bot_token)

    @bot.on_photo
    def handle_photo(file, message):
        print(f"Handle photo:\n{file}\n")

    @bot.on_command("/start")
    def command_start(command, message):
        print(f"Handle command:\n{command}\n")

    @bot.on_command("/stop")
    def command_start(command, message):
        print(f"Handle command:\n{command}\n")
        bot.stop()

    bot.run()


def main_olld():
    bot = Bot(token=bot_token)
    dp = Dispatcher()

    @dp.message(commands=['start'])
    async def process_start_command(message: types.Message):
        await message.reply(start_message)

    @dp.message_handler(commands=['help'])
    async def process_start_command(message: types.Message):
        await message.reply(help_message)

    @dp.message_handler(content_types=['photo'])
    async def photo_handler(message: types.Message, state: FSMContext):
        # we are here if the first message.content_type == 'photo'

        # save the largest photo (message.photo[-1]) in FSM, and start photo_counter
        await state.update_data(photo_0=message.photo[-1], photo_counter=0)

        await state.set_state('next_photo')

    @dp.message_handler(content_types=['photo'], state='next_photo')
    async def next_photo_handler(message: types.Message, state: FSMContext):
        # we are here if the second and next messages are photos

        async with state.proxy() as data:
            data['photo_counter'] += 1
            photo_counter = data['photo_counter']
            data[f'photo_{photo_counter}'] = message.photo[-1]
        await state.set_state('next_photo')

    @dp.message_handler(state='next_photo')
    async def not_foto_handler(message: types.Message, state: FSMContext):
        # we are here if the second and next messages are not photos

        async with state.proxy() as data:
            # here you can do something with data dictionary with all photos
            print(data)

        await state.finish()

    dp.start_polling(bot)


if __name__ == "__main__":
    main()
