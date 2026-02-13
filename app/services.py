"""OpenRouter AI servis fonksiyonları."""

import requests
from flask import current_app


# ── Yardımcı ────────────────────────────────────────────────

def _api_call(messages, max_tokens=None):
    """OpenRouter API'ye istek gönder ve JSON yanıt döndür."""
    api_key = current_app.config["OPENROUTER_API_KEY"]
    model = current_app.config["OPENROUTER_MODEL"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = {"model": model, "messages": messages}
    if max_tokens:
        body["max_tokens"] = max_tokens

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=body,
    )
    return response.json()


# ── Genel Servisler ─────────────────────────────────────────

def get_first_greeting(psikolog):
    """İlk karşılama mesajını AI'dan al."""
    result = _api_call([
        {
            "role": "system",
            "content": (
                psikolog["sistem"]
                + " Bu ilk karşılaşman. Kendini tanıt, sıcak bir şekilde selamla "
                "ve ilk açık uçlu psikolojik soruyu sor. Kısa ve öz ol, "
                "maksimum 3-4 cümle."
            ),
        },
        {"role": "user", "content": "Merhaba, seninle konuşmak istiyorum."},
    ])

    if "choices" not in result:
        print("❌ API HATASI:", result)
        return (
            f"Merhaba! Ben {psikolog['isim']}. "
            "Seninle tanıştığıma memnun oldum. Bugün seni buraya getiren nedir?"
        )
    return result["choices"][0]["message"]["content"].strip()


def get_ai_response_with_style(history, psikolog, extended_mode=False):
    """Tarz bazlı AI yanıtı al."""
    base_prompt = (
        psikolog["sistem"]
        + " Danışanın son cevabına kısa bir yorum/karşılık ver (1-2 cümle), "
        "empati göster veya anlayış belirt, sonra yeni bir açık uçlu psikolojik "
        "soru sor. Toplamda 3-4 cümleyi geçme."
    )

    if extended_mode:
        base_prompt += (
            " \n\nÖNEMLİ: Görüşmede önemli bir noktaya ulaştın (10+ mesaj). "
            "Klinik bir değerlendirme için yeterli verin var mı değerlendir. "
            "Eğer YOKSA, eksik bilgiyi özellikle sor. "
            "Eğer VARSA, sohbeti doğal bir şekilde sürdür ama derinlemesine "
            "sorular sormaya devam et."
        )

    messages = [{"role": "system", "content": base_prompt}]
    for item in history:
        if item.get("tip") == "psikolog":
            messages.append({"role": "assistant", "content": item["mesaj"]})
        elif item.get("tip") == "kullanici":
            messages.append({"role": "user", "content": item["mesaj"]})

    result = _api_call(messages)
    if "choices" not in result:
        print("❌ API HATASI:", result)
        return "Anlıyorum... Peki bunu biraz daha açar mısın?"
    return result["choices"][0]["message"]["content"].strip()


def get_summary_response(qa_list):
    """Görüşme sonu analiz/özet yanıtı al."""
    content = "Aşağıda bir kişinin psikolojik sorulara verdiği yanıtlar var:\n\n"
    for i, qa in enumerate(qa_list, 1):
        content += f"{i}. Soru: {qa['soru']}\n   Cevap: {qa['cevap']}\n\n"

    content += (
        "Yukarıdaki yanıtlara göre bu kişinin ruhsal durumunu psikolojik açıdan gözlemle. "
        "Duygusal eğilimlerini, zorlandığı alanları ve dikkat çeken noktaları kısa ama öz "
        "bir dille analiz et. Lütfen tanı koy. 4-5 cümlelik profesyonel gözlem yap. "
        "Açıklayıcı, özgün ve sadece Türkçe yaz."
    )

    result = _api_call([
        {"role": "system", "content": "Sen bir deneyimli psikolojik danışmansın."},
        {"role": "user", "content": content},
    ])

    if "choices" not in result:
        print("❌ ANALİZ API HATASI:", result)
        return "Analiz oluşturulamadı."
    return result["choices"][0]["message"]["content"].strip()


def check_if_ready_for_diagnosis(history):
    """LLM'e sohbetin analiz için yeterli olup olmadığını sor."""
    try:
        conversation = ""
        for item in history:
            if item.get("tip") == "psikolog":
                conversation += f"Psikolog: {item['mesaj']}\n"
            else:
                conversation += f"Danışan: {item['mesaj']}\n"

        result = _api_call(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a clinical assessment expert. "
                        "Analyze the conversation and determine if there's enough "
                        "psychological data for a preliminary observation. "
                        "Answer ONLY with 'READY' or 'NOT_READY'. Nothing else."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Based on this conversation history, do you have enough data "
                        "to provide a preliminary psychological observation?\n\n"
                        + conversation
                    ),
                },
            ],
            max_tokens=10,
        )

        answer = result["choices"][0]["message"]["content"].strip().upper()
        print(f"🔍 READY kontrolü: {answer}")
        return "READY" in answer

    except Exception as e:
        print(f"❌ READY kontrol hatası: {e}")
        return False
