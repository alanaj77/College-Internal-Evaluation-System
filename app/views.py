from flask import Blueprint, render_template,session,url_for,redirect,request
from .models import get_connection   # import DB function
views = Blueprint('views',__name__)
from mysql.connector import Error


@views.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user_id=session["user_id"] 
   
    sql = """
    SELECT 
        
        p.p_id,
        a.t_id,
        a.sem_number,
        s.subject_code,
        p.name, 
        s.subject_name AS Teaching, 
        
        
        a.branch_id AS `To Branch` 
    FROM t_assignment a
    JOIN professor p ON a.p_id = p.p_id
    JOIN subject s ON a.subject_code = s.subject_code where p.p_id=%s;
    """
    conn = get_connection()
    if conn is None:
         return "Database Connection Failed. Please try again later.",500
    try:
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql,(user_id,))
        user = cursor.fetchall()
        
        return render_template("dashboard.html",name = user[0]['name'],user_id=session["user_id"],user = user)
    except Error as e:
        print(f"Query Error: {e}")
        return "Error fetching data",500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    
  

    

@views.route('/marks_entry')
def marks_entry():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    pid      = request.args.get('pid')
    tid      = request.args.get('tid')
    semno    = request.args.get('semno')
    sub_code = request.args.get('sub_code')

    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get subject name for the header
        cursor.execute("SELECT subject_name FROM subject WHERE subject_code = %s", (sub_code,))
        subject = cursor.fetchone()
        subject_name = subject['subject_name'] if subject else ''

        # Get all students with their marks
        cursor.execute("""
            SELECT
                sd.adm_no,
                sd.name,
                cm.assignment_marks,
                cm.attendance_marks,
                cm.series_one,
                cm.series_two,
                tm.total_mark
            FROM student_details sd
            JOIN student_class sc ON sd.adm_no = sc.adm_no
            JOIN t_assignment ta  ON ta.sem_number = sc.sem_number
                                 AND ta.branch_id  = sc.branch_id
            JOIN component_marks cm ON sd.adm_no = cm.adm_no
                                   AND cm.subject_code = ta.subject_code
            JOIN total_marks tm     ON cm.adm_no = tm.adm_no
                                   AND cm.subject_code = tm.subject_code
            WHERE ta.subject_code = %s
              AND ta.p_id = %s
              AND sc.sem_number = %s
              AND ta.t_id = %s
        """, (sub_code, pid, semno, tid))

        students = cursor.fetchall()

        return render_template('marks_entry.html',
                               students=students,
                               subject_name=subject_name,
                               sub_code=sub_code)
    except Error as e:
        print(f"Error: {e}")
        return "Error fetching data", 500
    finally:
        cursor.close()
        conn.close()


@views.route('/update_marks', methods=['POST'])
def update_marks():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    adm_no       = request.form.get('adm_no')
    sub_code     = request.form.get('sub_code')
    redirect_url = request.form.get('redirect_url')

    # ── Convert empty string to None (NULL in MySQL) ──
    def to_int(val):
        try:
            return int(val) if val and val.strip() != '' else None
        except ValueError:
            return None

    assignment_marks = to_int(request.form.get('assignment_marks'))
    attendance_marks = to_int(request.form.get('attendance_marks'))
    series_one       = to_int(request.form.get('series_one'))
    series_two       = to_int(request.form.get('series_two'))

    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE component_marks
            SET assignment_marks = %s,
                attendance_marks = %s,
                series_one       = %s,
                series_two       = %s
            WHERE adm_no = %s AND subject_code = %s
        """, (assignment_marks, attendance_marks,
              series_one, series_two, adm_no, sub_code))
        conn.commit()
        return redirect(redirect_url)
    except Error as e:
        print(f"Error: {e}")
        return "Error updating marks", 500
    finally:
        cursor.close()
        conn.close()
