from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from .models import Transaction

analysis_bp = Blueprint("analysis", __name__, url_prefix="/analysis")


@analysis_bp.route("/smart")
@login_required
def smart():
    # семейный или личный контекст
    if current_user.family_id:
        q = Transaction.query.filter_by(family_id=current_user.family_id)
    else:
        q = Transaction.query.filter_by(user_id=current_user.id)

    # агрегируем по типу и категории
    rows = (
        q.with_entities(
            Transaction.type,
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
        )
        .group_by(Transaction.type, Transaction.category)
        .all()
    )

    insights = []
    for ttype, cat, total in rows:
        if ttype == "expense":
            insights.append(f"Расходы на «{cat}»: {total:.2f} ₽.")
        else:
            insights.append(f"Доходы из источника «{cat}»: {total:.2f} ₽.")

    return render_template("analysis/smart.html", rows=rows, insights=insights)


@analysis_bp.route("/stats")
@login_required
def stats():
    # семейный или личный контекст
    if current_user.family_id:
        q = Transaction.query.filter_by(family_id=current_user.family_id)
    else:
        q = Transaction.query.filter_by(user_id=current_user.id)

    # статистика только по расходам
    rows = (
        q.filter_by(type="expense")
         .with_entities(
             Transaction.category,
             func.count(Transaction.id).label("n"),
             func.avg(Transaction.amount).label("avg"),
             func.min(Transaction.amount).label("min"),
             func.max(Transaction.amount).label("max"),
             func.sum(Transaction.amount).label("total"),
         )
         .group_by(Transaction.category)
         .all()
    )

    return render_template("analysis/stats.html", rows=rows)


# ---------- МЕНЮ СИМУЛЯТОРА ----------

@analysis_bp.route("/simulator")
@login_required
def simulator_menu():
    # просто страница-меню с выбором формул
    return render_template("analysis/sim_menu.html")


# ---------- GPT БЮДЖЕТНЫЙ СИМУЛЯТОР ----------

@analysis_bp.route('/simulator/gpt', methods=['GET', 'POST'])
@login_required
def simulator_gpt():
    """Интерактивный симулятор бюджета с GPT"""
    from app.ai_service import simulate_budget_changes
    
    if request.method == 'POST':
        # Получаем данные из формы
        changes = {
            'reduce_category': request.form.get('category'),
            'reduce_percent': float(request.form.get('reduce_percent', 0)),
            'increase_income': float(request.form.get('increase_income', 0)),
            'new_expense': request.form.get('new_expense'),
            'simulation_months': int(request.form.get('months', 6))
        }
        
        # Получаем текущие данные пользователя
        current_data = get_user_financial_data(current_user.id)
        
        # GPT анализирует изменения
        simulation_result = simulate_budget_changes(current_data, changes)
        
        # Получаем категории для отображения формы после POST
        categories = get_expense_categories(current_user.id)
        current_stats = get_current_month_stats(current_user.id)
        
        return render_template('analysis/simulator_gpt.html', 
                             result=simulation_result,
                             changes=changes,
                             categories=categories,
                             stats=current_stats)
    
    # GET - показываем форму
    categories = get_expense_categories(current_user.id)
    current_stats = get_current_month_stats(current_user.id)
    
    return render_template('analysis/simulator_gpt.html', 
                         categories=categories,
                         stats=current_stats,
                         result=None,
                         changes=None)


