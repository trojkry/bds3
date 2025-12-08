from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import CustomerProfile, Order, OrderItem, Address, UserAccount, PaymentTransaction, ShoppingCart, CartItem
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, cast, String
from datetime import datetime
import logging

customers_bp = Blueprint('customers', __name__)
logger = logging.getLogger(__name__)

# --- SEZNAM ZÁKAZNÍKŮ ---
@customers_bp.route('/customers')
@login_required
def customers_list():
    search_term = request.args.get('search', '').strip()
    
    sort_by = request.args.get('sort_by', 'customer_id')
    sort_order = request.args.get('sort_order', 'asc')

    query = CustomerProfile.query.join(UserAccount, isouter=True)

    if search_term:
        conditions = [
            CustomerProfile.first_name.ilike(f'%{search_term}%'),
            CustomerProfile.last_name.ilike(f'%{search_term}%'),
            UserAccount.email.ilike(f'%{search_term}%'),
            cast(CustomerProfile.customer_id, String).ilike(f'%{search_term}%')
        ]
        query = query.filter(or_(*conditions))

    order_column = CustomerProfile.customer_id # Default
    
    if sort_by == 'first_name':
        order_column = CustomerProfile.first_name
    elif sort_by == 'last_name':
        order_column = CustomerProfile.last_name
    elif sort_by == 'email':
        order_column = UserAccount.email
    elif sort_by == 'dob':
        order_column = CustomerProfile.date_of_birth
    elif sort_by == 'customer_id':
        order_column = CustomerProfile.customer_id

    if sort_order == 'asc':
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    customers = query.options(joinedload(CustomerProfile.user)).all()
    
    return render_template('customers/list.html', 
                           customers=customers,
                           search_term=search_term,
                           sort_by=sort_by,
                           sort_order=sort_order)

# --- EDITACE ZÁKAZNÍKA ---
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
            else:
                customer.date_of_birth = None
            
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

# --- HTML PRO DETAIL ZÁKAZNÍKA ---
@customers_bp.route('/customers/detail_content/<int:customer_id>')
@login_required
def customer_detail_content(customer_id):
    customer = CustomerProfile.query.options(
        joinedload(CustomerProfile.user),
        joinedload(CustomerProfile.orders).joinedload(Order.status), 
        joinedload(CustomerProfile.addresses)
    ).get_or_404(customer_id)
    
    return render_template('customers/detail_fragment.html', customer=customer)

# --- SMAZAT ZÁKAZNÍKA ---
@customers_bp.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
def customer_delete(customer_id):
    customer = CustomerProfile.query.get_or_404(customer_id)
    user_account = customer.user
    
    try:
        carts = ShoppingCart.query.filter_by(customer_id=customer_id).all()
        for cart in carts:
            CartItem.query.filter_by(cart_id=cart.cart_id).delete()
            db.session.delete(cart)

        Address.query.filter_by(customer_id=customer_id).delete()

        orders = Order.query.filter_by(customer_id=customer_id).all()
        for order in orders:
            OrderItem.query.filter_by(order_id=order.order_id).delete()
            
            PaymentTransaction.query.filter_by(order_id=order.order_id).delete()
            
            db.session.delete(order)

        db.session.delete(customer)

        if user_account:
            db.session.delete(user_account)

        db.session.commit()
        flash(f'Zákazník a všechna jeho data byla úspěšně smazána.', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error(f'Chyba při mazání zákazníka {customer_id}: {e}')
        flash(f'Chyba při mazání zákazníka: {str(e)}', 'danger')

    return redirect(url_for('customers.customers_list'))