import os
import datetime
import shutil
from peewee import *

db = SqliteDatabase(None)


def database_backup(name):
    timestamp = datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    src = os.path.abspath(f'{name}.db')
    if os.path.exists(src):
        dst = os.path.abspath(f'{name}_{timestamp}.db')
        shutil.copy(src, dst)


def database_init(name):
    path = os.path.abspath(f'{name}.db')
    db.init(path)
    db.connect()
    db.create_tables([BotUser, Receipt, Product])


class BotUser(Model):
    tid = BigIntegerField(primary_key=True)
    is_admin = BooleanField(default=False)

    class Meta:
        database = db  # This model uses the "people.db" database.


class Receipt(Model):
    id = AutoField()
    uid = BigIntegerField()
    invoice = CharField(64, unique=True)
    token = CharField(64)
    datetime = DateTimeField(default=datetime.datetime.now)
    link = CharField(2048)
    total = DecimalField()

    class Meta:
        database = db  # This model uses the "people.db" database.


class Product(Model):
    id = AutoField()
    uid = BigIntegerField()
    receipt_id = ForeignKeyField(Receipt)
    name = CharField()
    quantity = IntegerField()
    total = DecimalField()
    unitPrice = DecimalField()
    label = CharField(4)
    labelRate = IntegerField()
    taxBaseAmount = DecimalField()
    vatAmount = DecimalField()
    datetime = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db  # This model uses the "people.db" database.


def main():
    db.connect()
    db.create_tables([Receipt, Product])


if __name__ == "__main__":
    main()
