from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Product, Category, ProductImage, ProductVariant
from app.utils import handle_image_upload
from sqlalchemy import or_, cast, String
from sqlalchemy.orm import joinedload
import logging
import random
import string

products_bp = Blueprint('products', __name__)
logger = logging.getLogger(__name__)

# --- FUNKCE PRO ZPRACOVÁNÍ VARIANT ---
def process_variants(product, form):
    variant_ids = form.getlist('variant_id[]')
    attrs = form.getlist('variant_attr[]')
    skus = form.getlist('variant_sku[]')
    prices = form.getlist('variant_price[]')
    
    delete_ids = form.getlist('delete_variant[]')
    if delete_ids:
        ProductVariant.query.filter(ProductVariant.variant_id.in_(delete_ids)).delete(synchronize_session=False)

    for v_id, attr, sku, price in zip(variant_ids, attrs, skus, prices):
        if v_id in delete_ids:
            continue
            
        if not attr.strip():
            continue 

        try:
            add_price = float(price) if price else 0.0
        except ValueError:
            add_price = 0.0

        final_sku = sku.strip()
        if not final_sku:
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            final_sku = f"{product.name[:3].upper()}-{attr[:3].upper()}-{suffix}"

        if v_id == '0':
            new_variant = ProductVariant(
                product_id=product.product_id,
                attribute_value=attr,
                sku=final_sku,
                additional_price=add_price
            )
            db.session.add(new_variant)
        else:
            existing = ProductVariant.query.get(int(v_id))
            if existing:
                existing.attribute_value = attr
                existing.sku = final_sku
                existing.additional_price = add_price

# --- SEZNAM PRODUKTŮ ---
@products_bp.route('/products')
@login_required
def products_list():
    search_term = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    
    sort_by = request.args.get('sort_by', 'product_id')
    sort_order = request.args.get('sort_order', 'desc')

    query = Product.query.join(Category, isouter=True)
    
    if search_term:
        conditions = [
            Product.name.ilike(f'%{search_term}%'),
            Product.description.ilike(f'%{search_term}%'),
            cast(Product.product_id, String).ilike(f'%{search_term}%')
        ]
        
        query = query.filter(or_(*conditions))
    
    if category_id:
        query = query.filter(Product.category_id == category_id)

    order_column = Product.product_id 
    if sort_by == 'name':
        order_column = Product.name
    elif sort_by == 'base_price':
        order_column = Product.base_price
    elif sort_by == 'category_name':
        order_column = Category.name
    elif sort_by == 'product_id':
        order_column = Product.product_id

    if sort_order == 'asc':
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    products = query.all()
    categories = Category.query.all()
    
    return render_template('products/list.html', 
                           products=products, 
                           categories=categories, 
                           search_term=search_term,
                           selected_category_id=category_id,
                           sort_by=sort_by,
                           sort_order=sort_order)

# --- DETAIL PRODUKTU ---
@products_bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    product = Product.query.options(db.joinedload(Product.category), db.joinedload(Product.variants), db.joinedload(Product.images)).get_or_404(product_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('products/modal_fragment.html', product=product)
    
    return render_template('products/detail.html', product=product)

# --- FRAGMENT PRO ACCORDION ---
@products_bp.route('/products/detail_content/<int:product_id>')
@login_required
def product_detail_content(product_id):
    product = Product.query.options(
        joinedload(Product.category),
        joinedload(Product.variants),
        joinedload(Product.images)
    ).get_or_404(product_id)
    
    return render_template('products/detail_fragment.html', product=product)

# --- PŘIDAT PRODUKT ---
@products_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def product_add():
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            base_price = request.form.get('base_price')
            category_id = request.form.get('category_id', type=int)

            if not all([name, base_price, category_id]):
                flash('Vyplňte povinná pole.', 'danger')
                template = 'products/form_fragment.html' if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else 'products/form.html'
                return render_template(template, product=None, categories=categories, form_data=request.form)

            variant_attrs = request.form.getlist('variant_attr[]')
            valid_variants = [attr for attr in variant_attrs if attr.strip()]

            if not valid_variants:
                flash('Nelze vytvořit produkt bez variant. Přidejte alespoň jednu.', 'danger')
                template = 'products/form_fragment.html' if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else 'products/form.html'
                return render_template(template, product=None, categories=categories, form_data=request.form)

            description = request.form.get('description')
            new_product = Product(name=name, description=description, base_price=base_price, category_id=category_id)
            db.session.add(new_product)
            db.session.flush()

            file = request.files.get('product_image')
            image_url = handle_image_upload(new_product.product_id, file)
            if image_url:
                db.session.add(ProductImage(product_id=new_product.product_id, url=image_url, sort_order=1))

            process_variants(new_product, request.form)

            db.session.commit()
            flash(f'Produkt "{name}" byl úspěšně vytvořen.', 'success')
            return redirect(url_for('products.products_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba add: {e}')
            flash(f'Chyba uložení: {str(e)}', 'danger')

    template = 'products/form_fragment.html' if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else 'products/form.html'
    return render_template(template, product=None, categories=categories)

# --- UPRAVIT PRODUKT ---
@products_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            product.base_price = request.form.get('base_price')
            product.category_id = request.form.get('category_id', type=int)
            
            file = request.files.get('product_image')
            image_url = handle_image_upload(product.product_id, file)

            if image_url:
                primary_image = ProductImage.query.filter_by(product_id=product.product_id, sort_order=1).first()
                if primary_image:
                    primary_image.url = image_url
                else:
                    db.session.add(ProductImage(product_id=product.product_id, url=image_url, sort_order=1))
            
            process_variants(product, request.form)
            
            db.session.commit()
            flash(f'Produkt "{product.name}" aktualizován.', 'success')
            return redirect(url_for('products.products_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba edit: {e}')
            flash('Chyba při aktualizaci.', 'danger')

    template = 'products/form_fragment.html' if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else 'products/form.html'
    return render_template(template, product=product, categories=categories)

# --- SMAZAT PRODUKT ---
@products_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        db.session.delete(product)
        db.session.commit()
        flash('Smazáno.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f'Chyba mazání: {e}')
        flash('Chyba mazání.', 'danger')
    return redirect(url_for('products.products_list'))