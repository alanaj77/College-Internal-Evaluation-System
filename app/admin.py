from flask import Blueprint, render_template, request,session,redirect,url_for
from .models import get_connection
from mysql.connector import Error

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
        addstudent = 0
        return render_template("admin/dashboard.html",
                               total_students=total_students,
                               total_professors=total_professors,
                               total_subjects=total_subjects,
                               total_assignments=total_assignments,addstudent = addstudent)
    except Error as e:
        print(f"Error: {e}")
        return "Error loading dashboard", 500
    finally:
        cursor.close()
        conn.close()

@admin.route('/admin/add_student', methods=['GET', 'POST'])
def add_student():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    error = None
    success = None

    if request.method == 'POST':
        adm_no         = request.form.get('adm_no')
        admission_year = request.form.get('admission_year')
        name           = request.form.get('name')
        gender         = request.form.get('gender')
        dob            = request.form.get('dob')
        email_id       = request.form.get('email_id')
        status         = request.form.get('status')
        form_type      = request.form.get('form')
        address        = request.form.get('address')
        branch_id      = request.form.get('branch_id')
        sem_number     = request.form.get('sem_number')
        roll_number    = request.form.get('roll_number')
        reg_number     = request.form.get('reg_number')

        conn   = get_connection()
        cursor = conn.cursor()
        try:
            # Insert into student_details
            cursor.execute("""
                INSERT INTO student_details
                (adm_no, admission_year, name, gender, status, form, dob, email_id, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (adm_no, admission_year, name, gender,
                  status, form_type, dob, email_id, address))

            # Insert into student_class
            cursor.execute("""
                INSERT INTO student_class
                (adm_no, branch_id, sem_number, roll_number, reg_number)
                VALUES (%s, %s, %s, %s, %s)
            """, (adm_no, branch_id, sem_number, roll_number, reg_number))

            conn.commit()
            success = f"Student {name} ({adm_no}) added and enrolled successfully."

        except Error as e:
            conn.rollback()
            error = f"Error: {e}"
        finally:
            cursor.close()
            conn.close()

    return render_template('admin/add_student.html', error=error, success=success)



@admin.route("admin/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


