from flask import Blueprint, render_template, request, redirect, url_for, session
from app import db
from sqlalchemy import text
import logging

sqli_bp = Blueprint('sqli', __name__)
logger = logging.getLogger(__name__)

def reset_search_db():
    setup_sql = """
    DROP TABLE IF EXISTS bds.dummy_sqli;
    CREATE TABLE bds.dummy_sqli (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100),
        secret_data VARCHAR(100)
    );
    GRANT SELECT, INSERT, UPDATE, DELETE ON bds.dummy_sqli TO "bds-app";
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
        logger.error(f"Setup search db error: {e}")

# --- VYHLEDÁVÁNÍ (Search Injection) ---
@sqli_bp.route('/sql-injection-demo', methods=['GET', 'POST'])
def index():
    unsafe_result = None
    safe_result = None
    executed_sql = ""
    error_msg = None
    
    search_input = request.form.get('search', '') 
    if not search_input:
        search_input = request.form.get('unsafe_search', '')

    if request.args.get('reset') == 'true':
        reset_search_db()
        return redirect(url_for('sqli.index'))

    if request.method == 'GET':
        reset_search_db()

    if request.method == 'POST':
        
        raw_sql = f"SELECT * FROM bds.dummy_sqli WHERE username = '{search_input}'"
        executed_sql = raw_sql
        
        try:
            result_proxy = db.session.execute(text(raw_sql))
            if result_proxy.returns_rows:
                unsafe_result = result_proxy.fetchall()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)

        safe_sql = "SELECT id, username, secret_data FROM bds.dummy_sqli WHERE username = :val"
        
        try:
            result_proxy = db.session.execute(text(safe_sql), {'val': search_input})
            if result_proxy.returns_rows:
                safe_result = result_proxy.fetchall()
        except Exception:
            db.session.rollback()
            pass

    return render_template('sqli/demo.html', 
                           unsafe_result=unsafe_result,
                           safe_result=safe_result,     
                           executed_sql=executed_sql,
                           search_query=search_input,   
                           error_msg=error_msg,
                           is_post=(request.method == 'POST'))


# --- Login Bypass ---
@sqli_bp.route('/sql-injection-login', methods=['GET', 'POST'])
def login_bypass():
    setup_sql = """
    DROP TABLE IF EXISTS bds.dummy_users;
    CREATE TABLE bds.dummy_users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100),
        password VARCHAR(100),
        role VARCHAR(50)
    );
    GRANT SELECT, INSERT, UPDATE, DELETE ON bds.dummy_users TO "bds-app";
    INSERT INTO bds.dummy_users (username, password, role) VALUES 
        ('admin', 'SuperTajneHeslo123', 'Administrátor'),
        ('pepa', '12345', 'Uživatel');
    """

    should_reset = request.args.get('reset') == 'true'
    is_fresh_load = request.method == 'GET' and 'unsafe_res' not in session

    if should_reset or is_fresh_load:
        try:
            db.session.execute(text(setup_sql))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Reset login error: {e}")
        
        session.pop('unsafe_res', None)
        session.pop('safe_res', None)
            
        if should_reset:
            return redirect(url_for('sqli.login_bypass'))

    username_input = request.form.get('username', '')
    password_input = request.form.get('password', '')
    
    if request.method == 'POST':
        if 'btn_unsafe' in request.form:
            raw_sql = f"SELECT * FROM bds.dummy_users WHERE username = '{username_input}' AND password = '{password_input}'"
            result_state = {'sql': raw_sql, 'success': False, 'user': None, 'role': None, 'error': None}
            try:
                result_proxy = db.session.execute(text(raw_sql))
                user_row = result_proxy.fetchone()
                if user_row:
                    result_state['success'] = True
                    result_state['user'] = user_row[1]
                    result_state['role'] = user_row[3] 
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                result_state['error'] = str(e)
            session['unsafe_res'] = result_state

        elif 'btn_safe' in request.form:
            safe_sql = "SELECT * FROM bds.dummy_users WHERE username = :u AND password = :p"
            result_state = {'sql': "SELECT ... WHERE username = :u ...", 'real_param_u': username_input, 'success': False, 'user': None, 'role': None, 'error': None}
            try:
                result_proxy = db.session.execute(text(safe_sql), {'u': username_input, 'p': password_input})
                user_row = result_proxy.fetchone()
                if user_row:
                    result_state['success'] = True
                    result_state['user'] = user_row[1]
                    result_state['role'] = user_row[3]
            except Exception as e:
                db.session.rollback()
                result_state['error'] = str(e)
            session['safe_res'] = result_state

    return render_template('sqli/login.html', 
                           username_input=username_input,
                           password_input=password_input,
                           unsafe_res=session.get('unsafe_res'),
                           safe_res=session.get('safe_res'))