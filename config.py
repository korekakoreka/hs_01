from flask_login import UserMixin
from peewee import ForeignKeyField
from peewee import SqliteDatabase, Model, IntegerField, CharField, TextField, BooleanField, DateTimeField
from datetime import datetime

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


class Progress(Model):
    user = ForeignKeyField(User, backref='progresses')
    video_id = CharField()
    completed = BooleanField(default=False)
    timestamp = DateTimeField(default=datetime.now)

    class Meta:
        database = db


class Feedback(Model):
    user = ForeignKeyField(User, backref='Feedbacks')
    content = TextField()
    timestamp = DateTimeField(default=datetime.now)

    class Meta:
        database = db


class Question(Model):
    video_id = CharField()
    content = TextField()

    class Meta:
        database = db


class Choice(Model):
    question = ForeignKeyField(Question, backref='choices')
    content = TextField()
    is_correct = BooleanField(default=False)

    class Meta:
        database = db


db.create_tables([User, Lesson, Progress, Feedback, Question, Choice])
