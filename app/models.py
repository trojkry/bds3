from app import db
from flask_login import UserMixin
from sqlalchemy.orm import relationship

# ---------------------- UŽIVATELÉ A ROLE ----------------------

class Role(db.Model):
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'bds'}
    
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(30), nullable=False)
    
    staff_members = relationship('StaffMember', backref='role', lazy=True)

class StaffMember(UserMixin, db.Model):
    __tablename__ = 'staff_member'
    __table_args__ = {'schema': 'bds'}

    staff_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('bds.roles.role_id'), nullable=False)
    hire_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<StaffMember {self.email}>'
    
    def get_id(self):
        return str(self.staff_id)

class CustomerProfile(db.Model):
    __tablename__ = 'customer_profile'
    __table_args__ = {'schema': 'bds'}

    customer_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    
    orders = relationship('Order', backref='customer', lazy=True)

# ---------------------- PRODUKTY A KATEGORIE ----------------------

class Category(db.Model):
    __tablename__ = 'category'
    __table_args__ = {'schema': 'bds'}

    category_id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('bds.category.category_id'))
    name = db.Column(db.String(100), nullable=False)

    products = relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    __tablename__ = 'product'
    __table_args__ = {'schema': 'bds'}

    product_id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('bds.category.category_id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    is_featured = db.Column(db.Boolean, default=False)
    
    variants = relationship('ProductVariant', backref='product', lazy=True, cascade="all, delete-orphan")

class ProductVariant(db.Model):
    __tablename__ = 'product_variant'
    __table_args__ = {'schema': 'bds'}

    variant_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('bds.product.product_id'), nullable=False)
    sku = db.Column(db.String(50), nullable=False)
    attribute_value = db.Column(db.String(100), nullable=False)
    additional_price = db.Column(db.Numeric(10, 2))

# ---------------------- OBJEDNÁVKY ----------------------

class OrderStatus(db.Model):
    __tablename__ = 'order_status'
    __table_args__ = {'schema': 'bds'}
    
    status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), nullable=False)

class ShippingMethod(db.Model):
    __tablename__ = 'shipping_method'
    __table_args__ = {'schema': 'bds'}

    shipping_method_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = {'schema': 'bds'}

    order_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('bds.customer_profile.customer_id'), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('bds.order_status.status_id'), nullable=False)
    shipping_method_id = db.Column(db.Integer, db.ForeignKey('bds.shipping_method.shipping_method_id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False, default=db.func.current_date())
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_cost = db.Column(db.Numeric(10, 2), nullable=False)
    is_paid = db.Column(db.Boolean, default=False)

    status = relationship('OrderStatus')
    shipping_method = relationship('ShippingMethod')
    items = relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    __table_args__ = {'schema': 'bds'}

    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('bds.orders.order_id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('bds.product_variant.variant_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    variant = relationship('ProductVariant')