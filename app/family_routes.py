from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from .models import Family
from . import db

family_bp = Blueprint("family", __name__, url_prefix="/family")


@family_bp.route("/manage", methods=["GET", "POST"])
@login_required
def manage():
    family = None
    if current_user.family_id:
        family = Family.query.get(current_user.family_id)

    if request.method == "POST":
        name = request.form["name"].strip()

        if not name:
            flash("Название семьи не может быть пустым")
            return redirect(url_for("family.manage"))

        # есть семья -> переименовать
        if family:
            family.name = name
            if not family.invite_code:
                family.generate_invite_code()
        # нет семьи -> создать
        else:
            family = Family(name=name)
            family.generate_invite_code()
            db.session.add(family)
            db.session.flush()  # получаем id без отдельного commit
            current_user.family_id = family.id

        db.session.commit()
        flash("Семья сохранена")
        return redirect(url_for("transactions.dashboard"))

    return render_template("family/manage.html", family=family)


@family_bp.route("/join", methods=["GET", "POST"])
@login_required
def join():
    if request.method == "POST":
        code = request.form["invite_code"].strip().upper()
        if not code:
            flash("Введите код приглашения")
            return redirect(url_for("family.join"))

        family = Family.query.filter_by(invite_code=code).first()
        if not family:
            flash("Семья с таким кодом не найдена")
            return redirect(url_for("family.join"))

        current_user.family_id = family.id
        db.session.commit()
        flash(f"Вы присоединились к семье «{family.name}»")
        return redirect(url_for("transactions.dashboard"))

    return render_template("family/join.html")


@family_bp.route("/leave")
@login_required
def leave():
    if not current_user.family_id:
        flash("Вы и так не состоите в семье")
        return redirect(url_for("transactions.dashboard"))

    current_user.family_id = None
    db.session.commit()
    flash("Вы вышли из семьи")
    return redirect(url_for("transactions.dashboard"))
