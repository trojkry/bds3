from app import db
from flask_login import UserMixin

class StaffMember(UserMixin, db.Model):

    __tablename__ = 'staff_member'
    __table_args__ = {'schema': 'bds'}

    staff_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    role_id = db.Column(db.Integer, nullable=False)
    hire_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<StaffMember {self.email}>'
    
    def get_id(self):
        return str(self.staff_id)