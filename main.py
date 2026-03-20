from app import create_app
from flask import redirect
app = create_app()

@app.route("/")
def home():
    return redirect("/login")
    
if __name__ == '__main__':
    
    app.run(host="0.0.0.0", port=5000, debug=False)

