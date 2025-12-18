import sys
from datetime import date
from argon2 import PasswordHasher
from app import create_app, db
from app.models import StaffMember, Role

app = create_app()
ph = PasswordHasher()

def create_admin_user():
    with app.app_context():
        print("--- Vytváření Admin uživatele ---")

        role = Role.query.filter(Role.role_name.ilike('admin')).first()
        
        if not role:
            print("Role 'ADMIN' nebyla v databázi nalezena.")
            try:
                role = Role(role_name='ADMIN')
                db.session.add(role)
                db.session.commit()
                print(f"-> Vytvořena nová role: {role.role_name} (ID: {role.role_id})")
            except Exception as e:
                db.session.rollback()
                print(f"Chyba při vytváření role: {e}")
                return
        else:
            print(f"-> Používám existující roli: {role.role_name} (ID: {role.role_id})")

        target_email = "admin@eshop.cz"
        target_password = "admin"

        existing_user = StaffMember.query.filter_by(email=target_email).first()
        
        if existing_user:
            print(f"Uživatel '{target_email}' již existuje.")
            existing_user.password_hash = ph.hash(target_password)
            db.session.commit()
            print("-> Heslo bylo resetováno na 'admin'.")
        else:
            new_admin = StaffMember(
                email=target_email,
                password_hash=ph.hash(target_password),
                role_id=role.role_id,
                hire_date=date.today() 
            )
            
            try:
                db.session.add(new_admin)
                db.session.commit()
                print(f"-> Uživatel '{target_email}' byl úspěšně vytvořen.")
            except Exception as e:
                db.session.rollback()
                print(f"Chyba při ukládání uživatele: {e}")

if __name__ == "__main__":
    create_admin_user()