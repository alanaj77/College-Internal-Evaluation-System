from flask import Blueprint, render_template,session,url_for,redirect,request
from .models import get_connection   # import DB function
views = Blueprint('views',__name__)
from mysql.connector import Error
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64


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
    print(pid)
    conn = get_connection()
    sql= '''
        SELECT 
    sd.adm_no,
    sd.name,
    cm.assignment_marks,
    cm.attendance_marks,
    cm.series_one,
    cm.series_two,
    tm.total_mark
FROM 
    student_details sd
JOIN 
    student_class sc 
        ON sd.adm_no = sc.adm_no
JOIN 
    t_assignment ta 
        ON ta.sem_number = sc.sem_number
        AND ta.branch_id = sc.branch_id
JOIN 
    component_marks cm 
        ON sd.adm_no = cm.adm_no
        AND cm.subject_code = ta.subject_code
JOIN 
     total_marks tm
       ON cm.adm_no = tm.adm_no
       AND cm.subject_code = tm.subject_code
WHERE 
    ta.subject_code = %s
    AND ta.p_id = %s
    AND sc.sem_number = %s
    AND ta.t_id = %s;
       '''
    if conn is None:
         return "Database Connection Failed. Please try again later.",500
    try:
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql,(sub_code,pid,semno,tid,))
        students = cursor.fetchall()
        
        return render_template('marks_entry.html',students= students)
    except Error as e:
        print(f"Query Error: {e}")
        return "Error fetching data",500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

   
@views.route('/performance_graphs')
def performance_graphs():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
        
    pid      = request.args.get('pid')
    tid      = request.args.get('tid')
    semno    = request.args.get('semno')
    sub_code = request.args.get('sub_code')

    conn = get_connection()
    
    # Your exact same brilliant 5-table JOIN query
    sql = '''
        SELECT 
            sd.adm_no, sd.name, cm.assignment_marks, cm.attendance_marks,
            cm.series_one, cm.series_two, tm.total_mark
        FROM student_details sd
        JOIN student_class sc ON sd.adm_no = sc.adm_no
        JOIN t_assignment ta ON ta.sem_number = sc.sem_number AND ta.branch_id = sc.branch_id
        JOIN component_marks cm ON sd.adm_no = cm.adm_no AND cm.subject_code = ta.subject_code
        JOIN total_marks tm ON cm.adm_no = tm.adm_no AND cm.subject_code = tm.subject_code
        WHERE ta.subject_code = %s AND ta.p_id = %s AND sc.sem_number = %s AND ta.t_id = %s;
    '''
    
    if conn is None:
         return "Database Connection Failed.", 500
         
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (sub_code, pid, semno, tid))
        students = cursor.fetchall()
        
        if not students:
            return "No data available to plot.", 404

        # --- THE MAGIC STARTS HERE ---
        
        # 1. Load SQL results directly into a Pandas DataFrame
        df = pd.DataFrame(students)

        # 2. Configure a modern, dark-themed Matplotlib aesthetic
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#121212') # Match a dark website background
        ax.set_facecolor('#121212')
        
        # Plotting a Scatter: Attendance vs. Total Marks
        # Using vibrant electric blue and bright pink to make the data pop
        ax.scatter(df['attendance_marks'], df['total_mark'], 
                   color='#00FFFF', edgecolors='#FF00FF', 
                   s=120, alpha=0.9, linewidths=1.5)
        
        # Styling the grid lines with a subtle violet
        ax.grid(color='#8A2BE2', linestyle='--', linewidth=0.5, alpha=0.4)
        
        # Labels and Title
        ax.set_title('Impact of Attendance on Total Marks', color='#FF00FF', fontsize=18, fontweight='bold', pad=15)
        ax.set_xlabel('Attendance Marks', color='#00FFFF', fontsize=12)
        ax.set_ylabel('Total Marks', color='#00FFFF', fontsize=12)
        
        # Hide the top and right borders for a cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#8A2BE2')
        ax.spines['left'].set_color('#8A2BE2')

        # 3. Save the plot to a temporary memory buffer
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', facecolor=fig.get_facecolor())
        img.seek(0)

        # 4. Encode the image into a base64 string
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        
        # CRITICAL: Close the plot to free up server memory
        plt.close(fig) 

        # Pass the encoded string to your template
        return render_template('performance.html', plot_url=plot_url)

    except Error as e:
        print(f"Query Error: {e}")
        return "Error fetching data", 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()