def get_user_financial_data(user_id):
    """Получает полные финансовые данные пользователя"""
    # Доходы и расходы за последние 3 месяца
    three_months_ago = datetime.utcnow() - timedelta(days=90)
    
    # Учитываем семейный контекст
    if current_user.family_id:
        q = Transaction.query.filter_by(family_id=current_user.family_id)
    else:
        q = Transaction.query.filter_by(user_id=user_id)
    
    transactions = q.filter(
        Transaction.date >= three_months_ago
    ).all()
    
    income_total = sum(t.amount for t in transactions if t.type == 'income')
    expense_total = sum(t.amount for t in transactions if t.type == 'expense')
    
    # Группировка расходов по категориям
    expense_by_category = {}
    for t in transactions:
        if t.type == 'expense':
            if t.category not in expense_by_category:
                expense_by_category[t.category] = 0
            expense_by_category[t.category] += t.amount
    
    # Безопасное деление
    months_set = set()
    for t in transactions:
        months_set.add(t.date.strftime('%Y-%m'))
    months_count = max(1, len(months_set) or 1)
    
    return {
        'total_income': income_total,
        'total_expense': expense_total,
        'balance': income_total - expense_total,
        'expense_by_category': expense_by_category,
        'avg_monthly_income': income_total / months_count,
        'avg_monthly_expense': expense_total / months_count,
        'months_count': months_count
    }


def get_expense_categories(user_id):
    """Получает список категорий расходов пользователя"""
    if current_user.family_id:
        q = Transaction.query.filter_by(family_id=current_user.family_id, type='expense')
    else:
        q = Transaction.query.filter_by(user_id=user_id, type='expense')
    
    categories = q.with_entities(Transaction.category).distinct().all()
    return [c[0] for c in categories]


def get_current_month_stats(user_id):
    """Получает статистику за текущий месяц"""
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    if current_user.family_id:
        q = Transaction.query.filter_by(family_id=current_user.family_id)
    else:
        q = Transaction.query.filter_by(user_id=user_id)
    
    transactions = q.filter(Transaction.date >= month_start).all()
    
    income = sum(t.amount for t in transactions if t.type == 'income')
    expense = sum(t.amount for t in transactions if t.type == 'expense')
    
    return {
        'income': income,
        'expense': expense,
        'balance': income - expense
    }


# ---------- ВКЛАД: ПРОСТЫЕ / СЛОЖНЫЕ ПРОЦЕНТЫ ----------

@analysis_bp.route("/sim/deposit", methods=["GET", "POST"])
@login_required
def sim_deposit():
    result = None

    if request.method == "POST":
        principal = float(request.form["principal"])
        rate = float(request.form["rate"]) / 100.0
        years = float(request.form["years"])
        kind = request.form.get("interest_kind")          # simple / compound
        m = int(request.form.get("periods_per_year", 1))  # начислений в год

        if kind == "simple":
            # Простые проценты: Cn = C0 * (1 + n * i)
            future_value = principal * (1 + years * rate)
        else:
            # Сложные проценты: Cn = C0 * (1 + i/m)^(m*n)
            i_per = rate / m
            n = m * years
            future_value = principal * (1 + i_per) ** n

        result = {
            "principal": principal,
            "rate": rate * 100,
            "years": years,
            "kind": kind,
            "periods_per_year": m,
            "future_value": future_value,
        }

    return render_template("analysis/sim_deposit.html", result=result)


# ---------- ЭКВИВАЛЕНТНАЯ ГОДОВАЯ СТАВКА ----------

@analysis_bp.route("/sim/equivalent", methods=["GET", "POST"])
@login_required
def sim_equivalent():
    result = None

    if request.method == "POST":
        rate_nominal = float(request.form["rate_nominal"]) / 100.0
        m = int(request.form.get("m", 1))
        if m > 0:
            # Эквивалентная (эффективная) годовая ставка: (1 + i/m)^m - 1
            eq_rate = (1 + rate_nominal / m) ** m - 1
        else:
            eq_rate = rate_nominal

        result = {
            "rate_nominal": rate_nominal * 100,
            "m": m,
            "eq_rate": eq_rate * 100,
        }

    return render_template("analysis/sim_equivalent.html", result=result)


# ---------- РЕАЛЬНАЯ СТАВКА ----------

@analysis_bp.route("/sim/real", methods=["GET", "POST"])
@login_required
def sim_real():
    result = None

    if request.method == "POST":
        rate_nominal = float(request.form["rate_nominal"]) / 100.0
        inflation = float(request.form["inflation"]) / 100.0
        # Реальная ставка = номинальная - инфляция (упрощённо)
        real_rate = rate_nominal - inflation

        result = {
            "rate_nominal": rate_nominal * 100,
            "inflation": inflation * 100,
            "real_rate": real_rate * 100,
        }

    return render_template("analysis/sim_real.html", result=result)


