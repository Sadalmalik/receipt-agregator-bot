from peewee import *

db = SqliteDatabase('accounting.db')


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
