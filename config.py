from flask_login import UserMixin
from peewee import SqliteDatabase, Model, IntegerField, CharField, TextField

db = SqliteDatabase("db.sqlite")


class User(UserMixin, Model):
    name = CharField(unique=True)
    school_year = CharField(unique=True)
    class_room = CharField(unique=True)
    number = CharField(unique=True)
    password = TextField()

    class Meta:
        database = db
        table_name = "users"


db.create_tables([User])
