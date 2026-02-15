from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from .models import Transaction
from . import db
from datetime import datetime, timedelta

transaction_bp = Blueprint("transactions", __name__, url_prefix="/app")


def get_user_monthly_income(user_id):
    """Получает средний месячный доход пользователя за последние 3 месяца"""
    three_months_ago = datetime.utcnow() - timedelta(days=90)
    
    if current_user.family_id:
        q = Transaction.query.filter_by(family_id=current_user.family_id, type='income')
    else:
        q = Transaction.query.filter_by(user_id=user_id, type='income')
    
    transactions = q.filter(Transaction.date >= three_months_ago).all()
    
    if not transactions:
        return 50000  # Значение по умолчанию
    
    total_income = sum(t.amount for t in transactions)
    months_set = set(t.date.strftime('%Y-%m') for t in transactions)
    months_count = max(1, len(months_set))
    
    return total_income / months_count


@transaction_bp.route("/dashboard")
@login_required
def dashboard():
    # если пользователь в семье — показываем семейные операции,
    # иначе только его личные
    if current_user.family_id:
        q = Transaction.query.filter_by(family_id=current_user.family_id)
    else:
        q = Transaction.query.filter_by(user_id=current_user.id)

    total_income = (
        q.filter_by(type="income")
         .with_entities(func.sum(Transaction.amount))
         .scalar() or 0
    )
    total_expense = (
        q.filter_by(type="expense")
         .with_entities(func.sum(Transaction.amount))
         .scalar() or 0
    )

    last_transactions = (
        q.order_by(Transaction.date.desc())
         .limit(10)
         .all()
    )

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expense=total_expense,
        last_transactions=last_transactions,
    )


@transaction_bp.route("/add", methods=["POST"])
@login_required
def add_transaction():
    t = Transaction(
        user_id=current_user.id,
        family_id=current_user.family_id,  # если нет семьи — будет None
        type=request.form["type"],
        amount=float(request.form["amount"]),
        category=request.form["category"],
        description=request.form.get("description"),
    )
    db.session.add(t)
    db.session.commit()
    
    # Автоматический AI-анализ для крупных расходов
    if t.type == 'expense' and t.amount > 5000:
        from app.ai_service import analyze_transaction
        
        # Получаем месячный доход пользователя для расчёта процента
        user_monthly_income = get_user_monthly_income(current_user.id)
        
        advice = analyze_transaction({
            'amount': t.amount,
            'category': t.category,
            'user_monthly_income': user_monthly_income
        })
        
        if advice:
            flash(f"💡 {advice}", "info")
    
    return redirect(url_for("transactions.dashboard"))