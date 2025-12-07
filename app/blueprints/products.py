from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Product, Category, ProductImage
from app.utils import handle_image_upload
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import logging

products_bp = Blueprint('products', __name__)
logger = logging.getLogger(__name__)

# --- SEZNAM PRODUKTŮ ---
@products_bp.route('/products')
@login_required
def products_list():
    search_term = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)

    query = Product.query.join(Category, isouter=True)
    
    if search_term:
        query = query.filter(or_(
            Product.name.ilike(f'%{search_term}%'),
            Product.description.ilike(f'%{search_term}%')
        ))
    
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.product_id.desc()).all()
    categories = Category.query.all()
    
    return render_template('products/list.html', 
                           products=products, 
                           categories=categories, 
                           search_term=search_term,
                           selected_category_id=category_id)

# --- DETAIL PRODUKTU ---
@products_bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    product = Product.query.options(
        db.joinedload(Product.category),
        db.joinedload(Product.variants),
        db.joinedload(Product.images)
    ).get_or_404(product_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('products/modal_fragment.html', product=product)
    
    return render_template('products/detail.html', product=product)

# --- PŘIDAT PRODUKT ---
@products_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def product_add():
    categories = Category.query.all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            base_price = request.form.get('base_price')
            category_id = request.form.get('category_id', type=int)

            if not all([name, base_price, category_id]):
                flash('Vyplňte povinná pole.', 'danger')
                template = 'products/form_fragment.html' if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else 'products/form.html'
                return render_template(template, form_data=request.form, categories=categories, product=None)

            new_product = Product(name=name, description=description, base_price=base_price, category_id=category_id)
            db.session.add(new_product)
            db.session.flush()

            file = request.files.get('product_image')
            image_url = handle_image_upload(new_product.product_id, file)
            if image_url:
                db.session.add(ProductImage(product_id=new_product.product_id, url=image_url, sort_order=1))

            db.session.commit()
            flash(f'Produkt "{name}" přidán.', 'success')
            return redirect(url_for('products.products_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba add: {e}')
            flash('Chyba uložení.', 'danger')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('products/form_fragment.html', product=None, categories=categories)

    return render_template('products/form.html', categories=categories, product=None)

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
            
            db.session.commit()
            flash(f'Produkt "{product.name}" aktualizován.', 'success')
            return redirect(url_for('products.products_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba edit: {e}')
            flash('Chyba při aktualizaci.', 'danger')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('products/form_fragment.html', product=product, categories=categories)

    return render_template('products/form.html', categories=categories, product=product)

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