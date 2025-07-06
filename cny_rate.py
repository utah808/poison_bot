import requests

# Твоя фиксированная надбавка в рублях
CNY_MARKUP = 0.7

def get_cny_rate():
    """
    Получает актуальный курс юаня с ЦБ РФ и добавляет фиксированную надбавку.
    Если что-то идёт не так — возвращает запасной курс 12.
    """
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        cny_raw = data["Valute"]["CNY"]
        nominal = cny_raw["Nominal"]
        value = cny_raw["Value"]

        # Приводим к цене за 1 юань
        base_rate = value / nominal
        final_rate = round(base_rate + CNY_MARKUP, 2)

        print(f"💱 Курс ЦБ: {base_rate:.4f}₽ → С надбавкой: {final_rate}₽")

        return final_rate

    except Exception as e:
        print(f"❌ Ошибка получения курса ЦБ: {e}")
        # Если не удалось получить — запасной курс
        return 12
