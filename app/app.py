# Импортируем модули
import pyrebase
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
from datetime import datetime
import re

# Создаём Flask 
app = Flask(__name__)
# Создаём секретный ключ для безопасности
app.secret_key = "123456789"

# Конфигурация 
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

# Рут для вхоода
@app.route("/")
def login():
    return render_template("login.html")

# Рут для регистрации
@app.route("/signup")
def signup():
    return render_template("signup.html")

# Рут для успешного входа
@app.route("/DobroPozhalovat")
def welcome():
    # Проверка входа в систему
    if session.get("is_logged_in", False):
        return render_template("welcome.html", email=session["email"], name=session["name"])
    else:
        # Возврат если нет
        return redirect(url_for('login'))

# Функция проверки надежности пароля
def check_password_strength(password):
    # По крайней мере одна строчная буква, одна заглавная буква, одна цифра, один специальный символ и длина не менее 8 символов.
    return re.match(r'^(?=.*\d)(?=.*[!@#$%^&*])(?=.*[a-z])(?=.*[A-Z]).{8,}$', password) is not None

# Рут для результата входа в систему
@app.route("/result", methods=["POST", "GET"])
def result():
    if request.method == "POST":
        result = request.form
        email = result["email"]
        password = result["pass"]
        try:
            # Аутентификация пользователя
            user = auth.sign_in_with_email_and_password(email, password)
            session["is_logged_in"] = True
            session["email"] = user["email"]
            session["uid"] = user["localId"]
            # Получить данные пользователя
            data = db.child("users").get().val()
            # Обновить данные сеанса
            if data and session["uid"] in data:
                session["name"] = data[session["uid"]]["name"]
                # Обновить время последнего входа в систему
                db.child("users").child(session["uid"]).update({"last_logged_in": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})
            else:
                session["name"] = "User"
            # Перенаправление на страницу приветствия при успешном входе
            return redirect(url_for('welcome'))
        except Exception as e:
            print("Error occurred: ", e)
            return redirect(url_for('login'))
    else:
        # Если пользователь вошел в систему, перенаправить на страницу приветствия
        if session.get("is_logged_in", False):
            return redirect(url_for('welcome'))
        else:
            return redirect(url_for('login'))

# Рут регистрации пользователя
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        result = request.form
        email = result["email"]
        password = result["pass"]
        name = result["name"]
        if not check_password_strength(password):
            print("Пароль не соответствует требованиям надежности")
            return redirect(url_for('signup'))
        try:
            # Создать учетную запись пользователя
            auth.create_user_with_email_and_password(email, password)
            # Аутентификация пользователя
            user = auth.sign_in_with_email_and_password(email, password)
            session["is_logged_in"] = True
            session["email"] = user["email"]
            session["uid"] = user["localId"]
            session["name"] = name
            # Сохранить пользовательские данные
            data = {"name": name, "email": email, "last_logged_in": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}
            db.child("users").child(session["uid"]).set(data)
            return redirect(url_for('welcome'))
        except Exception as e:
            print("Error occurred during registration: ", e)
            return redirect(url_for('signup'))
    else:
        # Если пользователь вошел в систему, перенаправить на страницу приветствия
        if session.get("is_logged_in", False):
            return redirect(url_for('welcome'))
        else:
            return redirect(url_for('signup'))

# Маршрут для сброса пароля
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form["email"]
        try:
            # Отправить письмо для сброса пароля
            auth.send_password_reset_email(email)
            return render_template("reset_password_done.html")  # Показываем страницу, предлагающую пользователю проверить свою электронную почту
        except Exception as e:
            print("Error occurred: ", e)
            return render_template("reset_password.html", error="An error occurred. Please try again.")  # Говорим об ошибке
    else:
        return render_template("reset_password.html")  # Показать страницу сброса пароля

# Рут для выхода из системы
@app.route("/logout")
def logout():
    # Обновить время последнего выхода
    db.child("users").child(session["uid"]).update({"last_logged_out": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")})
    session["is_logged_in"] = False
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
