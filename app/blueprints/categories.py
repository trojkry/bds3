from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Category, Product
from sqlalchemy import or_
import logging

categories_bp = Blueprint('categories', __name__)
logger = logging.getLogger(__name__)

# --- SEZNAM KATEGORIÍ ---
@categories_bp.route('/categories')
@login_required
def categories_list():
    search_term = request.args.get('search', '').strip()
    
    query = Category.query
    
    if search_term:
        query = query.filter(Category.name.ilike(f'%{search_term}%'))

    categories = query.order_by(Category.category_id).all()
    
    return render_template('categories/list.html', 
                           categories=categories, 
                           search_term=search_term)

# --- PŘIDAT KATEGORII ---
@categories_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def category_add():
    all_categories = Category.query.order_by(Category.name).all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            parent_id = request.form.get('parent_id')
            
            if not name:
                flash('Název kategorie je povinný.', 'danger')
            else:
                parent_id_val = int(parent_id) if parent_id and parent_id.isdigit() else None
                
                new_cat = Category(name=name, parent_id=parent_id_val)
                db.session.add(new_cat)
                db.session.commit()
                
                flash(f'Kategorie "{name}" byla úspěšně přidána.', 'success')
                return redirect(url_for('categories.categories_list'))
                
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba při přidávání kategorie: {e}')
            flash('Chyba při ukládání.', 'danger')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('categories/form_fragment.html', category=None, all_categories=all_categories)

    return render_template('categories/form.html', category=None, all_categories=all_categories)

# --- UPRAVIT KATEGORII ---
@categories_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def category_edit(category_id):
    category = Category.query.get_or_404(category_id)
    all_categories = Category.query.filter(Category.category_id != category_id).order_by(Category.name).all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            parent_id = request.form.get('parent_id')
            
            if not name:
                flash('Název kategorie je povinný.', 'danger')
            else:
                parent_id_val = int(parent_id) if parent_id and parent_id.isdigit() else None
                
                if parent_id_val == category.category_id:
                    flash('Kategorie nemůže být nadřazená sama sobě.', 'danger')
                else:
                    category.name = name
                    category.parent_id = parent_id_val
                    db.session.commit()
                    flash(f'Kategorie "{name}" byla upravena.', 'success')
                    return redirect(url_for('categories.categories_list'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Chyba editace kategorie {category_id}: {e}')
            flash('Chyba při úpravě.', 'danger')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('categories/form_fragment.html', category=category, all_categories=all_categories)

    return render_template('categories/form.html', category=category, all_categories=all_categories)

# --- SMAZAT KATEGORII ---
@categories_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def category_delete(category_id):
    category = Category.query.get_or_404(category_id)
    
    products_count = Product.query.filter_by(category_id=category_id).count()
    subcategories_count = Category.query.filter_by(parent_id=category_id).count()
    
    if products_count > 0:
        flash(f'Nelze smazat: Kategorie obsahuje {products_count} produktů.', 'danger')
    elif subcategories_count > 0:
        flash(f'Nelze smazat: Kategorie má {subcategories_count} podkategorií.', 'danger')
    else:
        try:
            db.session.delete(category)
            db.session.commit()
            flash('Kategorie smazána.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Chyba databáze při mazání.', 'danger')
            
    return redirect(url_for('categories.categories_list'))