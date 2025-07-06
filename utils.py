# utils.py

def calculate_price(price_yuan, cny_rate, category):
    """
    Рассчитать финальную цену товара с учётом комиссии и доставки.
    """
    # Вес по категории
    if category == "обувь":
        weight = 1.2
    elif category == "аксессуары":
        weight = 0.1
    else:  # Одежда
        weight = 0.7

    # Комиссия 10%
    commission = 0.10

    # Стоимость доставки — фиксированная ставка 700₽ за кг
    delivery_cost = weight * 700

    # Полный расчёт
    base_price = price_yuan * cny_rate
    total_price = (base_price + delivery_cost) * (1 + commission)

    return round(total_price, 2), weight
