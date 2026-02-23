import os
from datetime import datetime
from huggingface_hub import InferenceClient
import re

API_TOKEN = os.getenv('HF_TOKEN', '')

if not API_TOKEN:
    print("WARNING: HF_TOKEN not set!")

client = InferenceClient(
    provider="hf-inference",
    api_key=API_TOKEN,
)

MODEL_ID = "HuggingFaceTB/SmolLM3-3B"

print(f"HuggingFace connected: {API_TOKEN[:10]}...")


def clean_html_text(text):
    """Remove HTML tags and decode HTML entities from text"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    return text.strip()

def generate_smart_advice(user_data):
    if not API_TOKEN:
        return "AI советы временно недоступны: HF_TOKEN не настроен"

    prompt = f"""
Ты — финансовый аналитик-консультант. Проанализируй данные о семейном бюджете:

📊 ДОХОДЫ:
{user_data.get('income_summary', 'Нет данных')}

💸 РАСХОДЫ ПО КАТЕГОРИЯМ:
{user_data.get('expense_breakdown', 'Нет данных')}

💰 ОБЩАЯ ИНФОРМАЦИЯ:
- Общий доход: {user_data.get('total_income', 0)} руб
- Общий расход: {user_data.get('total_expense', 0)} руб
- Баланс: {user_data.get('balance', 0)} руб

🎯 КРУПНЫЕ РАСХОДЫ (>10000 руб):
{user_data.get('large_expenses', 'Нет крупных расходов')}

ЗАДАНИЕ:
1. Проанализируй структуру расходов и найди аномалии
2. Дай 3-5 конкретных оригинальных советов
3. Предложи реалистичный план оптимизации на месяц
Отвечай по-русски, с эмодзи и конкретными цифрами.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "Ты опытный финансовый консультант. Отвечаешь по-русски с эмодзи."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.8,
        )
        return clean_html_text(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in generate_smart_advice: {e}")
        return f"Ошибка генерации советов: {e}"


def analyze_transaction(transaction_data):
    if not API_TOKEN:
        return None

    try:
        amount = float(transaction_data.get('amount', 0))
        category = transaction_data.get('category', '')
        user_income = float(transaction_data.get('user_monthly_income', 0))

        if amount == 0 or user_income == 0:
            return None

        percentage = (amount / user_income) * 100

        if percentage < 5:
            return None

        prompt = f"""
Пользователь потратил {amount:.0f} руб на категорию "{category}".
Месячный доход: {user_income:.0f} руб (это {percentage:.1f}% от дохода).
Дай ОДИН короткий совет (2-3 предложения) по-русски:
- Если много - предложи альтернативу
- Если нормально - похвали и дай совет как сэкономить
"""

        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in analyze_transaction: {e}")
        return None


def simulate_budget_changes(current_data, changes):
    gpt_advice = ""
    new_income = 0
    new_expenses = 0
    new_balance = 0
    projected_savings = 0
    current_balance = 0
    savings_increase_percent = 0
    reduction_amount = 0
    category = None
    reduce_percent = 0
    months = 6

    if not API_TOKEN:
        gpt_advice = "AI анализ недоступен: HF_TOKEN не настроен"
    else:
        try:
            new_income = float(current_data['avg_monthly_income']) + float(changes.get('increase_income', 0))
            category = changes.get('reduce_category')
            reduce_percent = float(changes.get('reduce_percent', 0))
            new_expenses = float(current_data['avg_monthly_expense'])
            reduction_amount = 0

            if category and category in current_data['expense_by_category']:
                category_expense = float(current_data['expense_by_category'][category])
                months_count = float(current_data.get('months_count', 1))
                monthly_category_expense = category_expense / months_count
                reduction_amount = monthly_category_expense * (reduce_percent / 100)
                new_expenses -= reduction_amount

            new_balance = new_income - new_expenses
            months = int(changes.get('simulation_months', 6))
            projected_savings = new_balance * months
            current_balance = float(current_data.get('balance', 0))

            if current_balance != 0:
                savings_increase_percent = ((new_balance - current_balance) / abs(current_balance)) * 100
            elif new_balance > 0:
                savings_increase_percent = 100

            prompt = f"""
Проанализируй финансовую симуляцию и ответь по-русски:

ТЕКУЩЕЕ СОСТОЯНИЕ:
- Доход: {current_data['avg_monthly_income']:.0f} руб/мес
- Расход: {current_data['avg_monthly_expense']:.0f} руб/мес
- Баланс: {current_balance:.0f} руб

ПРОГНОЗ после изменений:
- Новый доход: {new_income:.0f} руб/мес
- Новый расход: {new_expenses:.0f} руб/мес
- Новый баланс: {new_balance:.0f} руб/мес
- Накопления за {months} мес: {projected_savings:.0f} руб

Дай оценку реалистичности (1-10), 3 конкретных совета и мотивацию.
"""

            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": "Ты финансовый советник. Отвечаешь по-русски с эмодзи."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1500,
                temperature=0.7,
            )
            gpt_advice = response.choices[0].message.content

        except Exception as e:
            print(f"Error in simulate_budget_changes: {e}")
            gpt_advice = "Не удалось получить AI-анализ. Попробуйте позже."

    return {
        'current_income': current_data['avg_monthly_income'],
        'current_expense': current_data['avg_monthly_expense'],
        'current_balance': current_balance,
        'new_income': new_income,
        'new_expense': new_expenses,
        'new_balance': new_balance,
        'projected_savings': projected_savings,
        'months': months,
        'gpt_advice': gpt_advice,
        'savings_increase_percent': savings_increase_percent,
        'reduction_amount': reduction_amount,
        'reduction_category': category,
        'reduction_percent': reduce_percent
    }


def analyze_financial_health(user_data):
    if not API_TOKEN:
        return "Анализ недоступен: HF_TOKEN не настроен"

    try:
        prompt = f"""
Проведи анализ финансового здоровья по-русски:

Доходы: {float(user_data.get('total_income', 0)):.0f} руб
Расходы: {float(user_data.get('total_expense', 0)):.0f} руб
Сбережения: {float(user_data.get('savings', 0)):.0f} руб

Оцени:
1. Коэффициент финансовой независимости
2. Рекомендации по подушке безопасности
3. Потенциал для инвестиций
4. 3 главные цели на год
"""

        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in analyze_financial_health: {e}")
        return "Анализ временно недоступен"
