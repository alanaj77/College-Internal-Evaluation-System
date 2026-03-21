from flask import Blueprint, render_template, request, session, redirect, url_for
from werkzeug.security import check_password_hash
from .models import get_connection   # import DB function

auth = Blueprint('auth', __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_connection()
        
        # Safety check in case the database is offline
        if conn is None:
            return render_template("login.html", error="Database connection failed. Try again later.")

        try:
            cursor = conn.cursor(dictionary=True)

            # Fixed the nested execute statements
            cursor.execute(
                "SELECT p_id, name, password_hash FROM professor WHERE email=%s",
                (email,)
            )

            user = cursor.fetchone()

            if user and check_password_hash(user["password_hash"], password):
                session["user_id"] = user["p_id"]
                session["name"]    = user["name"]
                session["role"]    = "faculty" # Added this so your app knows they are a professor!
                
                return redirect(url_for("views.dashboard"))
            else:
                return render_template("login.html", error="Invalid Email or Password")
                
        except Exception as e:
            print(f"Login Error: {e}")
            return render_template("login.html", error="An error occurred during login.")
            
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    # GET request just loads the page
    return render_template("login.html")

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))