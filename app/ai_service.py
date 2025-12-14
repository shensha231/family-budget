import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_smart_advice(summary):
    prompt = (
        "Ты финансовый помощник. На основе сводки расходов семьи придумай 3–5 " 
        "оригинальных, практических советов без банальностей.\n\n" + summary
    )
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    return resp.choices[0].message["content"]
