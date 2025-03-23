import os
import json
from RreceiptDecoder.qt_to_receipt import read_receipts
from Telegram.TBot import TBot
from database import BotUser, init_database
from sessions import SessionsManager
from private.config import bot_token
from private.setup import setup

messages = {
    "start": """Привет!
Я аггрегатор чеков.

Присылай мне фотографии с QR-кодом с чеков и я буду вытягивать с них информацию о списке покупок, сохранять её для тебя и отдавать в виде удобной таблицы (или таблиц)

Напишите /help для дополнительной информации""",
    "help": """Доступные команды:
/start
/help
/get_sheet - не реализовано
/get_analysis - не реализовано""",
    "stop": """Я засыпаю...""",
    "reject_command": """У вас недостаточно прав для выполнения этой команды"""
}


bot = TBot(bot_token)
sessionManager = SessionsManager(storage=os.path.abspath("private/sessions"))
init_database(f"private/database.db")
setup()


def main():
    def get_user(message) -> BotUser:
        user, created = BotUser.get_or_create(tid=message["from"]["id"])
        return user

    @bot.on_command("/start")
    def command_start(command, message):
        bot.send({
            'chat_id': message["from"]["id"],
            'text': messages["start"]
        })

    @bot.on_command("/help")
    def command_start(command, message):
        bot.send({
            'chat_id': message["chat"]["id"],
            'text': messages["help"]
        })

    @bot.on_command("/stop")
    def command_stop(command, message):
        print(f"Handle command:\n{command}\n")
        user = get_user(message)
        if not user.is_admin:
            bot.send({
                'chat_id': message["chat"]["id"],
                'text': messages["reject_command"]
            })
            return
        bot.send({
            'chat_id': message["chat"]["id"],
            'text': messages["stop"]
        })
        bot.stop()

    @bot.on_photo
    def handle_photo(file, message):
        print(f"Handle photo:\n{file}\n")
        receipts = read_receipts(file["local_path"])
        if receipts and len(receipts)>0:
            session = sessionManager.get_session(message["from"]["id"])
            r_list = session.get("receipts", [])
            for rec in receipts:
                r_list.append({
                    "file": file,
                    "receipt": rec
                })

    @bot.on_message
    def handle_photo(message, commands, photos):
        session = sessionManager.get_session(message["from"]["id"])
        bot.send({
            'chat_id': message["chat"]["id"],
            'text': f"Session:\n\n'{json.dumps(session, indent=4)}"
        })

    bot.run()


if __name__ == "__main__":
    main()
