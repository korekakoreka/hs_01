from flask import Flask, flash, redirect, render_template, request, url_for, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import db, User, Progress, Feedback, Lesson, Question, Choice, QuizResult
from datetime import datetime
from werkzeug.utils import secure_filename
import sqlite3
import logging


app = Flask(__name__)


# データベース接続用の関数
def get_db_connection():
    conn = sqlite3.connect('db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn


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
app.config['SECRET_KEY'] = 'your_secret_key'

# LoginManager の設定
logging.basicConfig(level=logging.INFO)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



# Flask-Loginがユーザー情報を取得するためのメソッド
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get_by_id(user_id)
    except User.DoesNotExist:
        return None


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


# 仮の授業データ
lessons = [
    {"id": 1, "subject": "数学", "title": "数学1", "youtube_url": "https://www.youtube.com/embed/L5qpin1xO_s"},
    {"id": 2, "subject": "英語", "title": "英語1", "youtube_url": "https://www.youtube.com/embed/WkipCckEMUs"},   
    {"id": 3, "subject": "国語", "title": "国語1", "youtube_url": "https://www.youtube.com/embed/O-VkiN1dfNs"}
]


# ホームページ
@app.route("/")
def index():
    logging.info("Fetching all lessons")
    lessons = Lesson.select()
    logging.info(f"Total lessons fetched: {len(lessons)}")

    if current_user.is_authenticated:
        logging.info(f"User {current_user.name} is authenticated")
        return render_template("index.html", name=current_user.name, lessons=lessons)
    else:
        logging.info("No user is authenticated")
        return render_template('index.html', lessons=lessons)
        lessons = Lesson.select()
        return render_template('index.html', name=current_user.name,  lessons=lessons)


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


# 許可されたファイルの拡張子を確認
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# 動画アップロードのルート
@app.route("/upload", methods=["GET", "POST"])
def upload_video():
    if request.method == "POST":
        # 動画ファイルと授業タイトルを取得
        file = request.files["file"]
        title = request.form["title"]
        user_id = request.form["user_id"]  # 動画を割り当てる生徒ID

        # ファイルが選択されているか確認
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))  # ファイルを保存

            # データベースに動画情報を保存
            conn = sqlite3.connect("db.sqlite")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO videos (title, filename, user_id) VALUES (?, ?, ?)", (title, filename, user_id)
            )
            conn.commit()
            conn.close()

            return redirect(url_for("upload_video"))  # アップロード後にリダイレクト

    # 登録されている生徒リストを取得して表示
    conn = sqlite3.connect("db.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template("upload.html", users=users)


# 動画視聴ページ
@app.route("/videos")
@login_required
def videos():
    return render_template("videos.html")


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
