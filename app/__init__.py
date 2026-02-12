from flask import Flask, render_template, redirect, url_for, request  # ← Добавлен request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    
    # Кэширование статических файлов
    @app.after_request
    def add_cache_headers(response):
        """Добавляет заголовки кэширования для статических файлов"""
        if '/static/' in request.path:
            # Кэшировать статику на 1 год
            response.cache_control.max_age = 31536000
            response.cache_control.public = True
        return response
    
    # Инициализация расширений
    db.init_app(app)
    Migrate(app, db)
    login_manager.init_app(app)

    # Импорт моделей, чтобы Alembic их видел
    from .models import User, Family, Transaction  # noqa

    # Blueprint'ы
    from .auth_routes import auth_bp
    from .family_routes import family_bp
    from .transaction_routes import transaction_bp
    from .analysis_routes import analysis_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(analysis_bp)

    # Flask-Login: функция загрузки пользователя
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Главная страница
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("transactions.dashboard"))
        return render_template("index.html")

    # Создание таблиц БД при первом запуске
    with app.app_context():
        db.create_all()
    
    return app