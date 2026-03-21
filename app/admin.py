from flask import Blueprint, render_template, request,session,redirect,url_for
from .models import get_connection

admin = Blueprint('admin', __name__)
@admin.route("/admin/login",methods = ["GET","POST"])
def login():
    
    if request.method == "POST":
        adminID = request.form.get("admin_id")
        adminPass = request.form.get("password")

        admin_username = "admin"
        admin_password = "admin"

        if admin_username == adminID and admin_password == adminPass:
            session["role"] = "admin"

            return redirect(url_for("admin.dashboard",name =admin_username))
        else:
            return render_template("admin/login.html", error="Invalid credentials")
   
    return render_template("admin/login.html")


@admin.route("/admin/dashboard")
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for("admin.login"))

    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM student_details")
        total_students = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM professor")
        total_professors = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM subject")
        total_subjects = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM t_assignment")
        total_assignments = cursor.fetchone()[0]

        return render_template("admin/dashboard.html",
                               total_students=total_students,
                               total_professors=total_professors,
                               total_subjects=total_subjects,
                               total_assignments=total_assignments)
    except Error as e:
        print(f"Error: {e}")
        return "Error loading dashboard", 500
    finally:
        cursor.close()
        conn.close()

@admin.route("admin/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))