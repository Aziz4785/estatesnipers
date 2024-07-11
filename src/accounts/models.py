from datetime import datetime
from flask_login import UserMixin
from src import bcrypt, db


class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, email, password, is_admin=False):
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8') #because https://stackoverflow.com/questions/34548846/flask-bcrypt-valueerror-invalid-salt
        self.created_on = datetime.now()
        self.is_admin = is_admin

    def __repr__(self):
        return f"<email {self.email}>"
    

class StripeCustomer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    stripeCustomerId = db.Column(db.String(255), nullable=False)
    stripeSubscriptionId = db.Column(db.String(255), nullable=False)

    def __init__(self, user_id, stripeCustomerId, stripeSubscriptionId):
        self.user_id = user_id
        self.stripeCustomerId = stripeCustomerId
        self.stripeSubscriptionId = stripeSubscriptionId

    def __repr__(self):
        return f"<StripeCustomer user_id={self.user_id}, stripeCustomerId={self.stripeCustomerId}>"