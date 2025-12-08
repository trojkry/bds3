from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from sqlalchemy import text
from flask_login import LoginManager
import logging
from logging.handlers import TimedRotatingFileHandler
from flask import Flask, render_template



db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    
    load_dotenv()
    
    app = Flask(__name__)
    

    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url + "?options=-csearch_path%3Dbds"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/uploads/products') 
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB limit


    if not os.path.exists('logs'):
        os.mkdir('logs')
        
    # Logy o půlnoci (snad)
    file_handler = TimedRotatingFileHandler('logs/bds.log', when='midnight', interval=1, backupCount=30)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)


    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Pro přístup na tuto stránku se musíte přihlásit."

    from app.models import StaffMember
    @login_manager.user_loader
    def load_user(user_id):
        return StaffMember.query.get(int(user_id))
    
    # Blueprinty
    from app.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.blueprints.products import products_bp
    app.register_blueprint(products_bp)
    
    from app.blueprints.orders import orders_bp
    app.register_blueprint(orders_bp)

    from app.blueprints.customers import customers_bp
    app.register_blueprint(customers_bp)

    from app.blueprints.categories import categories_bp
    app.register_blueprint(categories_bp)

    from app.blueprints.staff import staff_bp
    app.register_blueprint(staff_bp)

    from app.blueprints.sqli import sqli_bp
    app.register_blueprint(sqli_bp)
    
    @app.route('/')
    def index():
        db_version = "Neznámá"
        try:
            result = db.session.execute(text("SELECT version()")).fetchone()
            db_version = result[0]
        except Exception as e:
            db_version = f"Chyba: {e}"
            
        return render_template('index.html', db_version=db_version)

    return app