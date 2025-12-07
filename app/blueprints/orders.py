from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import jsonify as flask_jsonify 
from flask_login import login_required
from app import db
from app.models import Order, OrderItem, CustomerProfile, OrderStatus, ShippingMethod, ProductVariant
from sqlalchemy.orm import joinedload
import logging

orders_bp = Blueprint('orders', __name__)
logger = logging.getLogger(__name__)

# --- KONTEXTOVÝ PROCESOR ---
@orders_bp.context_processor
def utility_processor():
    def get_available_statuses():
        return OrderStatus.query.all()
    return dict(get_available_statuses=get_available_statuses)

# --- SEZNAM OBJEDNÁVEK ---
@orders_bp.route('/orders')
@login_required
def orders_list():
    orders = Order.query.join(CustomerProfile).join(OrderStatus).join(ShippingMethod).all()
    return render_template('orders/list.html', orders=orders)

# --- DETAIL OBJEDNÁVKY---
@orders_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.options(
        db.joinedload(Order.customer),
        db.joinedload(Order.status),
        db.joinedload(Order.shipping_method),
        db.joinedload(Order.items).joinedload(OrderItem.variant).joinedload(ProductVariant.product)
    ).get_or_404(order_id)
    return render_template('orders/detail.html', order=order)

# --- ZMĚNA STATUSU ---
@orders_bp.route('/orders/update_status/<int:order_id>', methods=['POST'])
@login_required
def order_update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status_id = request.form.get('status_id', type=int)
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not new_status_id:
        if is_ajax:
            return flask_jsonify({'success': False, 'message': 'Musíte vybrat status.'}), 400
        flash('Musíte vybrat nový status.', 'danger')
        return redirect(url_for('orders.order_detail', order_id=order_id))
        
    try:
        order.status_id = new_status_id
        db.session.commit()
        
        new_status_name = OrderStatus.query.get(new_status_id).status_name
        
        
        if is_ajax:
            return flask_jsonify({
                'success': True, 
                'message': 'Status byl úspěšně změněn.',
                'new_status_name': new_status_name
            })

        flash(f'Status objednávky {order_id} byl úspěšně změněn na "{new_status_name}".', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Chyba při aktualizaci statusu objednávky {order_id}: {e}')
        
        if is_ajax:
            return flask_jsonify({'success': False, 'message': f'Chyba: {str(e)}'}), 500
            
        flash('Chyba při aktualizaci statusu.', 'danger')
        
    return redirect(url_for('orders.order_detail', order_id=order_id))

# --- SMAZAT OBJEDNÁVKU ---
@orders_bp.route('/orders/delete/<int:order_id>', methods=['POST'])
@login_required
def order_delete(order_id):
    order = Order.query.get_or_404(order_id)
    try:
        db.session.delete(order)
        db.session.commit()
        flash(f'Objednávka {order_id} byla úspěšně smazána.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Chyba při mazání objednávky {order_id}: {e}')
        flash('Chyba při mazání objednávky. Zkontrolujte závislosti.', 'danger')
    return redirect(url_for('orders.orders_list'))

# --- OBSAH MODALU ---
@orders_bp.route('/orders/modal_content/<int:order_id>')
@login_required
def order_modal_content(order_id):
    order = Order.query.options(
        db.joinedload(Order.customer).joinedload(CustomerProfile.user),
        db.joinedload(Order.customer).joinedload(CustomerProfile.addresses),
        db.joinedload(Order.status),
        db.joinedload(Order.shipping_method),
        db.joinedload(Order.items).joinedload(OrderItem.variant).joinedload(ProductVariant.product)
    ).get_or_404(order_id)
    
    all_statuses = OrderStatus.query.all()
    
    return render_template('orders/modal_fragment.html', order=order, all_statuses=all_statuses)

@orders_bp.route('/orders/detail_content/<int:order_id>')
@login_required
def order_detail_content(order_id):
    order = Order.query.options(
        db.joinedload(Order.items).joinedload(OrderItem.variant).joinedload(ProductVariant.product)
    ).get_or_404(order_id)
    
    return render_template('orders/detail_fragment.html', order=order)