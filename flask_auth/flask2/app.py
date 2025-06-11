from flask import Flask, render_template, request, url_for, redirect, session, flash
from functools import wraps
import pyrebase
import json
from datetime import datetime

# Firebase configuration
firebase_config = {
    "apiKey": "AIzaSyCiAEuH1Kjy2IMVLpQ7xzLLmVEbz1Hf34Y",
    "authDomain": "test2-webauth.firebaseapp.com",
    "databaseURL": "https://test2-webauth-default-rtdb.europe-west1.firebasedatabase.app/",
    "projectId": "test2-webauth",
    "storageBucket": "test2-webauth.appspot.com",
    "messagingSenderId": "265692417148",
    "appId": "1:265692417148:web:07f2fc61bb49b79fe70df9",
    "measurementId": "G-84TQN5HKEY"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firebase_db = firebase.database()

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"

# Firebase authentication decorator
def firebase_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        
        try:
            # Verify the token is still valid
            user_info = auth.get_account_info(session['user']['idToken'])
            return f(*args, **kwargs)
        except:
            # Token is invalid, clear session and redirect
            session.clear()
            return redirect(url_for('login'))
    
    return decorated_function

# Helper function to get current user info
def get_current_user():
    if 'user' not in session:
        return None
    
    try:
        user_info = auth.get_account_info(session['user']['idToken'])
        return user_info['users'][0]
    except:
        return None

# Helper function to refresh user token
def refresh_user_token():
    if 'user' in session:
        try:
            refreshed_user = auth.refresh(session['user']['refreshToken'])
            session['user'] = {
                'idToken': refreshed_user['idToken'],
                'refreshToken': refreshed_user['refreshToken'],
                'localId': refreshed_user['localId'],
                'email': refreshed_user.get('email', '')
            }
        except:
            session.clear()

# Home route
@app.route("/")
def home():
    return redirect(url_for("login"))

# Register route
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name", "")

        try:
            # Create user with Firebase
            user = auth.create_user_with_email_and_password(email, password)
            
            # Save additional user info to Firebase Database
            user_data = {
                'email': email,
                'name': name,
                'created_at': datetime.now().isoformat(),
                'last_login': datetime.now().isoformat()
            }
            
            firebase_db.child("users").child(user['localId']).set(user_data)
            
            # Send email verification
            auth.send_email_verification(user['idToken'])
            
            flash("Account created successfully! Please check your email to verify your account.", "success")
            return redirect(url_for("login"))
            
        except Exception as e:
            error_message = str(e)
            if "EMAIL_EXISTS" in error_message:
                error = "Email address is already in use"
            elif "WEAK_PASSWORD" in error_message:
                error = "Password should be at least 6 characters"
            elif "INVALID_EMAIL" in error_message:
                error = "Invalid email address"
            else:
                error = "Registration failed. Please try again."
            
            return render_template("sign_up.html", error=error)
    
    return render_template("sign_up.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            # Sign in with Firebase
            user = auth.sign_in_with_email_and_password(email, password)
            
            # Store user session
            session['user'] = {
                'idToken': user['idToken'],
                'refreshToken': user['refreshToken'],
                'localId': user['localId'],
                'email': user['email']
            }
            
            # Update last login time
            firebase_db.child("users").child(user['localId']).update({
                'last_login': datetime.now().isoformat()
            })
            
            return redirect(url_for("dashboard"))
            
        except Exception as e:
            error_message = str(e)
            if "INVALID_PASSWORD" in error_message or "EMAIL_NOT_FOUND" in error_message:
                error = "Invalid email or password"
            elif "USER_DISABLED" in error_message:
                error = "This account has been disabled"
            elif "TOO_MANY_ATTEMPTS" in error_message:
                error = "Too many failed attempts. Please try again later."
            else:
                error = "Login failed. Please try again."
            
            return render_template("login.html", error=error)

    return render_template("login.html")

# Protected dashboard route
@app.route("/dashboard")
@firebase_auth_required
def dashboard():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    
    # Get additional user data from Firebase Database
    user_data = firebase_db.child("users").child(session['user']['localId']).get().val()
    
    context = {
        'user_email': current_user['email'],
        'user_name': user_data.get('name', '') if user_data else '',
        'last_login': user_data.get('last_login', '') if user_data else '',
        'email_verified': current_user.get('emailVerified', False)
    }
    
    return render_template("dashboard.html", **context)

# Reset password route
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email")
        
        try:
            auth.send_password_reset_email(email)
            flash("Password reset email sent! Please check your email.", "success")
            return render_template("reset_password.html", success="Password reset email sent!")
            
        except Exception as e:
            error_message = str(e)
            if "EMAIL_NOT_FOUND" in error_message:
                error = "No account found with this email address"
            elif "INVALID_EMAIL" in error_message:
                error = "Invalid email address"
            else:
                error = "Failed to send reset email. Please try again."
            
            return render_template("reset_password.html", error=error)
    
    return render_template("reset_password.html")

# Verify email route
@app.route("/verify-email")
@firebase_auth_required
def verify_email():
    try:
        auth.send_email_verification(session['user']['idToken'])
        flash("Verification email sent!", "success")
    except Exception as e:
        flash("Failed to send verification email", "error")
    
    return redirect(url_for('dashboard'))

# Change password route
@app.route("/change-password", methods=["GET", "POST"])
@firebase_auth_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        
        try:
            # Re-authenticate user
            user = auth.sign_in_with_email_and_password(
                session['user']['email'], 
                current_password
            )
            
            # Change password
            auth.update_user(user['idToken'], password=new_password)
            flash("Password updated successfully!", "success")
            
        except Exception as e:
            flash("Failed to update password. Please check your current password.", "error")
    
    return render_template("change_password.html")

# Logout route
@app.route("/logout")
@firebase_auth_required
def logout():
    session.clear()
    flash("You have been logged out successfully", "success")
    return redirect(url_for("login"))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=True)
