import os
import json
import datetime
import csv
from RreceiptDecoder.qt_to_receipt import read_receipts_from_image, read_receipts_from_urls
from Telegram.TBot import TBot, get_urls
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
/dump_sheet - складывает данные в csv-таблицу. Пока не присылает, потому что у телеги есть ограничения и не понятен масшта данных
/get_sheet - не реализовано
/get_analysis - не реализовано""",
    "stop": """Я засыпаю...""",
    "reject_command": """У вас недостаточно прав для выполнения этой команды""",
    "receipts_added": """Добавленно {count} чеков суммой в {summ:.2f} динар""",
    "no_receipts_added": """Новых чеков не найдено""",
    "unknown_receipts": """Не удалось распарсить некоторые данные: {count}""",
    "stats": """Статистика:
Пользователей: {users}
Чеков отсканировано: {receipts}
Всего позиций куплено: {count}
""",
    "dumps": """Данные сохранены в:\n\n{files}"""
}


def main():
    # common initialize
    bot = TBot(bot_token, download_path=os.path.abspath("private/downloads"))
    session_manager = SessionsManager(storage=os.path.abspath("private/sessions"))
    main_session = session_manager.get_session("root")
    if "dirty" not in main_session or main_session["dirty"]:
        database_backup(f"private/database")
        main_session["dirty"] = False
        main_session["broken_qrs"] = []
    database_init(f"private/database")
    setup()

    def get_user(subject) -> BotUser | None:
        tid = None
        if isinstance(subject, dict):
            tid = subject["from"]["id"]
        if isinstance(subject, int):
            tid = subject
        if tid is not None:
            user, created = BotUser.get_or_create(tid=tid)
            return user
        return None

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
        if user is None or not user.is_admin:
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
        if user is None or not user.is_admin:
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

    @bot.on_command("/dump_sheet")
    def handle_dump_sheet(command, message):
        user = get_user(message)
        timestamp = datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")

        file_products = os.path.abspath(f'private/dumps/{timestamp}_user_{user.tid}_products_.csv')
        query = Product.select().where(Product.uid == user.tid).order_by(Product.datetime)
        with open(file_products, 'w', newline='', encoding='utf8') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            header = ['receipt_id', 'datetime',
                      'name', 'quantity', 'total', 'unitPrice',
                      'label', 'labelRate', 'taxBaseAmount', 'vatAmount']
            csv_writer.writerow(header)
            for product in query:
                csv_writer.writerow([
                    product.receipt_id, product.datetime,
                    product.name, product.quantity, product.total, product.unitPrice,
                    product.label, product.labelRate, product.taxBaseAmount, product.vatAmount,
                ])
            csv_writer.writerow([''] * len(header))

        file_receipts = os.path.abspath(f'private/dumps/{timestamp}_user_{user.tid}_receipts_.csv')
        query = Receipt.select().where(Receipt.uid == user.tid).order_by(Receipt.datetime)
        with open(file_receipts, 'w', newline='', encoding='utf8') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            header = ['datetime', 'invoice', 'token', 'total', 'link']
            csv_writer.writerow(header)
            for receipt in query:
                csv_writer.writerow([
                    receipt.datetime,
                    receipt.invoice,
                    receipt.token,
                    receipt.total,
                    receipt.link
                ])
            csv_writer.writerow([''] * len(header))

        result = "\n\n".join([file_products, file_receipts])
        print(f"Files saved: {result}")
        bot.send({
            'chat_id': message["chat"]["id"],
            'text': texts["dumps"].format(files=result)
        })

    def handle_receipts(session, receipts, file=None):
        if receipts is not None and len(receipts) > 0:
            if "receipts" not in session:
                session["receipts"] = []
            r_list = session["receipts"]
            for rec in receipts:
                r_list.append({
                    "file": file,
                    "receipt": rec
                })
        elif file is not None:
            if "no-receipts" not in session:
                session["no-receipts"] = []
            session["no-receipts"].append(file)

    @bot.on_photo
    def handle_photo(message, file):
        session = session_manager.get_session(message["from"]["id"])
        receipts = read_receipts_from_image(file["local_path"])
        handle_receipts(session, receipts, file)

    @bot.on_photos_handled
    def handle_photos_complete(message, photos):
        session = session_manager.get_session(message["from"]["id"])
        if "no-receipts" in session:
            bot.send({
                'chat_id': message["chat"]["id"],
                'text': texts["unknown_receipts"].format(count=len(session["no-receipts"]))
            })
            main_session["broken_qrs"].extend(session["no-receipts"])
            session_manager.save_session("root")
            del session["no-receipts"]

    @bot.on_message
    def handle_message(message, **kwargs):
        urls = get_urls(message)
        if len(urls) > 0:
            session = session_manager.get_session(message["from"]["id"])
            receipts = read_receipts_from_urls(*urls)
            handle_receipts(session, receipts)

    @bot.on_messages_handled
    def after_messages_handled(frame):
        user = get_user(frame["from"])
        session = session_manager.get_session(frame["from"])
        if "receipts" in session:
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
                    uid=user.tid,
                    invoice=receipt['invoice'],
                    token=receipt['token'],
                    defaults={
                        'datetime': receipt['datetime'],
                        'link': receipt['url'],
                        'total': Decimal(0)
                    })
                if not created:
                    continue
                main_session["dirty"] = True
                total = Decimal(0)
                for item in receipt['items']:
                    Product.create(
                        uid=user.tid,
                        receipt_id=db_receipt.id,
                        name=item["name"],
                        quantity=item["quantity"],
                        total=Decimal(item["total"]),
                        unitPrice=Decimal(item["unitPrice"]),
                        label=item["label"],
                        labelRate=int(item["labelRate"]),
                        taxBaseAmount=Decimal(item["taxBaseAmount"]),
                        vatAmount=Decimal(item["vatAmount"]),
                        datetime=db_receipt.datetime,
                    )
                    total += Decimal(item["total"])
                db_receipt.total = total
                db_receipt.save()
                added += 1
                summar += total

            if added > 0:
                bot.send({
                    'chat_id': frame["chat"],
                    'text': texts["receipts_added"].format(count=added, summ=summar)
                })
            else:
                bot.send({
                    'chat_id': frame["chat"],
                    'text': texts["no_receipts_added"]
                })

            del session["receipts"]

    @bot.on_update
    def handle_update():
        session_manager.update()
        print("\n\n\n===update===\n\n\n")

    bot.run()


if __name__ == "__main__":
    main()
