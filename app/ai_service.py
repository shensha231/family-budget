import os
from openai import OpenAI
from datetime import datetime

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


def generate_smart_advice(user_data):
    """
    Генерирует персонализированные советы на основе полных данных пользователя
    """
    prompt = f"""
Ты — финансовый аналитик-консультант. Проанализируй следующие данные о семейном бюджете:

📊 ДОХОДЫ:
{user_data.get('income_summary', 'Нет данных')}

💸 РАСХОДЫ ПО КАТЕГОРИЯМ:
{user_data.get('expense_breakdown', 'Нет данных')}

💰 ОБЩАЯ ИНФОРМАЦИЯ:
- Общий доход: {user_data.get('total_income', 0)} ₽
- Общий расход: {user_data.get('total_expense', 0)} ₽
- Баланс: {user_data.get('balance', 0)} ₽

🎯 КРУПНЫЕ РАСХОДЫ (>10000 ₽):
{user_data.get('large_expenses', 'Нет крупных расходов')}

ЗАДАНИЕ:
1. Проанализируй структуру расходов и найди аномалии
2. Дай 3-5 КОНКРЕТНЫХ, ОРИГИНАЛЬНЫХ советов (не банальные "меньше тратьте")
3. Если есть категория "Рестораны/Еда вне дома" с большими тратами:
   - Посчитай процент от дохода
   - Предложи 2-3 вкусных домашних рецепта как альтернативу
   - Покажи экономию в цифрах
4. Предложи реалистичный план оптимизации на месяц

Ответ должен быть практичным, мотивирующим и с конкретными цифрами!
"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты опытный финансовый консультант, который дает практичные советы с юмором и конкретными примерами."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка генерации советов: {str(e)}"


def analyze_transaction(transaction_data):
    """
    Моментальный анализ одной транзакции при добавлении
    Возвращает совет сразу после добавления расхода
    """
    amount = transaction_data.get('amount', 0)
    category = transaction_data.get('category', '')
    user_income = transaction_data.get('user_monthly_income', 0)
    
    if amount == 0 or user_income == 0:
        return None
    
    percentage = (amount / user_income) * 100
    
    # Анализ только для крупных расходов (>5% от дохода)
    if percentage < 5:
        return None
        
    prompt = f"""
Пользователь только что потратил {amount} ₽ на категорию "{category}".
Его месячный доход: {user_income} ₽ (это {percentage:.1f}% от дохода).

Дай ОДИН короткий совет (2-3 предложения):
- Если это много — предложи конкретную альтернативу
- Если нормально — похвали и дай совет как сэкономить в этой категории

Будь дружелюбным и конкретным!
"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content
    except:
        return None


def simulate_budget_changes(current_data, changes):
    """
    Симулирует изменения бюджета с помощью GPT
    """
    # Рассчитываем новые показатели
    new_income = current_data['avg_monthly_income'] + changes.get('increase_income', 0)
    
    # Уменьшаем расходы в выбранной категории
    category = changes.get('reduce_category')
    reduce_percent = changes.get('reduce_percent', 0)
    
    new_expenses = current_data['avg_monthly_expense']
    reduction_amount = 0
    
    if category and category in current_data['expense_by_category']:
        category_expense = current_data['expense_by_category'][category]
        # Нормализуем категорийные расходы к месячным (делим на количество месяцев)
        months_count = current_data.get('months_count', 1)
        monthly_category_expense = category_expense / months_count
        reduction_amount = monthly_category_expense * (reduce_percent / 100)
        new_expenses -= reduction_amount
    
    new_balance = new_income - new_expenses
    months = changes.get('simulation_months', 6)
    projected_savings = new_balance * months
    
    # Текущий баланс (может быть отрицательным)
    current_balance = current_data.get('balance', 0)
    
    # Расчет процентного изменения
    savings_increase_percent = 0
    if current_balance != 0:
        savings_increase_percent = ((new_balance - current_balance) / abs(current_balance)) * 100
    elif new_balance > 0:
        savings_increase_percent = 100  # Было 0, стало положительное
    
    # Формируем информацию о категории для промпта
    category_info = f"{category}" if category else "не выбрана"
    reduction_info = f"{reduce_percent}%" if reduce_percent > 0 else "0%"
    
    # Детализация экономии
    if reduction_amount > 0 and category:
        monthly_saving = reduction_amount
        yearly_saving = monthly_saving * 12
        saving_details = f"💰 Экономия в категории «{category}»: {monthly_saving:.0f} ₽/мес ({yearly_saving:.0f} ₽/год)"
    else:
        saving_details = "📉 Сокращение расходов не запланировано"
    
    # GPT анализ
    prompt = f"""
Проанализируй финансовую симуляцию:

📊 ТЕКУЩЕЕ СОСТОЯНИЕ:
• Средний доход: {current_data['avg_monthly_income']:.0f} ₽/мес
• Средний расход: {current_data['avg_monthly_expense']:.0f} ₽/мес
• Текущий баланс: {current_balance:.0f} ₽

🔄 ПЛАНИРУЕМЫЕ ИЗМЕНЕНИЯ:
• Увеличение дохода: +{changes.get('increase_income', 0):.0f} ₽
• Сокращение расходов в категории «{category_info}»: -{reduction_info}
• Период симуляции: {months} месяцев

{saving_details}

📈 ПРОГНОЗ:
• Новый доход: {new_income:.0f} ₽/мес
• Новый расход: {new_expenses:.0f} ₽/мес  
• Новый баланс: {new_balance:.0f} ₽/мес
• Накопления за {months} мес: {projected_savings:.0f} ₽
• Изменение баланса: {savings_increase_percent:+.1f}%

🎯 ЗАДАНИЕ:
1. ОЦЕНКА РЕАЛИСТИЧНОСТИ: Поставь оценку от 1 до 10 и объясни почему
2. КОНКРЕТНЫЕ ШАГИ: Дай 3-4 практических совета для достижения этой цели
3. АЛЬТЕРНАТИВЫ: Предложи 2 других способа увеличить накопления
4. РИСКИ: Укажи возможные препятствия и как их избежать
5. МОТИВАЦИЯ: Напиши короткое вдохновляющее резюме

Ответ оформи красиво, используй эмодзи и четкую структуру.
Будь практичным, как опытный financial advisor!
"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Ты финансовый советник с 15-летним опытом. Помогаешь людям достигать финансовых целей. Даешь только конкретные, выполнимые советы с цифрами. Используешь эмодзи для наглядности."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        gpt_advice = response.choices[0].message.content
    except Exception as e:
        gpt_advice = "🤖 Не удалось получить AI-анализ. Попробуйте позже или проверьте API-ключ."
    
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
    """
    Комплексный анализ финансового здоровья пользователя
    """
    prompt = f"""
Проведи комплексный анализ финансового здоровья на основе данных:

Доходы: {user_data.get('total_income', 0)} ₽
Расходы: {user_data.get('total_expense', 0)} ₽
Сбережения: {user_data.get('savings', 0)} ₽

Оцени:
1. Коэффициент финансовой независимости
2. Рекомендации по "подушке безопасности"
3. Потенциал для инвестиций
4. 3 главные цели на ближайший год
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except:
        return "Анализ временно недоступен"