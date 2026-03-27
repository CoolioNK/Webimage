from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os, uuid

from models import db, User, Image

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["UPLOAD_FOLDER"] = "uploads"

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        file = request.files["file"]

        if file:
            ext = file.filename.rsplit(".", 1)[1]
            filename = f"{uuid.uuid4().hex}.{ext}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)

            img = Image(filename=filename, user_id=current_user.id)
            db.session.add(img)
            db.session.commit()

    images = Image.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", images=images)


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)

    with app.app_context():
        db.create_all()

    app.run(debug=True)
