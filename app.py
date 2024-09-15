from flask import Flask, flash, redirect, render_template, request, url_for, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import db, User, Progress, Feedback, Lesson, Question, Choice, QuizResult
from datetime import datetime


app = Flask(__name__)


@app.route("/some_route")
def some_function():
    try:
        # ユーザーを取得
        user = User.get(User.id == 3)  # id=3のユーザーを取得しようとする
    except User.DoesNotExist:  # ユーザーが存在しない場合のエラーハンドリング
        flash("ユーザーが見つかりませんでした")
        return redirect(url_for("index"))


# # 新しいユーザーを作成
# new_user = User.create(
#     name="Bob",
#     school_year="2024",
#     class_room="3A",
#     number="12",
#     password=generate_password_hash("password123"),
# )

app = Flask(__name__)
app.secret_key = "new_secret_key_123456789"  # 新しいシークレットキー
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
        if not request.form["name"] or not request.form["password"] or not request.form["school_year"]:
            flash("未入力の項目があります。")
            return redirect(request.url)
        if User.select().where(User.name == request.form["name"]).exists():
            flash("その名前はすでに使われています。")
            return redirect(request.url)

        User.create(
            name=request.form["name"],
            school_year=request.form["school_year"],
            class_room=request.form["class_room"],
            number=request.form["number"],
            password=generate_password_hash(request.form["password"]),
        )
        flash("ユーザー登録が完了しました！")
        return redirect("/login")

    return render_template("register.html")


# ログインフォームの表示・ログイン処理
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not request.form["password"] or not request.form["name"]:
            flash("未入力の項目があります。")
            return redirect(request.url)

        user = User.select().where(User.name == request.form["name"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            flash(f"ようこそ！ {user.name} さん")
            return redirect("/")
        flash("認証に失敗しました")
    return render_template("login.html")


# ログアウト機能
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("ログアウトしました")
    return redirect(url_for("index"))


# セッションを完全にクリア
@app.route("/reset_session")
def reset_session():
    session.clear()  # セッションを完全にクリア
    flash("セッションがリセットされました")
    return redirect(url_for("index"))


# ホームページ
@app.route("/")
def index():
    print(f"Current User: {current_user}")
    print(f"Is Authenticated: {current_user.is_authenticated}")

    if current_user.is_authenticated:
        print(f"Logged in as: {current_user.name}")
        # ログインユーザーに関連付けられた授業を取得
        lessons = Lesson.select().where(Lesson.user == current_user.id)
        return render_template("index.html", name=current_user.name, lessons=lessons)
    else:
        return render_template("index.html")  # ログインしていない場合の表示


# ダッシュボード
@app.route("/dashboard")
@login_required
def dashboard():
    lessons = Lesson.select().where(Lesson.user == current_user.id)
    quiz_results = QuizResult.select().where(QuizResult.user == current_user.id)
    progresses = Progress.select().where(Progress.user == current_user.id)
    completed_videos = [progress.video_id for progress in progresses if progress.completed]

    badges = award_badge(current_user)
    progress_rate = get_student_progress(current_user.id)

    return render_template(
        "dashboard.html",
        lessons=lessons,
        quiz_results=quiz_results,
        completed_videos=completed_videos,
        badges=badges,
        progress_rate=progress_rate,
    )


@app.route("/lesson/<int:lesson_id>")
@login_required
def lesson_detail(lesson_id):
    try:
        # 授業を取得する
        lesson = Lesson.get(Lesson.id == lesson_id)
        return render_template("lesson_detail.html", lesson=lesson)
    except Lesson.DoesNotExist:  # type: ignore[attr-defined]
        # 授業が存在しない場合のエラーハンドリング
        flash("授業が見つかりません")
        return redirect(url_for("index"))


# フィードバック送信
@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        content = request.form.get("content")
        if content:
            Feedback.create(user=current_user.id, content=content)
            flash("フィードバックが送信されました！")
            return redirect(url_for("dashboard"))
        else:
            flash("フィードバックを入力してください。")
    return render_template("feedback.html")


# バッジ付与のロジック
def award_badge(user):
    progress = get_student_progress(user.id)
    if progress > 50:
        return "進捗マスター"
    return "バッジなし"


# 学習進捗の取得
def get_student_progress(user_id):
    total_lessons = Lesson.select().count()
    completed_lessons = Progress.select().where(Progress.user == user_id, Progress.completed == True).count()

    if total_lessons > 0:
        return (completed_lessons / total_lessons) * 100  # 進捗率を計算
    return 0


# テーブルの作成
def create_tables():
    with db:
        db.create_tables([User, Progress, Feedback, Lesson, Question, Choice, QuizResult], safe=True)


# アプリケーションの起動
if __name__ == "__main__":
    if db.is_closed():
        db.connect()  # データベースが閉じている場合は接続

    create_tables()  # テーブルが存在しない場合に作成
    app.run(host="127.0.0.1", port=8000, debug=True)
