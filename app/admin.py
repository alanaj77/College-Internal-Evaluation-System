from flask import Blueprint, render_template, request, session, redirect, url_for
from .models import get_connection
from mysql.connector import Error  # <-- Added missing import

admin = Blueprint('admin', __name__)

@admin.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        adminID = request.form.get("admin_id")
        adminPass = request.form.get("password")

        # Hardcoded for the mini-project
        admin_username = "admin"
        admin_password = "admin"

        if admin_username == adminID and admin_password == adminPass:
            session["role"] = "admin"
            return redirect(url_for("admin.dashboard"))
        else:
            # UPDATE 1: Point to the unified login page, pass the error, and keep the admin tab active
            return render_template("login.html", error="Invalid credentials", active_tab="admin")
   
    # UPDATE 2: When they first visit /admin/login, load the unified page with the admin tab active
    return render_template("login.html", active_tab="admin")


@admin.route("/admin/dashboard")
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for("admin.login"))

    conn = get_connection()
    
    # <-- Added safety check in case the database is offline
    if conn is None: 
        return "Database Connection Failed", 500
        
    try:
        cursor = conn.cursor()
        
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
        if conn and conn.is_connected():
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

@admin.route('/admin/map_subject', methods=['GET', 'POST'])
def map_subject():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    # Fetch professors and subjects for dropdowns
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT p_id, name FROM professor")
    professors = cursor.fetchall()
    cursor.execute("SELECT subject_code, subject_name FROM subject")
    subjects = cursor.fetchall()
    cursor.close()
    conn.close()

    error   = None
    success = None

    if request.method == 'POST':
        p_id          = request.form.get('p_id')
        subject_code  = request.form.get('subject_code')
        branch_id     = request.form.get('branch_id')
        sem_number    = request.form.get('sem_number')
        academic_year = request.form.get('academic_year')

        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO t_assignment
                (p_id, subject_code, academic_year, branch_id, sem_number)
                VALUES (%s, %s, %s, %s, %s)
            """, (p_id, subject_code, academic_year, branch_id, sem_number))
            conn.commit()
            success = "Subject mapped to professor successfully."
        except Error as e:
            conn.rollback()
            error = f"Error: {e}"
        finally:
            cursor.close()
            conn.close()

    return render_template('admin/map_subject.html',
                           professors=professors,
                           subjects=subjects,
                           error=error,
                           success=success)

from werkzeug.security import generate_password_hash

@admin.route('/admin/add_professor', methods=['GET', 'POST'])
def add_professor():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    error   = None
    success = None

    if request.method == 'POST':
        name        = request.form.get('name')
        email       = request.form.get('email')
        phone       = request.form.get('phone')
        designation = request.form.get('designation')
        status      = request.form.get('status')
        password    = request.form.get('password')

        # Hash the password using scrypt — same method as existing records
        password_hash = generate_password_hash(password)

        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO professor
                (name, email, phone, status, designation, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, email, phone, status, designation, password_hash))
            conn.commit()
            success = f"Professor {name} added successfully."
        except Error as e:
            conn.rollback()
            error = f"Error: {e}"
        finally:
            cursor.close()
            conn.close()

    return render_template('admin/add_professor.html',
                           error=error,
                           success=success)


@admin.route("/admin/logout") # <-- Added missing leading slash
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin.route("/admin/students")
def manage_students():
    if session.get('role') != 'admin':
        return redirect(url_for("admin.login"))

    conn = get_connection()
    if conn is None:
        return "Database Connection Failed", 500

    try:
        cursor = conn.cursor(dictionary=True)
        # 1. UPDATED SQL: Fetching ALL attributes from both tables
        sql = """
            SELECT sd.adm_no, sd.admission_year, sd.name, sd.gender, sd.status, 
                   sd.form, sd.dob, sd.email_id, sd.address,
                   sc.branch_id, sc.sem_number, sc.roll_number, sc.reg_number
            FROM student_details sd
            LEFT JOIN student_class sc ON sd.adm_no = sc.adm_no
            ORDER BY sd.adm_no ASC
        """
        cursor.execute(sql)
        students = cursor.fetchall()

        return render_template("admin/manage_students.html", students=students)
    except Error as e:
        print(f"Error: {e}")
        return "Error loading students", 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@admin.route('/admin/update_student', methods=['POST'])
def update_student():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    # Grab ALL fields from the modal form
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

    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 2. UPDATED SQL: Update all fields in student_details
        cursor.execute("""
            UPDATE student_details 
            SET admission_year=%s, name=%s, gender=%s, dob=%s, 
                email_id=%s, status=%s, form=%s, address=%s 
            WHERE adm_no=%s
        """, (admission_year, name, gender, dob, email_id, status, form_type, address, adm_no))
        
        # 3. UPDATED SQL: Update all fields in student_class
        cursor.execute("""
            UPDATE student_class 
            SET branch_id=%s, sem_number=%s, roll_number=%s, reg_number=%s 
            WHERE adm_no=%s
        """, (branch_id, sem_number, roll_number, reg_number, adm_no))
        
        conn.commit()
    except Error as e:
        conn.rollback()
        print(f"Database Error: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            
    return redirect('/admin/students')

@admin.route('/admin/delete_student', methods=['POST'])
def delete_student():
    """Handles the 'Delete' button inside the Modal"""
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    adm_no = request.form.get('adm_no')

    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # NOTE: Always delete from child tables (student_class) BEFORE the parent table (student_details)
        # Otherwise, MySQL will block the deletion due to Foreign Key constraints!
        cursor.execute("DELETE FROM student_class WHERE adm_no = %s", (adm_no,))
        cursor.execute("DELETE FROM student_details WHERE adm_no = %s", (adm_no,))
        
        conn.commit()
    except Error as e:
        conn.rollback()
        print(f"Database Error: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            
    # Refresh the page to show the student is gone!
    return redirect('/admin/students')


@admin.route('/admin/subjects')
def subjects():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))
    return render_template('admin/subjects.html')


@admin.route('/admin/add_subject', methods=['GET', 'POST'])
def add_subject():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    error   = None
    success = None

    if request.method == 'POST':
        subject_code = request.form.get('subject_code')
        subject_name = request.form.get('subject_name')

        conn   = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO subject (subject_code, subject_name) VALUES (%s, %s)",
                (subject_code, subject_name)
            )
            conn.commit()
            success = f"Subject {subject_name} ({subject_code}) added successfully."
        except Error as e:
            conn.rollback()
            error = f"Error: {e}"
        finally:
            cursor.close()
            conn.close()

    return render_template('admin/add_subject.html', error=error, success=success)



@admin.route('/admin/professors')
def manage_professors():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM professor ORDER BY name")
        professors = cursor.fetchall()
        return render_template('admin/manage_professors.html',
                               professors=professors)
    except Error as e:
        return f"Error: {e}", 500
    finally:
        cursor.close()
        conn.close()


@admin.route('/admin/update_professor', methods=['POST'])
def update_professor():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    p_id        = request.form.get('p_id')
    name        = request.form.get('name')
    email       = request.form.get('email')
    phone       = request.form.get('phone')
    designation = request.form.get('designation')
    status      = request.form.get('status')
    password    = request.form.get('password')

    conn   = get_connection()
    cursor = conn.cursor()
    try:
        if password:
            # Update with new password
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(password)
            cursor.execute("""
                UPDATE professor
                SET name=%s, email=%s, phone=%s,
                    designation=%s, status=%s, password_hash=%s
                WHERE p_id=%s
            """, (name, email, phone, designation,
                  status, password_hash, p_id))
        else:
            # Update without changing password
            cursor.execute("""
                UPDATE professor
                SET name=%s, email=%s, phone=%s,
                    designation=%s, status=%s
                WHERE p_id=%s
            """, (name, email, phone, designation, status, p_id))

        conn.commit()
        return redirect(url_for('admin.manage_professors'))
    except Error as e:
        return f"Error: {e}", 500
    finally:
        cursor.close()
        conn.close()


@admin.route('/admin/delete_professor', methods=['POST'])
def delete_professor():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    p_id = request.form.get('p_id')

    conn   = get_connection()
    cursor = conn.cursor()
    try:
        # before_delete_professor trigger handles t_assignment cascade
        cursor.execute("DELETE FROM professor WHERE p_id = %s", (p_id,))
        conn.commit()
        return redirect(url_for('admin.manage_professors'))
    except Error as e:
        return f"Error: {e}", 500
    finally:
        cursor.close()
        conn.close()


@admin.route('/admin/assignments')
def manage_assignments():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                ta.t_id,
                ta.branch_id,
                ta.sem_number,
                ta.academic_year,
                p.name  AS professor_name,
                s.subject_code,
                s.subject_name
            FROM t_assignment ta
            JOIN professor p ON ta.p_id = p.p_id
            JOIN subject s   ON ta.subject_code = s.subject_code
            ORDER BY ta.t_id DESC
        """)
        assignments = cursor.fetchall()
        return render_template('admin/manage_assignments.html',
                               assignments=assignments)
    except Error as e:
        return f"Error: {e}", 500
    finally:
        cursor.close()
        conn.close()


@admin.route('/admin/delete_assignment', methods=['POST'])
def delete_assignment():
    if session.get('role') != 'admin':
        return redirect(url_for('admin.login'))

    t_id = request.form.get('t_id')

    conn   = get_connection()
    cursor = conn.cursor()
    try:
        # after_delete_t_assignment trigger handles
        # component_marks and total_marks cascade
        cursor.execute(
            "DELETE FROM t_assignment WHERE t_id = %s", (t_id,)
        )
        conn.commit()
        return redirect(url_for('admin.manage_assignments'))
    except Error as e:
        return f"Error: {e}", 500
    finally:
        cursor.close()
        conn.close()
        
