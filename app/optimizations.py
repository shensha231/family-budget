from flask import request
from flask_compress import Compress
from htmlmin import minify

def init_optimizations(app):
    """Инициализирует все оптимизации для Flask приложения"""
    
    # 1. Gzip/Brotli сжатие всех ответов
    Compress(app)
    
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html',
        'text/css',
        'text/xml',
        'application/json',
        'application/javascript',
        'image/svg+xml'
    ]
    app.config['COMPRESS_LEVEL'] = 6  # Уровень сжатия (1-9)
    app.config['COMPRESS_MIN_SIZE'] = 500  # Минимальный размер для сжатия
    
    # 2. Минификация HTML
    @app.after_request
    def response_minify(response):
        """Минифицирует HTML перед отправкой"""
        if response.content_type == 'text/html; charset=utf-8':
            try:
                response.set_data(
                    minify(
                        response.get_data(as_text=True),
                        remove_comments=True,
                        remove_empty_space=True
                    )
                )
            except Exception:
                pass  # Если ошибка минификации, отправляем оригинал
        return response
    
    # 3. Кэширование статических файлов
    @app.after_request
    def add_cache_headers(response):
        """Добавляет заголовки кэширования для статики"""
        if '/static/' in request.path:
            # Кэшировать на 1 год
            response.cache_control.max_age = 31536000
            response.cache_control.public = True
        return response
    
    print("✅ Оптимизации включены: Gzip/Brotli, HTML минификация, кэширование")
    return app
