from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import CustomerProfile, Order
from sqlalchemy.orm import joinedload
from datetime import datetime
import logging

customers_bp = Blueprint('customers', __name__)
logger = logging.getLogger(__name__)

# --- SEZNAM ZÁKAZNÍKŮ ---
@customers_bp.route('/customers')
@login_required
def customers_list():
    
    customers = CustomerProfile.query.options(joinedload(CustomerProfile.user)).order_by(CustomerProfile.customer_id).all()
    return render_template('customers/list.html', customers=customers)

# --- HYBRIDNÍ EDITACE ZÁKAZNÍKA ---
@customers_bp.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def customer_edit(customer_id):
    customer = CustomerProfile.query.get_or_404(customer_id)
    
    if request.method == 'POST':
        try:
            customer.first_name = request.form.get('first_name')
            customer.last_name = request.form.get('last_name')
            
            dob = request.form.get('date_of_birth')
            if dob:
                customer.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
            
            db.session.commit()
            flash(f'Zákazník {customer.first_name} {customer.last_name} byl úspěšně upraven.', 'success')
            
            return redirect(url_for('customers.customers_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba při úpravě zákazníka {customer_id}: {e}')
            flash('Došlo k chybě při ukládání změn.', 'danger')

    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('customers/form_fragment.html', customer=customer)

    return render_template('customers/form.html', customer=customer)

# --- HTML FRAGMENT PRO DETAIL ZÁKAZNÍKA ---
@customers_bp.route('/customers/detail_content/<int:customer_id>')
@login_required
def customer_detail_content(customer_id):
    customer = CustomerProfile.query.options(
        joinedload(CustomerProfile.orders).joinedload(Order.status), 
        joinedload(CustomerProfile.addresses)
    ).get_or_404(customer_id)
    
    return render_template('customers/detail_fragment.html', customer=customer)