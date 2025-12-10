import datetime
from app import db
from app.models import Category, Product, Role, StaffMember
from tests.base import BaseTestCase

class TestDatabase(BaseTestCase):
    
    def setUp(self):
        super().setUp()
        self.create_roles()

    def create_roles(self):
        """Pomocná metoda pro vytvoření rolí"""
        admin_role = Role(role_id=1, role_name='ADMIN')
        user_role = Role(role_id=2, role_name='USER')
        db.session.add_all([admin_role, user_role])
        db.session.commit()

    # --- TESTY ---

    # Vložení záznamu
    def test_category_creation(self):
        cat = Category(name="Elektronika")
        db.session.add(cat)
        db.session.commit()

        self.assertEqual(Category.query.count(), 1)
        retrieved = Category.query.filter_by(name="Elektronika").first()
        self.assertEqual(retrieved.name, "Elektronika")

    # Joiny a relace
    def test_product_creation_with_relation(self):
        cat = Category(name="Knihy")
        db.session.add(cat)
        db.session.commit()

        prod = Product(
            name="Harry Potter",
            base_price=399,
            category_id=cat.category_id,
            description="Fantasy román"
        )
        db.session.add(prod)
        db.session.commit()

        saved_prod = Product.query.filter_by(name="Harry Potter").first()
        self.assertEqual(saved_prod.category.name, "Knihy")

    def test_staff_member_insert(self):
        """Test: Vložení zaměstnance s datumem"""
        hire_date = datetime.date(2024, 1, 1)
        
        staff = StaffMember(
            email="test@bds.cz",
            password_hash="hash",
            role_id=1,
            hire_date=hire_date
        )
        db.session.add(staff)
        db.session.commit()

        fetched = StaffMember.query.filter_by(email="test@bds.cz").first()
        self.assertIsNotNone(fetched)

    # Úprava záznamu
    def test_product_update(self):
        cat = Category(name="Nábytek")
        db.session.add(cat)
        db.session.commit()
        
        prod = Product(name="Stůl", base_price=1000, category_id=cat.category_id)
        db.session.add(prod)
        db.session.commit()

        prod.base_price = 1200
        db.session.commit()

        updated_prod = Product.query.filter_by(name="Stůl").first()
        self.assertEqual(updated_prod.base_price, 1200)
    # Smazání záznamu
    def test_product_delete(self):
        cat = Category(name="Odpad")
        db.session.add(cat)
        db.session.commit()
        
        prod = Product(name="Ke smazání", base_price=10, category_id=cat.category_id)
        db.session.add(prod)
        db.session.commit()

        self.assertEqual(Product.query.count(), 1)

        # Smazání
        db.session.delete(prod)
        db.session.commit()

        self.assertEqual(Product.query.count(), 0)

    def test_product_filtering(self):
        cat = Category(name="Mix")
        db.session.add(cat)
        db.session.commit()

        p1 = Product(name="Modré auto", base_price=100, category_id=cat.category_id)
        p2 = Product(name="Červené auto", base_price=100, category_id=cat.category_id)
        db.session.add_all([p1, p2])
        db.session.commit()

        found = Product.query.filter(Product.name.contains("Modré")).all()
        
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].name, "Modré auto")

    # Transakce
    def test_transaction_rollback(self):
        db.session.add(Category(name="Test Rollback"))
        
        # Rollback
        db.session.rollback() 
        
        c = Category.query.filter_by(name="Test Rollback").first()
        self.assertIsNone(c)