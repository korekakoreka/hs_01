from flask import Flask, flash, redirect, render_template, request
from flask_login import LoginManager, login_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from config import User
  
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
        return render_template("index.html")
    
    return render_template("register.html")


# ログインフォームの表示
@app.route("/login")
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
        # NGならフラッシュメッセージを設定
        flash("認証に失敗しました")

    return render_template("login.html")


@app.route("/")
def index():
    return render_template("index.html")

# 動画視聴ページ
@app.route("/videos")
@login_required
def videos():
    return render_template("videos.html")

# バッジを与える基準を定義
def award_badge(user):
    # 進捗に基づいてバッジを付与
    progress = get_student_progress(user.id)  # この関数は進捗を取得する実装が必要
    if progress > 50:
        # バッジ付与のロジック
        pass

# 進捗確認とバッジ付与のルート
@app.route("/progress")
@login_required
def progress():
    award_badge(current_user)
    return render_template("progress.html", progress=get_student_progress(current_user.id))

# アプリケーションの起動
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
