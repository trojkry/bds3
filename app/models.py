from app import db

class StaffMember(db.Model):

    __tablename__ = 'staff_member'
    __table_args__ = {'schema': 'bds'}

    staff_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, nullable=False)


    def __repr__(self):
        return f'<StaffMember {self.email}>'