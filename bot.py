import os
import json
import datetime
from RreceiptDecoder.qt_to_receipt import read_receipts
from Telegram.TBot import TBot
from database import *
from sessions import SessionsManager
from private.config import bot_token
from private.setup import setup
from decimal import *

texts = {
    "start": """Привет!
Я аггрегатор чеков.

Присылай мне фотографии с QR-кодом с чеков и я буду вытягивать с них информацию о списке покупок, сохранять её для тебя и отдавать в виде удобной таблицы (или таблиц)

Напишите /help для дополнительной информации""",
    "help": """Доступные команды:
/start
/help
/stats - выдает статистику по базе данных (требуются права админа)
/get_sheet - не реализовано
/get_analysis - не реализовано""",
    "stop": """Я засыпаю...""",
    "reject_command": """У вас недостаточно прав для выполнения этой команды""",
    "receipts_added": """Добавленно {count} чеков суммой в {summ:.2f} динар""",
    "no_receipts_added": """Новых чеков не найдено""",
    "stats": """Статистика:
Пользователей: {users}
Чеков отсканировано: {receipts}
Всего позиций куплено: {count}
"""
}


def main():
    # common initialize
    bot = TBot(bot_token, download_path=os.path.abspath("private/downloads"))
    session_manager = SessionsManager(storage=os.path.abspath("private/sessions"))
    main_session = session_manager.get_session("root")
    if "dirty" not in main_session or main_session["dirty"]:
        database_backup(f"private/database")
        main_session["dirty"] = False
    database_init(f"private/database")
    setup()

    def get_user(message) -> BotUser:
        user, created = BotUser.get_or_create(tid=message["from"]["id"])
        return user

    @bot.on_command("/start")
    def command_start(command, message):
        bot.send({
            'chat_id': message["from"]["id"],
            'text': texts["start"]
        })

    @bot.on_command("/help")
    def command_start(command, message):
        bot.send({
            'chat_id': message["chat"]["id"],
            'text': texts["help"]
        })

    @bot.on_command("/stop")
    def command_stop(command, message):
        user = get_user(message)
        if not user.is_admin:
            bot.send({
                'chat_id': message["chat"]["id"],
                'text': texts["reject_command"]
            })
            return

        bot.send({
            'chat_id': message["chat"]["id"],
            'text': texts["stop"]
        })
        bot.stop()
        if main_session["dirty"]:
            database_backup(f"private/database")
            main_session["dirty"] = False
        session_manager.save_all()

    @bot.on_command("/stats")
    def handle_stats(command, message):
        user = get_user(message)
        if not user.is_admin:
            bot.send({
                'chat_id': message["chat"]["id"],
                'text': texts["reject_command"]
            })
            return

        bot.send({
            'chat_id': message["chat"]["id"],
            'text': texts["stats"].format(
                users=BotUser.select().count(),
                receipts=Receipt.select().count(),
                count=Product.select().count(),
            )
        })

    @bot.on_photo
    def handle_photo(file, message):
        receipts = read_receipts(file["local_path"])
        if receipts is not None and len(receipts) > 0:
            session = session_manager.get_session(message["from"]["id"])
            if "receipts" not in session:
                session["receipts"] = []
            r_list = session["receipts"]
            for rec in receipts:
                r_list.append({
                    "file": file,
                    "receipt": rec
                })

    @bot.on_message
    def handle_message(message, commands, photos):
        session = session_manager.get_session(message["from"]["id"])
        if "receipts" not in session:
            return
        # distinct
        receipts = {}
        for entry in session["receipts"]:
            invoice = entry["receipt"]["invoice"]
            if invoice in receipts:
                continue
            receipts[invoice] = entry

        # store to database
        added = 0
        summar = Decimal(0)
        for invoice, entry in receipts.items():
            file = entry["file"]
            receipt = entry["receipt"]
            db_receipt, created = Receipt.get_or_create(
                invoice=receipt['invoice'],
                token=receipt['token'],
                datetime=receipt['datetime'],
                link=receipt['url'],
                total=Decimal(0),
            )
            if not created:
                continue
            main_session["dirty"] = True
            total = Decimal(0)
            for item in receipt['items']:
                Product.create(
                    receipt_id=db_receipt.id,
                    name=item["name"],
                    quantity=item["quantity"],
                    total=Decimal(item["total"]),
                    unitPrice=Decimal(item["unitPrice"]),
                    label=item["label"],
                    labelRate=int(item["labelRate"]),
                    taxBaseAmount=Decimal(item["taxBaseAmount"]),
                    vatAmount=Decimal(item["vatAmount"]),
                )
                total += Decimal(item["total"])
            db_receipt.total = total
            db_receipt.save()
            added += 1
            summar += total

        if added > 0:
            bot.send({
                'chat_id': message["chat"]["id"],
                'text': texts["receipts_added"].format(count=added, summ=summar)
            })
        else:
            bot.send({
                'chat_id': message["chat"]["id"],
                'text': texts["no_receipts_added"]
            })

        del session["receipts"]

    @bot.on_update
    def handle_update():
        session_manager.update()

    bot.run()


if __name__ == "__main__":
    main()
