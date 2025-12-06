from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Product, Category
from sqlalchemy import or_
import logging

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

# VÝPIS PRODUKTŮ
@main_bp.route('/products')
@login_required
def products_list():
    
    search_term = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)

    query = Product.query.join(Category, isouter=True) 
    
    
    if search_term:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search_term}%'),
                Product.description.ilike(f'%{search_term}%')
            )
        )
    
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.product_id.desc()).all() # Požadavek: findAll
    categories = Category.query.all()
    
    return render_template('products/list.html', 
                           products=products, 
                           categories=categories, 
                           search_term=search_term,
                           selected_category_id=category_id)

#ZOBRAZENÍ DETAILU (DETAIL VIEW & JOIN)
@main_bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    # Relace 'variants' definovaná v models.py automaticky provede JOIN
    product = Product.query.get_or_404(product_id) # Požadavek: Detail View (JOIN)
    return render_template('products/detail.html', product=product)


#VYTVOŘENÍ PRODUKTU
@main_bp.route('/products/add', methods=['GET', 'POST'])
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
                flash('Všechna povinná pole musí být vyplněna.', 'danger')
                return render_template('products/form.html', form_data=request.form, categories=categories, product=None)

            new_product = Product(
                name=name,
                description=description,
                base_price=base_price,
                category_id=category_id
            )
            
            db.session.add(new_product)
            db.session.commit()
            flash(f'Produkt "{name}" byl úspěšně přidán.', 'success')
            return redirect(url_for('main.products_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba při přidávání produktu: {e}') # Požadavek: Logování
            flash('Došlo k chybě při ukládání produktu do databáze.', 'danger')

    return render_template('products/form.html', categories=categories, product=None)


#EDITACE PRODUKTU
@main_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
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
            
            db.session.commit()
            flash(f'Produkt "{product.name}" byl úspěšně aktualizován.', 'success')
            return redirect(url_for('main.products_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba při editaci produktu {product_id}: {e}')
            flash('Došlo k chybě při aktualizaci produktu v databázi.', 'danger')

    
    return render_template('products/form.html', categories=categories, product=product)


#SMAZÁNÍ PRODUKTU
@main_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    
    try:
        product_name = product.name
        db.session.delete(product)
        db.session.commit()
        flash(f'Produkt "{product_name}" byl úspěšně smazán.', 'success')
        
    except Exception as e:
        db.session.rollback() 
        logger.error(f'Chyba při mazání produktu {product_id}: {e}')
        flash('Došlo k chybě při mazání produktu. Zkontrolujte závislosti (např. varianty/položky objednávky).', 'danger')

    return redirect(url_for('main.products_list'))


