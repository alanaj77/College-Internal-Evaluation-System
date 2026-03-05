from flask import Blueprint, render_template,session,url_for,redirect
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
        p.name, 
        s.subject_name AS Teaching, 
        a.branch_id AS `To Branch`,
        a.sem_number 
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
    
    return render_template('marks_entry.html')
