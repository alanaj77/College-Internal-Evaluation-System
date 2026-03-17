from flask import Flask,render_template
 
def create_app():

    app = Flask(__name__)
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors_500.html'), 500
    app.config['SECRET_KEY'] = 'ABDSJHSD HBCSBD'

    from .views import views
    from .auth import auth 
    app.register_blueprint(views,url_prefix='/')
    app.register_blueprint(auth,url_prefix='/')
    return app 