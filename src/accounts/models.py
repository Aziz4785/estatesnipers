from datetime import datetime
from flask_login import UserMixin
from src import bcrypt, db,app
from itsdangerous import URLSafeTimedSerializer,BadSignature,SignatureExpired

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

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def __repr__(self):
        return f"<email {self.email}>"
    
    def generate_reset_password_token(self):
        serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
        return serializer.dumps(self.email, salt=self.password)

    @staticmethod
    def validate_reset_password_token(token: str, user_id: int):
        user = db.session.get(User, user_id)

        if user is None:
            return None

        serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
        try:
            token_user_email = serializer.loads(
                token,
                max_age=3600, #1 hour before expiration
                salt=user.password,
            )
        except (BadSignature, SignatureExpired):
            return None

        if token_user_email != user.email:
            return None

        return user


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