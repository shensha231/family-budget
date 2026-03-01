import os
import requests
import uuid
import re
import warnings
import time
import threading
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

# Отключаем предупреждения о SSL
warnings.simplefilter('ignore', InsecureRequestWarning)

# ТВОИ ДАННЫЕ ИЗ ЛИЧНОГО КАБИНЕТА
CLIENT_ID = "019ca8e4-741b-701c-947d-5c5739f09642"
SCOPE = "GIGACHAT_API_PERS"
AUTH_KEY = "MDE5Y2E4ZTQtNzQxYi03MDFjLTk0N2QtNWM1NzM5ZjA5NjQyOjFjMDMyYzEwLTAzYTEtNDJlNS05MTQ1LTliYzJkYTdmMzFlYg=="

print(f"✅ Данные авторизации загружены")
print(f"📋 Client ID: {CLIENT_ID}")
print(f"📋 Scope: {SCOPE}")

# API endpoints
GIGACHAT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Кэш для access token
_access_token = None
_token_expires = 0
_token_lock = threading.Lock()

def refresh_token_periodically():
    """Фоновое обновление токена каждые 25 минут"""
    while True:
        try:
            # Обновляем токен
            new_token = get_new_token()
            if new_token:
                print(f"✅ Фоновое обновление токена успешно в {datetime.now().strftime('%H:%M:%S')}")
            # Ждем 25 минут (1500 секунд) - меньше чем время жизни токена
            time.sleep(1500)
        except Exception as e:
            print(f"❌ Ошибка фонового обновления: {e}")
            time.sleep(60)  # При ошибке ждем минуту и пробуем снова

