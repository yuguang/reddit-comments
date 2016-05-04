from peewee import *
db = SqliteDatabase('db.sqlite3')

class Domain(Model):
    month = CharField(max_length=30)
    count = IntegerField() # stores up to 2,147,483,647
    name = CharField(max_length=200)
    class Meta:
        database = db

