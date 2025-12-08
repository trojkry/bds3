from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask import jsonify as flask_jsonify
from flask_login import login_required
from app import db
from app.models import Order, OrderItem, CustomerProfile, OrderStatus, ShippingMethod, ProductVariant, Product, PaymentTransaction
from sqlalchemy import or_, cast, String
from sqlalchemy.orm import joinedload
import logging

orders_bp = Blueprint('orders', __name__)
logger = logging.getLogger(__name__)

@orders_bp.context_processor
def utility_processor():
    def get_available_statuses():
        return OrderStatus.query.all()
    return dict(get_available_statuses=get_available_statuses)

# --- SEZNAM OBJEDNÁVEK ---
@orders_bp.route('/orders')
@login_required
def orders_list():
    search_term = request.args.get('search', '').strip()
    status_id = request.args.get('status_id', type=int)
    is_paid = request.args.get('is_paid', '') 
    
    sort_by = request.args.get('sort_by', 'order_id')
    sort_order = request.args.get('sort_order', 'desc')

    query = Order.query.join(CustomerProfile).join(OrderStatus).join(ShippingMethod)

    if search_term:
        conditions = [
            CustomerProfile.first_name.ilike(f'%{search_term}%'),
            CustomerProfile.last_name.ilike(f'%{search_term}%'),
            cast(Order.order_id, String).ilike(f'%{search_term}%')
        ]
        query = query.filter(or_(*conditions))

    if status_id:
        query = query.filter(Order.status_id == status_id)
    
    if is_paid != '':
        if is_paid == '1':
            query = query.filter(Order.is_paid == True)
        elif is_paid == '0':
            query = query.filter(Order.is_paid == False)

    order_column = Order.order_id
    if sort_by == 'customer':
        order_column = CustomerProfile.last_name
    elif sort_by == 'date':
        order_column = Order.order_date
    elif sort_by == 'status':
        order_column = OrderStatus.status_name
    elif sort_by == 'amount':
        order_column = Order.total_amount
    elif sort_by == 'paid':
        order_column = Order.is_paid
    elif sort_by == 'order_id':
        order_column = Order.order_id

    if sort_order == 'asc':
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    orders = query.all()
    
    return render_template('orders/list.html', 
                           orders=orders,
                           search_term=search_term,
                           selected_status_id=status_id,
                           selected_paid=is_paid,
                           sort_by=sort_by,
                           sort_order=sort_order)

# --- DETAIL OBJEDNÁVKY FULL ---
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
        # 1. Smazat položky objednávky (OrderItem)
        OrderItem.query.filter_by(order_id=order.order_id).delete()
        
        # 2. Smazat platby (PaymentTransaction) - pokud existují
        PaymentTransaction.query.filter_by(order_id=order.order_id).delete()

        # 3. Smazat samotnou objednávku
        db.session.delete(order)
        db.session.commit()
        flash(f'Objednávka {order_id} byla úspěšně smazána.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Chyba při mazání objednávky {order_id}: {e}')
        flash('Chyba při mazání objednávky. Zkontrolujte závislosti.', 'danger')
    return redirect(url_for('orders.orders_list'))

# --- OBSAH OKNA ---
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

# --- OBSAH SEZNAMU ---
@orders_bp.route('/orders/detail_content/<int:order_id>')
@login_required
def order_detail_content(order_id):
    order = Order.query.options(
        db.joinedload(Order.items).joinedload(OrderItem.variant).joinedload(ProductVariant.product)
    ).get_or_404(order_id)
    
    return render_template('orders/detail_fragment.html', order=order)

# --- API PRO NAŠEPOVÁNÍ (ZÁKAZNÍCI) ---
@orders_bp.route('/api/search_customers')
@login_required
def search_customers():
    query = request.args.get('q', '').strip()
    if not query: return flask_jsonify([])
    
    customers = CustomerProfile.query.filter(
        or_(
            CustomerProfile.first_name.ilike(f'%{query}%'),
            CustomerProfile.last_name.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = [{'id': c.customer_id, 'text': f"{c.first_name} {c.last_name}"} for c in customers]
    return flask_jsonify(results)

# --- API PRO NAŠEPOVÁNÍ (PRODUKTY) ---
@orders_bp.route('/api/search_products')
@login_required
def search_products():
    query = request.args.get('q', '').strip()
    if not query: return flask_jsonify([])
    
    products = Product.query.filter(Product.name.ilike(f'%{query}%')).limit(10).all()
    results = []
    
    for p in products:
        variants = []
        for v in p.variants:
            price = float(p.base_price + (v.additional_price or 0))
            variants.append({
                'id': v.variant_id, 
                'sku': v.sku, 
                'attribute': v.attribute_value, 
                'price': price
            })
        results.append({'id': p.product_id, 'name': p.name, 'variants': variants})
        
    return flask_jsonify(results)

# --- VYTVOŘENÍ OBJEDNÁVKY OKNO ---
@orders_bp.route('/orders/create', methods=['GET', 'POST'])
@login_required
def order_create():
    shipping_methods = ShippingMethod.query.all()

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        try:
            customer_id = request.form.get('customer_id')
            shipping_method_id = request.form.get('shipping_method_id')
            
            if not customer_id or not shipping_method_id:
                raise ValueError("Chybí zákazník nebo metoda dopravy.")

            shipping_method = ShippingMethod.query.get(shipping_method_id)
            new_order = Order(
                customer_id=int(customer_id),
                status_id=1,
                shipping_method_id=int(shipping_method_id),
                order_date=db.func.current_date(),
                shipping_cost=shipping_method.price,
                total_amount=0,
                is_paid=False
            )
            db.session.add(new_order)
            db.session.flush()

            total_items_price = 0
            variant_ids = request.form.getlist('variant_id[]')
            quantities = request.form.getlist('quantity[]')
            
            valid_items_count = 0
            
            if not variant_ids:
                raise ValueError("Objednávka neobsahuje žádné produkty.")

            for i in range(len(variant_ids)):
                if not variant_ids[i] or variant_ids[i] == '':
                    continue
                    
                v_id = int(variant_ids[i])
                qty = int(quantities[i])
                
                if qty < 1: continue

                variant = ProductVariant.query.get(v_id)
                final_price = variant.product.base_price + (variant.additional_price or 0)
                
                item = OrderItem(order_id=new_order.order_id, variant_id=v_id, quantity=qty, unit_price=final_price)
                db.session.add(item)
                total_items_price += (final_price * qty)
                valid_items_count += 1

            if valid_items_count == 0:
                raise ValueError("Nebyly vybrány žádné platné produkty.")

            new_order.total_amount = total_items_price + new_order.shipping_cost
            db.session.commit()
            
            success_msg = f'Objednávka #{new_order.order_id} byla úspěšně vytvořena.'
            
            if is_ajax:
                return flask_jsonify({'success': True, 'message': success_msg})
            
            flash(success_msg, 'success')
            return redirect(url_for('orders.orders_list'))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba create: {e}')
            msg = f'Chyba: {str(e)}'
            
            if is_ajax:
                return flask_jsonify({'success': False, 'message': msg}), 400
                
            flash(msg, 'danger')
            return redirect(url_for('orders.orders_list'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('orders/create_fragment.html', shipping_methods=shipping_methods)

    return "Pro vytvoření použijte tlačítko v seznamu."