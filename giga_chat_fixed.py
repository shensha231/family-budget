import requests
import uuid

# ТВОЙ ТОКЕН ИЗ ЛОГА (скопируй полностью!)
ACCESS_TOKEN = "eyJjdHkiOiJqd3QiLCJlbmMiOiJBMjU2Q0JDLUhTNTEyIiwiYWxnIjoiUlNBLU9BRVAtMjU2In0.hF62WH6sxiiMeJOVQCt-FklY_X8acAUIZE2Ax6N425zwKFUZ9_k6kUVVCCDGUSJB2mOBCwKFsxkEmi4odnplmX0t7_bvrRyinedU0ZigBaAv2E5_nlGQnmPkSRAJrGUDpNYcLJxf2AKD1yGvCgeT7guMjealD8dzjZufjUJc8v2vTvR5JlUfOdR92V6ZRYZAn9lgM_2tL1F8b0h-GfbB7MbZtjjAY9zKLm2d2B2y9eFQZv8EM-IRRmq1AEDvSArwVeE1wyGjjB8Bgi0Ephjy9DDAUNh-7L1Jq7D_T16wZO5IsZMezIVZ5obIH0fyl-ieKi-fG2Kf6TcvnknpguwDNg.OUutdrpR8bJzjgFvwybrmg.X3AasMw07iSNx5r5grvlE8sImX1IsXwSGyVzFwmzbNcXJbXoOErgNOcWqYBGJtiLu8VZLrGSuMrhIu-5fPGQCN1gWUQW2m0nSf-r84hthxAV5bq2TyFuSe93dBtlbCVsujZptWOKmPVJTw48zcIvow8x3e2lFT4J7vm0G20XzOBaKdZpJNlnDswU5AEZYw-pHTgHwcF2Co6Mt_ioMbXfio0DfcQq5q3Pya-_Z_d-HDXYBG8kOed3SLJ_I0lWRYCavbLsh8j_MWYus2hukHY7cwNbuJuxIs0ZZGXjxywm2lyG563cwNOGFgE2BqauprrsW5Hm2JPvZCBCywvfwjc7j6Hxruy08GwA7NX3SfFZ_osFUeQkOyU8gwSQnOUzsQLJTr2sprH3w2Coby8LVqpDACvCT9wWCcNW-gllSWL26rAkSeeXNZXg8Wn8xcohWUcEPlhrpAAyvPHx7pNSERCb3icwRJWK2mhjf_wcbSnERKat_XXoHzn2NwGG8RwF64AlH_9oThinOvieRNR2brfZYPfe8roSywqu80ZISgJzNw_EwBqBgaQR9by1qBrKIqUAqguONdZlwK9VO8IxuTnQSflXXTyJGDSiKp_GIQFhdruPjOkGEuH4bKMUZkkeZtuzpIEEu_O1detswk05YCFOx96ZdXFJ3arQwhtQa3O-JkvE17u5r-aV9Ty_eJct6q3x3Dp-0FKtFuTdPlFCHycLPfGG4b0ZquC_Pr0MGKzEuS0.5ssqeqNcXkTjyX83T1NF7Z5fotuq5-jDn2TuquZLLhc"

rq_uid = str(uuid.uuid4())

headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json',
    'RqUID': rq_uid
}

# РАБОЧИЕ МОДЕЛИ (не Lite!)
models_to_try = ["GigaChat", "GigaChat-Pro", "GigaChat-Plus"]  # Freemium тариф

for model in models_to_try:
    print(f"\nТестируем модель: {model}")
    data = {
        "model": model,
        "messages": [{"role": "user", "content": f"Привет! Тест модели {model} для family_budget."}],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    response = requests.post(
        'https://gigachat.devices.sberbank.ru/api/v1/chat/completions',
        headers=headers,
        json=data,
        verify=False
    )
    
    print(f"Статус {model}: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ МОДЕЛЬ РАБОТАЕТ!")
        print(result['choices'][0]['message']['content'])
        break
    else:
        print(f"Ошибка: {response.text}")

print("\nГотово для family_budget!")
