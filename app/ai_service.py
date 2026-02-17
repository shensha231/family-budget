import os
import random
from datetime import datetime

# Загружаем токен из переменной окружения
API_TOKEN = os.getenv('HF_TOKEN', '')
USE_AI = os.getenv('USE_AI', 'false').lower() == 'true'  # Флаг для включения/отключения AI

# Инициализируем клиент только если AI включен и есть токен
client = None
if USE_AI and API_TOKEN:
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=API_TOKEN,
            base_url="https://api-inference.huggingface.co/v1/"
        )
        print(f"✅ AI подключен: {API_TOKEN[:10]}...")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации AI: {e}")
        client = None
else:
    print("ℹ️ AI режим отключен (USE_AI=false или отсутствует токен)")

# Шаблоны для fallback-ответов (без использования AI)
FALLBACK_ADVICE_TEMPLATES = [
    "📊 Проанализировав ваш бюджет, рекомендую обратить внимание на категорию расходов, которая занимает более 30% от дохода. Попробуйте оптимизировать её, сократив на 10-15% в следующем месяце.",
    "💰 Отличная стратегия накоплений - правило 50/30/20: 50% на necessities, 30% на wants, 20% на savings. Как ваш текущий баланс соотносится с этим правилом?",
    "🎯 Совет месяца: поставьте конкретную финансовую цель на 3 месяца вперед. Например, накопить 10% от дохода на отпуск или подушку безопасности."
]

def generate_fallback_advice():
    return random.choice(FALLBACK_ADVICE_TEMPLATES)

def generate_smart_advice(user_data):
    if not client or not USE_AI:
        return generate_fallback_advice()
    
    # AI код здесь...
    return generate_fallback_advice()
