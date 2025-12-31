from flask import Blueprint,render_template

auth = Blueprint('auth',__name__)



@auth.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")
@auth.route('/new')
def new():
    return render_template("new.html")