def get_new_token():
    """Получение нового access token от GigaChat"""
    global _access_token, _token_expires
    
    try:
        rq_uid = str(uuid.uuid4())
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': rq_uid,
            'Authorization': f'Bearer {AUTH_KEY}'
        }
        
        payload = {
            'scope': SCOPE
        }
        
        print(f"🔄 Запрашиваю новый access token...")
        response = requests.post(
            GIGACHAT_AUTH_URL,
            headers=headers,
            data=payload,
            verify=False,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            _access_token = data.get('access_token')
            expires_at = data.get('expires_at', 0) / 1000  # конвертируем из миллисекунд
            _token_expires = expires_at - 60  # запас 60 секунд
            
            expires_time = datetime.fromtimestamp(expires_at)
            print(f"✅ Новый токен получен! Истекает: {expires_time.strftime('%H:%M:%S')}")
            return _access_token
        else:
            print(f"❌ Ошибка получения токена: {response.status_code}")
            print(f"❌ Ответ: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Исключение при получении токена: {e}")
        return None

def get_access_token():
    """Получение актуального access token (с автоматическим обновлением)"""
    global _access_token, _token_expires
    
    current_time = time.time()
    
    # Если токен есть и еще не истек (с запасом 60 секунд)
    with _token_lock:
        if _access_token and current_time < _token_expires:
            return _access_token
        
        # Иначе получаем новый токен
        print("🔄 Токен истек или отсутствует, получаем новый...")
        return get_new_token()


def clean_html_text(text):
    """Очистка текста от HTML"""
    if not text:
        return ""
    
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    text = text.replace('&quot;', '"').replace('&apos;', "'")
    text = text.replace('&nbsp;', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def gigachat_query(messages, model="GigaChat", max_tokens=2000, temperature=0.8):
    """Запрос к GigaChat API с автоматическим обновлением токена"""
    
    access_token = get_access_token()
    if not access_token:
        return "❌ Не удалось получить access token. Проверьте AUTH_KEY."
    
    rq_uid = str(uuid.uuid4())
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'RqUID': rq_uid
    }
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        print(f"🔄 Отправка запроса к GigaChat (модель: {model})...")
        response = requests.post(
            GIGACHAT_API_URL,
            headers=headers,
            json=data,
            verify=False,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return clean_html_text(result['choices'][0]['message']['content'])
        elif response.status_code == 401:
            # Токен истек - очищаем кэш и пробуем еще раз
            print("⚠️ Access token истек, пробуем обновить...")
            with _token_lock:
                _access_token = None
            return gigachat_query(messages, model, max_tokens, temperature)
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"❌ Текст: {response.text[:200]}")
            return f"❌ Ошибка GigaChat: {response.status_code}"
            
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return f"❌ Ошибка: {str(e)[:200]}"


def generate_smart_advice(user_data):
    """Генерация советов"""
    
    print(f"📊 Получены данные: {type(user_data)}")
    
    if isinstance(user_data, str):
        messages = [{"role": "user", "content": user_data}]
    elif isinstance(user_data, dict):
        income_summary = user_data.get('income_summary', 'Нет данных')
        expense_breakdown = user_data.get('expense_breakdown', 'Нет данных')
        total_income = user_data.get('total_income', 0)
        total_expense = user_data.get('total_expense', 0)
        balance = user_data.get('balance', 0)
        large_expenses = user_data.get('large_expenses', 'Нет крупных расходов')
        
        user_prompt = f"""Проанализируй семейный бюджет:

📊 ДОХОДЫ:
{income_summary}

💸 РАСХОДЫ:
{expense_breakdown}

💰 ИТОГО:
- Доход: {total_income} руб
- Расход: {total_expense} руб
- Баланс: {balance} руб

🎯 КРУПНЫЕ РАСХОДЫ:
{large_expenses}

Задание:
1. Найди аномалии в расходах
2. Дай 3-5 конкретных советов по оптимизации
3. Предложи план на месяц

Отвечай по-русски, с эмодзи и цифрами."""

        messages = [
            {"role": "system", "content": "Ты опытный финансовый консультант. Отвечаешь по-русски с эмодзи."},
            {"role": "user", "content": user_prompt}
        ]
    else:
        return "❌ Неверный формат данных"

    # Пробуем разные модели
    models_to_try = ["GigaChat", "GigaChat-Pro", "GigaChat-Plus"]
    
    for model in models_to_try:
        print(f"🔄 Пробуем модель: {model}")
        result = gigachat_query(messages, model=model, max_tokens=2000, temperature=0.8)
        if result and not result.startswith("❌"):
            return result
    
    return "❌ Не удалось получить ответ от GigaChat"


def analyze_transaction(transaction_data):
    """Анализ отдельной транзакции"""
    try:
        amount = float(transaction_data.get('amount', 0))
        category = transaction_data.get('category', '')
        user_income = float(transaction_data.get('user_monthly_income', 0))

        if amount == 0 or user_income == 0:
            return None

        percentage = (amount / user_income) * 100

        if percentage < 5:
            return None

        prompt = f"""Пользователь потратил {amount:.0f} руб на "{category}".
Доход: {user_income:.0f} руб (это {percentage:.1f}% от дохода).

Дай ОДИН короткий совет по этой трате (2-3 предложения):"""

        messages = [{"role": "user", "content": prompt}]
        
        result = gigachat_query(messages, model="GigaChat", max_tokens=150, temperature=0.7)
        return result
            
    except Exception as e:
        print(f"Error in analyze_transaction: {e}")
        return None


def simulate_budget_changes(current_data, changes):
    """Симуляция изменений в бюджете"""
    try:
        if isinstance(current_data, str):
            messages = [{"role": "user", "content": current_data}]
        else:
            expense_lines = []
            for cat, amount in current_data.get('expense_by_category', {}).items():
                expense_lines.append(f"- {cat}: {amount} руб")
            
            current_desc = f"""
ТЕКУЩИЙ БЮДЖЕТ:
- Доходы: {current_data.get('total_income', 0)} руб
- Расходы: {current_data.get('total_expense', 0)} руб
- Баланс: {current_data.get('balance', 0)} руб

Расходы по категориям:
{chr(10).join(expense_lines) if expense_lines else 'Нет расходов'}
"""

            changes_desc = "ПЛАНИРУЕМЫЕ ИЗМЕНЕНИЯ:\n"
            
            if changes.get('reduce_category') and changes.get('reduce_percent', 0) > 0:
                changes_desc += f"- Сократить '{changes['reduce_category']}' на {changes['reduce_percent']}%\n"
            
            if changes.get('increase_income', 0) > 0:
                changes_desc += f"- Увеличить доход на {changes['increase_income']} руб/мес\n"
            
            if changes.get('new_expense'):
                changes_desc += f"- Новый расход: {changes['new_expense']}\n"
            
            changes_desc += f"- Период: {changes.get('simulation_months', 6)} месяцев"

            user_prompt = f"""Проанализируй изменения в бюджете:

{current_desc}

{changes_desc}

Задание:
1. Рассчитай новый баланс через {changes.get('simulation_months', 6)} месяцев
2. Оцени эффект
3. Дай рекомендации
4. Предупреди о рисках

Ответь по-русски, с цифрами и эмодзи."""

            messages = [
                {"role": "system", "content": "Ты финансовый аналитик. Делаешь расчеты и даешь рекомендации."},
                {"role": "user", "content": user_prompt}
            ]
        
        result = gigachat_query(messages, model="GigaChat", max_tokens=1500, temperature=0.7)
        return result or "❌ Ошибка симулятора"
        
    except Exception as e:
        print(f"Error in simulate_budget_changes: {e}")
        return f"❌ Ошибка: {str(e)[:200]}"


# Запускаем фоновое обновление токена при импорте модуля
print("🚀 Запуск фонового обновления токена...")
refresh_thread = threading.Thread(target=refresh_token_periodically, daemon=True)
refresh_thread.start()
print("✅ Фоновое обновление токена запущено (каждые 25 минут)")