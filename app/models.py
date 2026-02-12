from datetime import datetime
from flask_login import UserMixin
from . import db
import uuid

class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    invite_code = db.Column(db.String(16), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    members = db.relationship("User", backref="family", lazy=True)
    transactions = db.relationship("Transaction", backref="family", lazy=True)
    
    def generate_invite_code(self):
        self.invite_code = uuid.uuid4().hex[:8].upper()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(128))
    family_id = db.Column(db.Integer, db.ForeignKey("family.id"))


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey("family.id"))
    
    # Основные поля
    type = db.Column(db.String(10), nullable=False)  # 'income' / 'expense'
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # НОВЫЕ ПОЛЯ ДЛЯ ЧЕКОВ
    receipt_image = db.Column(db.String(512))  # Путь к скану чека
    merchant_name = db.Column(db.String(128))  # Название магазина/ресторана
    
    # Связь с товарами из чека
    items = db.relationship("TransactionItem", backref="transaction", lazy=True, cascade="all, delete-orphan")


# НОВАЯ МОДЕЛЬ для детализации чеков
class TransactionItem(db.Model):
    """Товары из чека"""
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transaction.id"), nullable=False)
    item_name = db.Column(db.String(128), nullable=False)
    quantity = db.Column(db.Float, default=1.0)
    price = db.Column(db.Float, nullable=False)