# ---------- КРЕДИТ (АННУИТЕТНЫЙ ПЛАТЁЖ) ----------

@analysis_bp.route("/sim/loan", methods=["GET", "POST"])
@login_required
def sim_loan():
    result = None

    if request.method == "POST":
        principal = float(request.form["principal"])
        rate = float(request.form["rate"]) / 100.0
        years = float(request.form["years"])
        n = int(years * 12)           # месяцев
        monthly_rate = rate / 12.0

        if monthly_rate > 0 and n > 0:
            # a = C0 * i * (1 + i)^n / ((1 + i)^n - 1)
            k = (1 + monthly_rate) ** n
            payment = principal * monthly_rate * k / (k - 1)
            total_paid = payment * n
            overpay = total_paid - principal
        else:
            payment = total_paid = overpay = 0

        result = {
            "principal": principal,
            "rate": rate * 100,
            "years": years,
            "payment": payment,
            "total_paid": total_paid,
            "overpay": overpay,
        }

    return render_template("analysis/sim_loan.html", result=result)


# ---------- АНАЛИЗ ИНВЕСТИЦИОННОГО ПРОЕКТА ----------

@analysis_bp.route("/project", methods=["GET", "POST"])
@login_required
def project():
    result = None
    flows_text = ""
    if request.method == "POST":
        try:
            initial = float(request.form["initial"])          # a0 (обычно отрицательное)
            rate = float(request.form["discount_rate"]) / 100.0
            flows_text = request.form["flows"].strip()
            mode = request.form.get("mode", "manual")         # manual / geometric

            cash_flows = []

            if mode == "manual":
                # пользователь вводит через запятую: 10000, 15000, 20000
                if flows_text:
                    for part in flows_text.split(","):
                        val = float(part.strip())
                        cash_flows.append(val)
            else:
                # геометрическая прогрессия: первый поток, коэффициент роста, число лет
                first = float(request.form["geo_first"])
                growth = float(request.form["geo_growth"]) / 100.0   # % роста в год
                years = int(request.form["geo_years"])
                val = first
                for _ in range(years):
                    cash_flows.append(val)
                    val *= (1 + growth)

            # 1) NPV (ЧДД)
            npv = -initial
            for t, cf in enumerate(cash_flows, start=1):
                npv += cf / ((1 + rate) ** t)

            # 2) ROI = прибыль / вложенный капитал
            total_in = initial
            total_out = sum(cash_flows)
            profit = total_out - total_in
            roi = (profit / total_in * 100) if total_in != 0 else None

            # 3) IRR – численный поиск ставки, при которой NPV = 0
            irr = None
            def npv_at(r):
                v = -initial
                for t, cf in enumerate(cash_flows, start=1):
                    v += cf / ((1 + r) ** t)
                return v

            # простой поиск по сетке ставок от -0.9 до 1.0 (от -90% до 100%)
            best_r = None
            best_abs = None
            for r in [x / 1000.0 for x in range(-900, 1001)]:  # шаг 0.1%
                val = npv_at(r)
                if best_abs is None or abs(val) < best_abs:
                    best_abs = abs(val)
                    best_r = r
            irr = best_r * 100 if best_r is not None else None

            # 4) ЭДС = B − i · C
            # здесь B — суммарная прибыль, C — вложенный капитал, i — ставка дисконтирования
            eds = profit - rate * initial

            result = {
                "initial": initial,
                "rate": rate * 100,
                "cash_flows": cash_flows,
                "npv": npv,
                "roi": roi,
                "irr": irr,
                "eds": eds,
                "mode": mode,
            }
        except ValueError:
            result = None

    return render_template("analysis/project.html", result=result, flows_text=flows_text)


