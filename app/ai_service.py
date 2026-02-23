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
    """Extract plain text from HTML content"""
    # Remove script and style elements
    text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    text = text.replace('&quot;', '"').replace('&apos;', "'")
    text = text.replace('&nbsp;', ' ')
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def generate_smart_advice(user_data):
    if not API_TOKEN:
        return "AI советы временно недоступны: HF_TOKEN не настроен"

    prompt = f"""
Ты - финансовый аналитик-консультант. Проанализируй данные о семейном бюджете:

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
        return f"❌ Ошибка AI: {str(e)[:200]}. Проверьте HF_TOKEN в .env файле и убедитесь что он валидный."

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

        prompt = f"""Пользователь потратил {amount:.0f} руб на категорию "{category}".
Месячный доход: {user_income:.0f} руб (это {percentage:.1f}% от дохода).

Дай ОДИН короткий совет (2-3 предложения) по-русски:"""

        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
        )

        return clean_html_text(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in analyze_transaction: {e}")
        return None
