from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from sqlalchemy import text

# Inicializace databáze 
db = SQLAlchemy()

def create_app():
    # Načtení proměnných z .env
    load_dotenv()
    
    app = Flask(__name__)
    
    # Konfigurace programu

    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url + "?options=-csearch_path%3Dbds"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
    # Propojení databáze s aplikací
    db.init_app(app)
    
    #Později dodám blueprinty

    
    @app.route('/')
    
    def index():
        try:
            result = db.session.execute(text("SELECT version()")).fetchone()
            db_version = result[0]
            return f"<h1>Asi to funguje</h1><p>Mám dost.</p><p><strong>Verze PostgreSQL:</strong> {db_version}</p>"
        except Exception as e:
            return f"<h1>Chyba připojení k databázi</h1><p>{e}</p>"
    return app