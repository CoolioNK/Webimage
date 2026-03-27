from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os, uuid

from models import db, User, Image

app = Flask(__name__)

app.config["SECRET_KEY"] = "supersecret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["UPLOAD_FOLDER"] = "uploads"

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- AUTH ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=generate_password_hash(request.form["password"])
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect("/")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


# ---------------- MAIN FEED ----------------

@app.route("/", methods=["GET"])
@login_required
def index():
    images = Image.query.order_by(Image.id.desc()).all()
    return render_template("index.html", images=images)


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")

    if file:
        ext = file.filename.rsplit(".", 1)[1]
        filename = f"{uuid.uuid4().hex}.{ext}"

        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        img = Image(filename=filename, user_id=current_user.id)
        db.session.add(img)
        db.session.commit()

    return redirect("/")


@app.route("/like/<int:image_id>")
@login_required
def like(image_id):
    img = Image.query.get(image_id)
    img.likes += 1
    db.session.commit()
    return redirect("/")


# ---------------- RUN (HOST READY) ----------------

if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)

    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
