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
<<<<<<< HEAD
    
    # Группируем расходы по категориям для графика (из всех транзакций, не только последних)
    expense_by_category = {}
    
    # Получаем все расходы для более точной статистики
    if current_user.family_id:
        expense_query = Transaction.query.filter_by(family_id=current_user.family_id, type='expense')
    else:
        expense_query = Transaction.query.filter_by(user_id=current_user.id, type='expense')
    
    all_expenses = expense_query.all()
    
    for t in all_expenses:
        if t.category not in expense_by_category:
            expense_by_category[t.category] = 0
        expense_by_category[t.category] += t.amount
=======
>>>>>>> 86e1b5366313f5eb2c1c708d8c6a1d9e73968a3f

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expense=total_expense,
        last_transactions=last_transactions,
<<<<<<< HEAD
        expense_by_category=expense_by_category  # ← ВАЖНО: передаём данные для графика
=======
>>>>>>> 86e1b5366313f5eb2c1c708d8c6a1d9e73968a3f
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
    
<<<<<<< HEAD
    return redirect(url_for("transactions.dashboard"))


@transaction_bp.route("/delete/<int:transaction_id>", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    """Удаление транзакции"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Проверяем права на удаление
    if transaction.user_id != current_user.id and transaction.family_id != current_user.family_id:
        flash("У вас нет прав на удаление этой транзакции", "danger")
        return redirect(url_for("transactions.dashboard"))
    
    db.session.delete(transaction)
    db.session.commit()
    flash("Транзакция удалена", "success")
    return redirect(url_for("transactions.dashboard"))


@transaction_bp.route("/edit/<int:transaction_id>", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    """Редактирование транзакции"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Проверяем права на редактирование
    if transaction.user_id != current_user.id and transaction.family_id != current_user.family_id:
        flash("У вас нет прав на редактирование этой транзакции", "danger")
        return redirect(url_for("transactions.dashboard"))
    
    if request.method == "POST":
        transaction.type = request.form["type"]
        transaction.amount = float(request.form["amount"])
        transaction.category = request.form["category"]
        transaction.description = request.form.get("description")
        
        db.session.commit()
        flash("Транзакция обновлена", "success")
        return redirect(url_for("transactions.dashboard"))
    
    return render_template("edit_transaction.html", transaction=transaction)


@transaction_bp.route("/all")
@login_required
def all_transactions():
    """Просмотр всех транзакций с фильтрацией"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if current_user.family_id:
        q = Transaction.query.filter_by(family_id=current_user.family_id)
    else:
        q = Transaction.query.filter_by(user_id=current_user.id)
    
    # Фильтры
    transaction_type = request.args.get('type')
    if transaction_type in ['income', 'expense']:
        q = q.filter_by(type=transaction_type)
    
    category = request.args.get('category')
    if category:
        q = q.filter_by(category=category)
    
    # Сортировка
    sort = request.args.get('sort', 'date_desc')
    if sort == 'date_desc':
        q = q.order_by(Transaction.date.desc())
    elif sort == 'date_asc':
        q = q.order_by(Transaction.date.asc())
    elif sort == 'amount_desc':
        q = q.order_by(Transaction.amount.desc())
    elif sort == 'amount_asc':
        q = q.order_by(Transaction.amount.asc())
    
    # Пагинация
    transactions = q.paginate(page=page, per_page=per_page, error_out=False)
    
    # Получаем уникальные категории для фильтра
    categories = db.session.query(Transaction.category).distinct().filter(
        (Transaction.user_id == current_user.id) | (Transaction.family_id == current_user.family_id)
    ).all()
    categories = [c[0] for c in categories]
    
    return render_template(
        "all_transactions.html",
        transactions=transactions,
        categories=categories,
        current_filters={
            'type': transaction_type,
            'category': category,
            'sort': sort
        }
    )


@transaction_bp.route("/stats")
@login_required
def statistics():
    """Детальная статистика по транзакциям"""
    if current_user.family_id:
        q = Transaction.query.filter_by(family_id=current_user.family_id)
    else:
        q = Transaction.query.filter_by(user_id=current_user.id)
    
    # Статистика по месяцам
    current_year = datetime.utcnow().year
    
    monthly_stats = []
    for month in range(1, 13):
        month_income = q.filter(
            Transaction.type == 'income',
            func.extract('year', Transaction.date) == current_year,
            func.extract('month', Transaction.date) == month
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0
        
        month_expense = q.filter(
            Transaction.type == 'expense',
            func.extract('year', Transaction.date) == current_year,
            func.extract('month', Transaction.date) == month
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0
        
        monthly_stats.append({
            'month': month,
            'income': month_income,
            'expense': month_expense,
            'balance': month_income - month_expense
        })
    
    # Статистика по категориям
    category_stats = {}
    for t in q.filter_by(type='expense').all():
        if t.category not in category_stats:
            category_stats[t.category] = {
                'total': 0,
                'count': 0,
                'avg': 0
            }
        category_stats[t.category]['total'] += t.amount
        category_stats[t.category]['count'] += 1
    
    for cat in category_stats:
        category_stats[cat]['avg'] = category_stats[cat]['total'] / category_stats[cat]['count']
    
    return render_template(
        "statistics.html",
        monthly_stats=monthly_stats,
        category_stats=category_stats,
        current_year=current_year
    )
=======
    return redirect(url_for("transactions.dashboard"))
>>>>>>> 86e1b5366313f5eb2c1c708d8c6a1d9e73968a3f
