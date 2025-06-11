from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import pyrebase

firebase_config = {
    "apiKey": "AIzaSyCiAEuH1Kjy2IMVLpQ7xzLLmVEbz1Hf34Y",
    "authDomain": "test2-webauth.firebaseapp.com",
    "databaseURL": "https://test2-webauth-default-rtdb.europe-west1.firebasedatabase.app/",
    "projectId": "test2-webauth",
    "storageBucket": "test2-webauth.appspot.com",  # Исправлено: .appspot.com вместо .firebasestorage.app
    "messagingSenderId": "265692417148",
    "appId": "1:265692417148:web:07f2fc61bb49b79fe70df9",
    "measurementId": "G-84TQN5HKEY"
}

# Инициализируем Firebase
firebase = pyrebase.initialize_app(firebase_config)

# Получаем ссылку на службы аутентификации и базы данных
auth = firebase.auth()
db = firebase.database()


# Initialize Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

# Create database
with app.app_context():
    db.create_all()

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Home route
@app.route("/")
def home():
    return redirect(url_for("login"))

# Register route
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if Users.query.filter_by(username=username).first():
            return render_template("sign_up.html", error="Username already taken!")

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = Users(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))
    
    return render_template("sign_up.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# Protected dashboard route
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=current_user.username)

# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("register"))

if __name__ == "__main__":
    app.run(debug=True)