from app import create_app
from flask import redirect
app = create_app()

@app.route("/")
def home():
    return redirect("/login")
    
if __name__ == '__main__':
    
    app.run(debug=True)
