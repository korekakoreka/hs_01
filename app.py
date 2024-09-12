from flask import Flask, flash, redirect, render_template, request
from flask_login import LoginManager, login_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from config import db, User, Progress, Feedback, Lesson
from flask_login import current_user
from datetime import datetime
print(db.get_tables())


app = Flask(__name__)
app.secret_key = "secret"
login_manager = LoginManager()
login_manager.init_app(app)


# Flask-Loginがユーザー情報を取得するためのメソッド
@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

# ユーザー登録フォームの表示・登録処理
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # データの検証
        if not request.form["name"] or not request.form["password"] or not request.form["school_year"]:
            flash("未入力の項目があります。")
            return redirect(request.url)
        if User.select().where(User.name == request.form["name"]):
            flash("その名前はすでに使われています。")
            return redirect(request.url)

        # ユーザー登録
        User.create(
             name=request.form["name"],
             school_year=request.form["school_year"],
             class_room=request.form["class_room"],
             number=request.form["number"],
             password=generate_password_hash(request.form["password"])
        )   
        flash("ユーザー登録が完了しました！")
        return redirect("/login")
           
    return render_template("register.html")

# ログインフォームの表示・ログイン処理
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # データの検証 
        if not request.form["password"] or not request.form["name"]:
            flash("未入力の項目があります。")
            return redirect(request.url)
        # ここでユーザーを認証し、OKならログインする
        user = User.select().where(User.name == request.form["name"]).first()
        if user is not None and check_password_hash(user.password,  request.form["password"]):
            login_user(user)
            flash(f"ようこそ！ {user.name} さん")
            return redirect("/")
        flash("認証に失敗しました")

    return render_template("login.html")

@app.route("/mark_completed/<video_id>", methods=["POST"])
@login_required
def mark_completed(video_id):
    Progress.create(user=current_user.id, video_id=video_id, completed=True)
    flash("動画が完了としてマークされました！")
    return redirect("/videos")


@app.route("/")
def index():
    return render_template("index.html")

# 動画視聴ページ
@app.route("/videos")
@login_required
def videos():
    return render_template("videos.html")

@app.route("/dashboard")
@login_required
def dashboard():
    # ログインユーザーに関連付けられた授業を取得
    lessons = Lesson.select().where(Lesson.user == current_user.id)
    return render_template("dashboard.html", lessons=lessons)
    # ユーザーの進捗をデータベースから取得
    progresses = Progress.select().where(Progress.user == current_user.id)
    completed_videos = [progress.video_id for progress in progresses if progress.completed]
    return render_template("dashboard.html", completed_videos=completed_videos)

@app.route("/lesson/<int:lesson_id>")
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.get(Lesson.id == lesson_id)
    return render_template("lesson_detail.html", lesson=lesson)


# 学習進捗の取得
def get_student_progress(user_id):
    progresses = Progress.select().where(Progress.user == user_id)
    completed_videos = progresses.count()
    return completed_videos


# バッジを与える基準を定義
def award_badge(user):
    # 進捗に基づいてバッジを付与
    progress = get_student_progress(user.id)
    if progress > 50:
        # バッジ付与のロジック
        pass


# 進捗確認とバッジ付与のルート
@app.route("/progress")
@login_required
def progress():
    award_badge(current_user)
    return render_template("progress.html", progress=get_student_progress(current_user.id))


def create_tables():
    with db:
        # ここで必要なテーブルを作成
        db.create_tables([User, Progress], safe=True)


@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        content = request.form["content"]
        if content:
            # フィードバックをデータベースに保存（`Feedback` モデルが必要）
            Feedback.create(user=current_user.id, content=content)
            flash("フィードバックが送信されました。")
            return redirect("/dashboard")
        else:
            flash("フィードバック内容を入力してください。")
    return render_template("feedback.html")


if __name__ == '__main__':
    # データベースが接続されていない場合のみ接続する
    if db.is_closed():
        db.connect()

    create_tables()  # テーブルが存在しない場合に作成する
    app.run(host="127.0.0.1", port=8000, debug=True)  # Flaskアプリケーションを起動
