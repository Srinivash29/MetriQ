
import os
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from flask_wtf.csrf import CSRFProtect
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from db import get_db_connection
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")

if not secret_key:
    raise RuntimeError("SECRET_KEY is missing from .env")

app.config["SECRET_KEY"] = secret_key

# Enable CSRF protection
csrf = CSRFProtect(app)


# -------------------------------
# LOGIN REQUIRED DECORATOR
# -------------------------------

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# -------------------------------
# ROLE REQUIRED DECORATOR
# -------------------------------

def role_required(*allowed_roles):

    def decorator(function):

        @wraps(function)
        @login_required
        def wrapper(*args, **kwargs):

            if session.get("role") not in allowed_roles:
                flash("You are not authorized.", "danger")
                return redirect(url_for("dashboard"))

            return function(*args, **kwargs)

        return wrapper

    return decorator


# -------------------------------
# HOME PAGE
# -------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -------------------------------
# USER REGISTRATION
# -------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not all([full_name, email, password, confirm_password]):
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("register"))

        if len(full_name) > 100 or len(email) > 150:
            flash("Name or email is too long.", "danger")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if phone and len(phone) > 15:
            flash("Phone number is too long.", "danger")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO users
                (full_name, email, phone, password_hash, role)
                VALUES (%s, %s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    full_name,
                    email,
                    phone or None,
                    password_hash,
                    "applicant"
                )
            )

            connection.commit()

            flash("Registration successful! Please login.", "success")

            return redirect(url_for("login"))

        except Exception:
            if connection:
                connection.rollback()

            app.logger.exception("Registration failed")
            flash("Registration failed. Email may already exist.", "danger")

        finally:
            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template("register.html")


# -------------------------------
# USER LOGIN
# -------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT user_id, full_name, email,
                       password_hash, role
                FROM users
                WHERE email = %s
            """

            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if user and check_password_hash(
                user["password_hash"], password
            ):

                session.clear()

                session["user_id"] = user["user_id"]
                session["full_name"] = user["full_name"]
                session["role"] = user["role"]

                flash("Login successful!", "success")

                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "danger")

        except Exception:
            app.logger.exception("Login failed")
            flash("Unable to login. Please try again.", "danger")

        finally:
            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template("login.html")


# -------------------------------
# USER DASHBOARD
# -------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        full_name=session["full_name"],
        role=session["role"]
    )


# -------------------------------
# EXAMPLE ROLE PROTECTION
# -------------------------------

@app.route("/admin")
@role_required("admin")
def admin_dashboard():

    return "Admin access granted!"


# -------------------------------
# USER LOGOUT
# -------------------------------

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    session.clear()

    flash("You have logged out successfully.", "success")

    return redirect(url_for("home"))


# -------------------------------
# RUN APPLICATION
# -------------------------------

if __name__ == "__main__":
    app.run(debug=True)
