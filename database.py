from peewee import *

db = SqliteDatabase(None)


def init_database(name):
    db.init(name)
    db.connect()
    db.create_tables([BotUser, Receipt, Product])


class BotUser(Model):
    tid = BigIntegerField()
    is_admin = BooleanField(default=False)

    class Meta:
        database = db  # This model uses the "people.db" database.


class Receipt(Model):
    id = AutoField()
    date = DateField()
    time = TimeField()
    link = CharField(512)

    class Meta:
        database = db  # This model uses the "people.db" database.


class Product(Model):
    id = AutoField()
    receipt_id = ForeignKeyField(Receipt)
    name = CharField()
    quantity = IntegerField()
    total = DecimalField()
    price = DecimalField()
    label = CharField(4)
    labelRate = IntegerField()
    taxBaseAmount = DecimalField()
    vatAmount = DecimalField()

    class Meta:
        database = db  # This model uses the "people.db" database.


def main():
    db.connect()
    db.create_tables([Receipt, Product])


if __name__ == "__main__":
    main()
