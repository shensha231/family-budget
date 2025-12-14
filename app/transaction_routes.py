from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from .models import Transaction
from . import db

transaction_bp = Blueprint("transactions", __name__, url_prefix="/app")


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
    return redirect(url_for("transactions.dashboard"))
