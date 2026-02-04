from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User
from . import db
import re
from functools import wraps
from datetime import datetime, timedelta

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Хранилище попыток входа (в production лучше использовать Redis)
login_attempts = {}

def validate_email(email):
    """Проверяет корректность email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Проверяет пароль на соответствие требованиям:
    - Минимум 8 символов
    - Минимум 1 заглавная буква (A-Z)
    - Минимум 1 строчная буква (a-z)
    - Минимум 1 цифра (0-9)
    - Минимум 1 спецсимвол (!@#$%^&*()_+-=[]{}|;:,.<>?)
    """
    if len(password) < 8:
        return False, "Пароль должен содержать минимум 8 символов"
    
    if not re.search(r'[A-Z]', password):
        return False, "Пароль должен содержать минимум 1 заглавную букву"
    
    if not re.search(r'[a-z]', password):
        return False, "Пароль должен содержать минимум 1 строчную букву"
    
    if not re.search(r'\d', password):
        return False, "Пароль должен содержать минимум 1 цифру"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, "Пароль должен содержать минимум 1 спецсимвол (!@#$%^&* и т.д.)"
    
    return True, "Пароль соответствует требованиям"

def rate_limit(max_attempts=5, window_minutes=15):
    """Decorator для ограничения попыток входа"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            now = datetime.now()
            
            if ip in login_attempts:
                attempts, first_attempt = login_attempts[ip]
                
                # Если прошло больше window_minutes минут, сбрасываем счётчик
                if now - first_attempt > timedelta(minutes=window_minutes):
                    login_attempts[ip] = (1, now)
                elif attempts >= max_attempts:
                    flash(f"Слишком много попыток входа. Попробуйте через {window_minutes} минут", "error")
                    return render_template("auth/login.html"), 429
                else:
                    login_attempts[ip] = (attempts + 1, first_attempt)
            else:
                login_attempts[ip] = (1, now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
@auth_bp.route("/login", methods=["GET", "POST"])
@rate_limit(max_attempts=5, window_minutes=15)
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        # Валидация email
        if not email:
            flash("Введите email", "error")
            return render_template("auth/login.html")
        
        if not validate_email(email):
            flash("Неверный формат email", "error")
            return render_template("auth/login.html")
        
        # Валидация пароля
        if not password:
            flash("Введите пароль", "error")
            return render_template("auth/login.html")
        
        # Поиск пользователя
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            # Сбрасываем счётчик попыток при успешном входе
            if request.remote_addr in login_attempts:
                del login_attempts[request.remote_addr]
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for("transactions.dashboard"))
        
        flash("Неверный email или пароль", "error")
        return render_template("auth/login.html")
    
    return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        name = request.form.get("name", "").strip()
        
        # Валидация имени
        if not name:
            flash("Введите имя", "error")
            return render_template("auth/register.html")
        
        if len(name) < 2:
            flash("Имя должно содержать минимум 2 символа", "error")
            return render_template("auth/register.html")
        
        # Валидация email
        if not email:
            flash("Введите email", "error")
            return render_template("auth/register.html")
        
        if not validate_email(email):
            flash("Неверный формат email", "error")
            return render_template("auth/register.html")
        
        # Проверка существования пользователя
        if User.query.filter_by(email=email).first():
            flash("Пользователь с таким email уже существует", "error")
            return render_template("auth/register.html")
        
        # Валидация пароля
        if not password:
            flash("Введите пароль", "error")
            return render_template("auth/register.html")
        
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message, "error")
            return render_template("auth/register.html")
        
        # Проверка совпадения паролей
        if password != confirm_password:
            flash("Пароли не совпадают", "error")
            return render_template("auth/register.html")
        
        # Создание пользователя
        user = User(
            email=email,
            name=name,
            password_hash=generate_password_hash(password)
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Регистрация прошла успешно!", "success")
            return redirect(url_for("transactions.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash("Ошибка при регистрации. Попробуйте позже", "error")
            return render_template("auth/register.html")
    
    return render_template("auth/register.html")
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы успешно вышли из системы", "success")
    return redirect(url_for("index"))

# API для проверки пароля в реальном времени
@auth_bp.route("/api/check-password", methods=["POST"])
def check_password_strength():
    """API endpoint для проверки силы пароля"""
    password = request.json.get("password", "")
    
    if not password:
        return jsonify({"valid": False, "strength": 0, "message": "Введите пароль"})
    
    is_valid, message = validate_password(password)
    
    # Вычисляем силу пароля (0-100)
    strength = 0
    if len(password) >= 8:
        strength += 25
    if len(password) >= 12:
        strength += 10
    if re.search(r'[A-Z]', password):
        strength += 15
    if re.search(r'[a-z]', password):
        strength += 15
    if re.search(r'\d', password):
        strength += 15
    if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        strength += 20
    
    strength_label = "Слабый"
    if strength >= 70:
        strength_label = "Сильный"
    elif strength >= 50:
        strength_label = "Средний"
    
    return jsonify({
        "valid": is_valid,
        "strength": strength,
        "strength_label": strength_label,
        "message": message
    })
