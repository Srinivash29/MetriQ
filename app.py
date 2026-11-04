
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


# =====================================
# STEP 5 - INSTRUMENT MANAGEMENT
# =====================================


# VIEW ALL INSTRUMENTS
@app.route("/instruments")
@login_required
def instruments():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT *
            FROM instruments
            WHERE user_id = %s
            ORDER BY instrument_id DESC
        """

        cursor.execute(query, (session["user_id"],))
        instrument_list = cursor.fetchall()

        return render_template(
            "instruments.html",
            instruments=instrument_list
        )

    except Exception:
        app.logger.exception("Unable to load instruments")
        flash("Unable to load instruments.", "danger")
        return redirect(url_for("dashboard"))

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ADD NEW INSTRUMENT
@app.route("/instruments/add", methods=["GET", "POST"])
@login_required
def add_instrument():

    if request.method == "POST":

        instrument_name = request.form.get(
            "instrument_name", ""
        ).strip()

        instrument_type = request.form.get(
            "instrument_type", ""
        ).strip()

        manufacturer = request.form.get(
            "manufacturer", ""
        ).strip()

        model_number = request.form.get(
            "model_number", ""
        ).strip()

        serial_number = request.form.get(
            "serial_number", ""
        ).strip()

        location = request.form.get(
            "location", ""
        ).strip()

        if not all([
            instrument_name,
            instrument_type,
            serial_number
        ]):
            flash("Please fill all required fields.", "danger")
            return redirect(url_for("add_instrument"))

        if (
            len(instrument_name) > 100
            or len(instrument_type) > 100
            or len(manufacturer) > 100
            or len(model_number) > 100
            or len(serial_number) > 100
            or len(location) > 255
        ):
            flash("One or more fields exceed the allowed length.", "danger")
            return redirect(url_for("add_instrument"))

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO instruments (
                    user_id,
                    instrument_name,
                    instrument_type,
                    manufacturer,
                    model_number,
                    serial_number,
                    location
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    session["user_id"],
                    instrument_name,
                    instrument_type,
                    manufacturer or None,
                    model_number or None,
                    serial_number,
                    location or None
                )
            )

            connection.commit()

            flash("Instrument registered successfully!", "success")

            return redirect(url_for("instruments"))

        except Exception as error:

            if connection:
                connection.rollback()

            if getattr(error, "errno", None) == 1062:
                flash("This serial number is already registered.", "danger")
            else:
                app.logger.exception("Instrument registration failed")
                flash("Unable to register instrument.", "danger")

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template("add_instrument.html")


# EDIT INSTRUMENT
@app.route(
    "/instruments/edit/<int:instrument_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_instrument(instrument_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM instruments
            WHERE instrument_id = %s AND user_id = %s
            """,
            (instrument_id, session["user_id"])
        )

        instrument = cursor.fetchone()

        if not instrument:
            flash("Instrument not found or access denied.", "danger")
            return redirect(url_for("instruments"))

        if request.method == "POST":

            instrument_name = request.form.get(
                "instrument_name", ""
            ).strip()

            instrument_type = request.form.get(
                "instrument_type", ""
            ).strip()

            manufacturer = request.form.get(
                "manufacturer", ""
            ).strip()

            model_number = request.form.get(
                "model_number", ""
            ).strip()

            serial_number = request.form.get(
                "serial_number", ""
            ).strip()

            location = request.form.get(
                "location", ""
            ).strip()

            if not all([
                instrument_name,
                instrument_type,
                serial_number
            ]):
                flash("Please fill all required fields.", "danger")

                return render_template(
                    "edit_instrument.html",
                    instrument=instrument
                )

            if (
                len(instrument_name) > 100
                or len(instrument_type) > 100
                or len(manufacturer) > 100
                or len(model_number) > 100
                or len(serial_number) > 100
                or len(location) > 255
            ):
                flash("One or more fields exceed the allowed length.", "danger")

                return render_template(
                    "edit_instrument.html",
                    instrument=instrument
                )

            update_query = """
                UPDATE instruments
                SET instrument_name = %s,
                    instrument_type = %s,
                    manufacturer = %s,
                    model_number = %s,
                    serial_number = %s,
                    location = %s
                WHERE instrument_id = %s AND user_id = %s
            """

            cursor.execute(
                update_query,
                (
                    instrument_name,
                    instrument_type,
                    manufacturer or None,
                    model_number or None,
                    serial_number,
                    location or None,
                    instrument_id,
                    session["user_id"]
                )
            )

            connection.commit()

            flash("Instrument updated successfully!", "success")

            return redirect(url_for("instruments"))

        return render_template(
            "edit_instrument.html",
            instrument=instrument
        )

    except Exception as error:

        if connection:
            connection.rollback()

        if getattr(error, "errno", None) == 1062:
            flash("This serial number is already registered.", "danger")
        else:
            app.logger.exception("Instrument update failed")
            flash("Unable to update instrument.", "danger")

        return redirect(url_for("instruments"))

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# DELETE INSTRUMENT
@app.route(
    "/instruments/delete/<int:instrument_id>",
    methods=["POST"]
)
@login_required
def delete_instrument(instrument_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM instruments
            WHERE instrument_id = %s AND user_id = %s
            """,
            (instrument_id, session["user_id"])
        )

        if cursor.rowcount == 0:
            flash("Instrument not found or access denied.", "danger")
        else:
            connection.commit()
            flash("Instrument deleted successfully!", "success")

    except Exception as error:

        if connection:
            connection.rollback()

        if getattr(error, "errno", None) == 1451:
            flash(
                "This instrument is linked to an application and cannot be deleted.",
                "warning"
            )
        else:
            app.logger.exception("Instrument deletion failed")
            flash("Unable to delete instrument.", "danger")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for("instruments"))

# -------------------------------
# RUN APPLICATION
# -------------------------------

if __name__ == "__main__":
    app.run(debug=True)
