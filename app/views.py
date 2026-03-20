from flask import Blueprint, render_template, session, url_for, redirect, request
from .models import get_connection   # import DB function
from mysql.connector import Error
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import io
import base64

views = Blueprint('views', __name__)

@views.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user_id = session["user_id"] 
    
    sql = """
    SELECT 
        p.p_id,
        a.t_id,
        a.sem_number,
        s.subject_code,
        p.name as profname, 
        s.subject_name AS Teaching, 
        a.branch_id AS `To Branch` 
    FROM t_assignment a
    JOIN professor p ON a.p_id = p.p_id
    JOIN subject s ON a.subject_code = s.subject_code 
    WHERE p.p_id = %s;
    """
    conn = get_connection()
    if conn is None:
        return "Database Connection Failed. Please try again later.", 500
         
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (user_id,))
        user = cursor.fetchall()
        
        prof_name = user[0]['profname'] if user else "Professor"
        return render_template("dashboard.html", name=prof_name, user_id=session["user_id"], user=user)
        
    except Error as e:
        print(f"Query Error: {e}")
        return "Error fetching data", 500
    finally:
        if conn and conn.is_connected():
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

    prof_name = session.get('name', '')
    
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
                               sub_code=sub_code,prof_name=prof_name)
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



@views.route('/performance_graphs')
def performance_graphs():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
        
    pid      = request.args.get('pid')
    tid      = request.args.get('tid')
    semno    = request.args.get('semno')
    sub_code = request.args.get('sub_code')
    
    prof_name = session.get('name','')
    # Get graph type from URL, default to categorization
    graph_type = request.args.get('graph_type', 'categorization')

    conn = get_connection()
    
    sql = '''
        SELECT sd.adm_no, sd.name, cm.assignment_marks, cm.attendance_marks,
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

        df = pd.DataFrame(students)
        
        # 🌟 Convert marks out of 40 to Percentages for accuracy
        df['percentage'] = (df['total_mark'] / 40.0) * 100
        
        # --- GRAPH SETUP ---
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_alpha(0.0) # Transparent background
        ax.set_facecolor('none')
        title = ""

        # 1. CATEGORIZATION (Excellent, Good, Average, Weak)
        if graph_type == 'categorization':
            bins = [0, 50, 75, 90, 101] 
            labels = ['Weak (<50%)', 'Average (50-74%)', 'Good (75-89%)', 'Excellent (90-100%)']
            df['category'] = pd.cut(df['percentage'], bins=bins, labels=labels, right=False)
            cat_counts = df['category'].value_counts().reindex(labels) 
            
            colors = ['#f03e3e', '#f59f00', '#0ca678', '#3b5bdb']
            ax.bar(cat_counts.index.astype(str), cat_counts.values, color=colors, width=0.6, alpha=0.9, edgecolor='#1a1f36')
            ax.set_ylabel('Number of Students', color='#6b7280', fontweight='bold')
            title = 'Marks Range Categorization'

        # 2. MARKS DISTRIBUTION (0-10%, 10-20%, etc.)
        elif graph_type == 'distribution':
            bins = range(0, 101, 10)
            labels = [f"{i}-{i+10}%" for i in range(0, 91, 10)]
            df['dist_category'] = pd.cut(df['percentage'], bins=bins, labels=labels, right=False)
            dist_counts = df['dist_category'].value_counts().reindex(labels).fillna(0)
            
            ax.bar(dist_counts.index.astype(str), dist_counts.values, color='#7950f2', width=0.8, alpha=0.85, edgecolor='#5c38cc')
            ax.set_xlabel('Percentage Range', color='#6b7280', fontweight='bold')
            ax.set_ylabel('Number of Students', color='#6b7280', fontweight='bold')
            plt.xticks(rotation=45, color='#6b7280')
            title = 'Overall Marks Distribution'

        # 3. TOP PERFORMERS (Top 5)
        elif graph_type == 'top_performers':
            top_df = df.nlargest(5, 'total_mark').sort_values('total_mark', ascending=True) 
            
            # Find the absolute highest mark in this group (handles ties for 1st place!)
            max_mark = top_df['total_mark'].max()
            
            # Dynamic Colors: Gold for the topper(s), your standard Blue for the rest
            colors = ['#f59f00' if mark == max_mark else '#3b5bdb' for mark in top_df['total_mark']]
            edges = ['#e67e22' if mark == max_mark else '#2f4ac4' for mark in top_df['total_mark']]
            
            bars = ax.barh(top_df['name'], top_df['total_mark'], color=colors, height=0.6, alpha=0.9, edgecolor=edges)
            
            # Add the exact marks as text right next to each bar
            for index, value in enumerate(top_df['total_mark']):
                # Make the text gold if they are the topper, otherwise standard gray
                text_color = '#f59f00' if value == max_mark else '#6b7280'
                
                # ax.text(x, y, string) places the text dynamically
                ax.text(value + 0.8, index, f"{value}", va='center', color=text_color, fontweight='bold', fontsize=11)

            ax.set_xlabel('Total Marks (Out of 40)', color='#6b7280', fontweight='bold')
            
            # Extended the X-axis slightly to 45 so the text labels don't get cut off at the edge
            ax.set_xlim(0, 45) 
            title = 'Top 5 Performers'

        # 4. WEAK STUDENTS (< 40% / < 16 Marks)
        elif graph_type == 'weak_students':
            weak_df = df[df['total_mark'] < 16].sort_values('total_mark', ascending=False)
            if weak_df.empty:
                ax.text(0.5, 0.5, "No Weak Students! 🎉", ha='center', va='center', fontsize=20, color='#0ca678', fontweight='bold')
                ax.axis('off')
            else:
                ax.bar(weak_df['name'], weak_df['total_mark'], color='#f03e3e', width=0.5, alpha=0.9, edgecolor='#c92a2a')
                ax.set_ylabel('Total Marks (Out of 40)', color='#6b7280', fontweight='bold')
                ax.set_ylim(0, 16)
                plt.xticks(rotation=45, color='#6b7280')
            title = 'Students Needing Improvement (< 40%)'

        # 5. SERIES EXAM COMPARISON
        elif graph_type == 'series_compare':
            s1_avg = df['series_one'].mean()
            s2_avg = df['series_two'].mean()
            
            ax.plot(['Series 1 (Max 10)', 'Series 2 (Max 10)'], [s1_avg, s2_avg], 
                    color='#3b5bdb', marker='o', markersize=10, linewidth=3, markerfacecolor='#f59f00')
            ax.set_ylabel('Class Average Marks', color='#6b7280', fontweight='bold')
            ax.set_ylim(0, 10)
            title = 'Series 1 vs Series 2 Performance Trend'

        # 6. PASS VS FAIL RATIO
        elif graph_type == 'pass_fail':
            pass_count = (df['total_mark'] >= 16).sum()
            fail_count = len(df) - pass_count
            
            ax.pie([pass_count, fail_count], labels=[f'Pass ({pass_count})', f'Fail ({fail_count})'], 
                   colors=["#4ee367", '#f03e3e'], autopct='%1.1f%%', 
                   startangle=90, textprops={'color': '#6b7280', 'weight': 'bold', 'size': 12})
            title = 'Pass vs Fail Ratio (40% Threshold)'
            
        # Clean up styling (applied to all except pie charts)
        if graph_type != 'pass_fail' and not (graph_type == 'weak_students' and df[df['total_mark'] < 16].empty):
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#b0b8cc')
            ax.spines['bottom'].set_color('#b0b8cc')
            ax.tick_params(colors='#6b7280')
            ax.grid(axis='y' if graph_type not in ['top_performers'] else 'x', color='#b0b8cc', linestyle='--', linewidth=0.5, alpha=0.3)

        ax.set_title(title, color='#3b5bdb', fontsize=18, fontweight='bold', pad=20, fontfamily='sans-serif')

        # Save and encode to Base64
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', transparent=True)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close('all') 

        return render_template('performance.html', plot_url=plot_url, 
                               pid=pid, tid=tid, semno=semno, sub_code=sub_code, current_graph=graph_type,prof_name=prof_name)

    except Error as e:
        print(f"Query Error: {e}")
        return "Error fetching data", 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
