from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import StaffMember, Role
from argon2 import PasswordHasher
from datetime import datetime
from functools import wraps
import logging

staff_bp = Blueprint('staff', __name__)
logger = logging.getLogger(__name__)
ph = PasswordHasher()

# --- KONTROLA ADMIN ROLE ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.role_name != 'ADMIN':
            flash('Tato sekce je přístupná pouze pro administrátory.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- SEZNAM ZAMĚSTNANCŮ ---
@staff_bp.route('/staff')
@login_required
@admin_required
def staff_list():
    staff_members = StaffMember.query.join(Role).order_by(StaffMember.staff_id).all()
    roles = Role.query.all()
    return render_template('staff/list.html', staff_members=staff_members, roles=roles)

# --- PŘIDAT ZAMĚSTNANCE ---
@staff_bp.route('/staff/add', methods=['GET', 'POST'])
@login_required
@admin_required
def staff_add():
    roles = Role.query.all()
    
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            role_id = request.form.get('role_id')
            hire_date_str = request.form.get('hire_date')
            
            if not all([email, password, role_id, hire_date_str]):
                flash('Všechna pole jsou povinná.', 'danger')
            else:
                hashed_password = ph.hash(password)
                hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
                
                new_staff = StaffMember(
                    email=email,
                    password_hash=hashed_password,
                    role_id=int(role_id),
                    hire_date=hire_date
                )
                db.session.add(new_staff)
                db.session.commit()
                flash(f'Zaměstnanec {email} byl úspěšně přidán.', 'success')
                return redirect(url_for('staff.staff_list'))
                
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba při přidávání zaměstnance: {e}')
            flash(f'Chyba: {str(e)}', 'danger')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('staff/form_fragment.html', staff=None, roles=roles)

    return render_template('staff/form.html', staff=None, roles=roles)

# --- UPRAVIT ZAMĚSTNANCE ---
@staff_bp.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def staff_edit(staff_id):
    staff = StaffMember.query.get_or_404(staff_id)
    roles = Role.query.all()
    
    if request.method == 'POST':
        try:
            staff.email = request.form.get('email')
            staff.role_id = int(request.form.get('role_id'))
            
            hire_date_str = request.form.get('hire_date')
            if hire_date_str:
                staff.hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
            
            new_password = request.form.get('password')
            if new_password and new_password.strip():
                staff.password_hash = ph.hash(new_password)
                
            db.session.commit()
            flash(f'Zaměstnanec {staff.email} byl upraven.', 'success')
            return redirect(url_for('staff.staff_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba editace zaměstnance {staff_id}: {e}')
            flash('Chyba při úpravě.', 'danger')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('staff/form_fragment.html', staff=staff, roles=roles)

    return render_template('staff/form.html', staff=staff, roles=roles)

# --- SMAZAT ZAMĚSTNANCE ---
@staff_bp.route('/staff/delete/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def staff_delete(staff_id):
    if staff_id == current_user.staff_id:
        flash('Nemůžete smazat svůj vlastní účet!', 'danger')
        return redirect(url_for('staff.staff_list'))

    staff = StaffMember.query.get_or_404(staff_id)
    try:
        db.session.delete(staff)
        db.session.commit()
        flash('Zaměstnanec smazán.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Chyba při mazání.', 'danger')
    return redirect(url_for('staff.staff_list'))