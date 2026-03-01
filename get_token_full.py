import requests
import base64
import uuid  # Для уникального RqUID
from urllib.parse import urlencode

# ТВОИ НОВЫЕ ДАННЫЕ
auth_key = "MDE5Y2E4ZTQtNzQxYi03MDFjLTk0N2QtNWM1NzM5ZjA5NjQyOjFjMDMyYzEwLTAzYTEtNDJlNS05MTQ1LTliYzJkYTdmMzFlYg=="

# УНИКАЛЬНЫЙ RqUID
rq_uid = str(uuid.uuid4())

url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'

headers = {
    'Authorization': f'Basic {auth_key}',
    'Content-Type': 'application/x-www-form-urlencoded',
    'RqUID': rq_uid,
    'Accept': 'application/json'
}

# URLENCODE data (важно!)
data = urlencode({
    'scope': 'GIGACHAT_API_PERS',
    'grant_type': 'client_credentials'
})

print(f"RqUID: {rq_uid}")
print("Отправляем запрос...")

response = requests.post(url, headers=headers, data=data, verify=False)

print(f"Статус: {response.status_code}")
print(f"Ответ: {response.text}")

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data['access_token']
    print(f"\n✅ ТОКЕН ПОЛУЧЕН!")
    print(f"access_token: {access_token}")
    print(f"expires_at: {token_data.get('expires_at', 'Не указан')}")
    
    # ТЕСТ ЧАТА
    print("\n--- ТЕСТ ЧАТА ---")
    chat_headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'RqUID': str(uuid.uuid4())
    }
    chat_data = {
        "model": "GigaChat2Lite",
        "messages": [{"role": "user", "content": "GigaChat готов для family_budget!"}]
    }
    
    chat_response = requests.post(
        'https://gigachat.devices.sberbank.ru/api/v1/chat/completions',
        headers=chat_headers,
        json=chat_data,
        verify=False
    )
    
    if chat_response.status_code == 200:
        print("✅ ЧАТ РАБОТАЕТ!")
        print(chat_response.json()['choices'][0]['message']['content'])
    else:
        print(f"Чат ошибка: {chat_response.status_code} {chat_response.text}")
else:
    print("❌ OAuth не сработал. Новый ключ нужен?")