# ---------- ЭКОНОМИЧЕСКИЕ ФОРМУЛЫ (СРЕДНИЕ/ПРЕДЕЛЬНЫЕ ИЗДЕРЖКИ, ЭЛАСТИЧНОСТЬ) ----------

@analysis_bp.route("/costs", methods=["GET", "POST"])
@login_required
def costs():
    result = {
        "ac": None,
        "mc": None,
        "mr": None,
        "elasticity": None,
        "tot": None,
        "fisher": None,
    }

    if request.method == "POST":
        action = request.form.get("action")

        # 1) Средние издержки: AC = TC / Q
        if action == "ac":
            tc = float(request.form["tc"])
            q = float(request.form["q"])
            ac = tc / q if q != 0 else None
            result["ac"] = {
                "tc": tc,
                "q": q,
                "ac": ac,
            }

        # 2) Предельные издержки: MC = ΔC / ΔQ
        elif action == "mc":
            c1 = float(request.form["c1"])
            c2 = float(request.form["c2"])
            q1 = float(request.form["q1"])
            q2 = float(request.form["q2"])
            delta_c = c2 - c1
            delta_q = q2 - q1
            mc = delta_c / delta_q if delta_q != 0 else None
            result["mc"] = {
                "c1": c1,
                "c2": c2,
                "q1": q1,
                "q2": q2,
                "delta_c": delta_c,
                "delta_q": delta_q,
                "mc": mc,
            }

        # 3) Предельный доход: MR = ΔB / ΔQ
        elif action == "mr":
            b1 = float(request.form["b1"])
            b2 = float(request.form["b2"])
            q1 = float(request.form["q1_mr"])
            q2 = float(request.form["q2_mr"])
            delta_b = b2 - b1
            delta_q = q2 - q1
            mr = delta_b / delta_q if delta_q != 0 else None
            result["mr"] = {
                "b1": b1,
                "b2": b2,
                "q1": q1,
                "q2": q2,
                "delta_b": delta_b,
                "delta_q": delta_q,
                "mr": mr,
            }

        # 4) Эластичность спроса: E = (Δq / q) / (Δp / p)
        elif action == "elasticity":
            q1 = float(request.form["q1_el"])
            q2 = float(request.form["q2_el"])
            p1 = float(request.form["p1_el"])
            p2 = float(request.form["p2_el"])
            delta_q = q2 - q1
            delta_p = p2 - p1
            avg_q = (q1 + q2) / 2.0
            avg_p = (p1 + p2) / 2.0
            if avg_q != 0 and avg_p != 0 and delta_p != 0:
                e = (delta_q / avg_q) / (delta_p / avg_p)
            else:
                e = None
            result["elasticity"] = {
                "q1": q1,
                "q2": q2,
                "p1": p1,
                "p2": p2,
                "elasticity": e,
            }

        # 5) Условия торговли: ToT = P_export / P_import
        elif action == "tot":
            p_exp = float(request.form["p_exp"])
            p_imp = float(request.form["p_imp"])
            tot = p_exp / p_imp if p_imp != 0 else None
            result["tot"] = {
                "p_exp": p_exp,
                "p_imp": p_imp,
                "tot": tot,
            }

        # 6) Уравнение Фишера: M * V = P * Q
        elif action == "fisher":
            m = float(request.form.get("m") or 0)
            v = float(request.form.get("v") or 0)
            p = float(request.form.get("p") or 0)
            q = float(request.form.get("q_f") or 0)
            unknown = request.form.get("unknown")  # M / V / P / Q

            mv = m * v
            pq = p * q

            m_res = m
            v_res = v
            p_res = p
            q_res = q

            if unknown == "M":
                m_res = pq / v if v != 0 else None
            elif unknown == "V":
                v_res = pq / m if m != 0 else None
            elif unknown == "P":
                p_res = mv / q if q != 0 else None
            elif unknown == "Q":
                q_res = mv / p if p != 0 else None

            result["fisher"] = {
                "m": m_res,
                "v": v_res,
                "p": p_res,
                "q": q_res,
            }

    return render_template("analysis/costs.html", result=result)