from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.models import StaffMember

auth_bp = Blueprint('auth', __name__)
ph = PasswordHasher()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        
        user = StaffMember.query.filter_by(email=email).first()
        
        if user and user.password_hash:
            try:
                
                if ph.verify(user.password_hash, password):
                    login_user(user)
                    flash('Úspěšně přihlášen.', 'success')
                    
                    return redirect(url_for('index'))
            except VerifyMismatchError:
                
                pass
        
        flash('Neplatný email nebo heslo.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Byli jste odhlášeni.', 'info')
    return redirect(url_for('auth.login'))