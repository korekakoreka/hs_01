from flask_login import UserMixin
from peewee import ForeignKeyField
from peewee import SqliteDatabase, Model, IntegerField, CharField, TextField

db = SqliteDatabase("db.sqlite")


class User(UserMixin, Model):
    name = CharField(unique=True)
    school_year = CharField()
    class_room = CharField()
    number = CharField()
    password = TextField()

    class Meta:
        database = db
        table_name = "users"  # 明示的にテーブル名を指定

# 授業モデル
class Lesson(Model):
    title = CharField()  # 授業のタイトル（数学、国語、英語など）
    subject = CharField()  # 科目名
    youtube_url = CharField()  # YouTubeの限定配信URL
    user = ForeignKeyField(User, backref='lessons')  # ユーザー（生徒）と関連付け

    class Meta:
        database = db
        table_name = "lessons"  # 授業テーブルの名前を明示


db.create_tables([User, Lesson])
