from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from sqlalchemy import text
import logging

sqli_bp = Blueprint('sqli', __name__)
logger = logging.getLogger(__name__)

def reset_db():
    """Pomocná funkce pro reset tabulky"""
    setup_sql = """
    DROP TABLE IF EXISTS bds.dummy_sqli;
    CREATE TABLE bds.dummy_sqli (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100),
        secret_data VARCHAR(100)
    );
    INSERT INTO bds.dummy_sqli (username, secret_data) VALUES 
        ('admin', 'HesloJe1234'),
        ('pepa', 'MojeTajemstvi'),
        ('user', 'NicZajimaveho'),
        ('karel', 'TajnyKod99');
    """
    try:
        db.session.execute(text(setup_sql))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Setup error: {e}")

@sqli_bp.route('/sql-injection-demo', methods=['GET', 'POST'])
def index():
    # Proměnné pro šablonu
    unsafe_result = None
    unsafe_headers = [] # NOVÉ: Názvy sloupců
    
    safe_result = None
    safe_headers = []   # NOVÉ: Názvy sloupců
    
    executed_sql = ""
    error_msg = None
    search_query = request.form.get('search', '')
    is_post = request.method == 'POST'
    
    if request.args.get('reset') == 'true':
        reset_db()
        return redirect(url_for('sqli.index'))

    if request.method == 'GET':
        reset_db()

    if is_post:
        # --- A) NEBEZPEČNÝ DOTAZ ---
        raw_sql = f"SELECT * FROM bds.dummy_sqli WHERE username = '{search_query}'"
        executed_sql = raw_sql
        
        try:
            result_proxy = db.session.execute(text(raw_sql))
            if result_proxy.returns_rows:
                # Získáme data
                unsafe_result = result_proxy.fetchall()
                # Získáme názvy sloupců (dynamicky)
                unsafe_headers = result_proxy.keys()
                
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)

        # --- B) BEZPEČNÝ DOTAZ ---
        safe_sql = "SELECT id, username, '****** (Skryto)' as secret_data FROM bds.dummy_sqli WHERE username = :val"
        try:
            result_proxy_safe = db.session.execute(text(safe_sql), {'val': search_query})
            if result_proxy_safe.returns_rows:
                safe_result = result_proxy_safe.fetchall()
                safe_headers = result_proxy_safe.keys()
        except Exception:
            db.session.rollback()
            pass

    return render_template('sqli/demo.html', 
                           unsafe_result=unsafe_result,
                           unsafe_headers=unsafe_headers, # Posíláme do šablony
                           safe_result=safe_result, 
                           safe_headers=safe_headers,     # Posíláme do šablony
                           executed_sql=executed_sql,
                           search_query=search_query,
                           error_msg=error_msg,
                           is_post=is_post)