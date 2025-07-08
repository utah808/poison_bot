from aiogram import Bot, Dispatcher, executor, types
import re
import gspread
from google.oauth2.service_account import Credentials
from config import BOT_TOKEN
from cny_rate import get_cny_rate
from utils import calculate_price

# === Google Sheets ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_file(
    'poizonbot-465106-909673b2e2e6.json', scopes=SCOPES
)
SPREADSHEET_ID = '13l_Lmo9rO8DEjN2K6_NFP4yIHGkIWiGf7rxfhAYdy0o'
SHEET_NAME = 'Orders'
gc = gspread.authorize(CREDS)
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# === Bot ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
user_data = {}

# Главное меню с иконками
main_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add("👟 Обувь", "👕 Одежда", "🎒 Аксессуары")
main_kb.add("🔄 Перезапустить", "❌ Остановить")
main_kb.add("💬 Связаться с администратором")

# /start с новым приветствием
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    uid = message.from_user.id
    user_data[uid] = {"items": []}
    await message.answer(
        "👋 Привет! Я — PoisonBot.\n\n"
        "Этот бот — для заказа брендовых и качественных вещей с Poizon 🇨🇳.\n"
        "Если нужно заказать с других китайских платформ или оптом — напиши администратору.\n\n"
        "📦 Собирай свой заказ шаг за шагом прямо здесь.\n"
        "Спасибо, что ты с нами!",
        reply_markup=main_kb
    )

# Перезапустить с иконкой
@dp.message_handler(lambda msg: msg.text == "🔄 Перезапустить")
async def restart(message: types.Message):
    uid = message.from_user.id
    user_data.pop(uid, None)
    await start_cmd(message)

# Остановить с иконкой
@dp.message_handler(lambda msg: msg.text == "❌ Остановить")
async def cancel(message: types.Message):
    uid = message.from_user.id
    user_data.pop(uid, None)
    await message.answer("❌ Заказ отменён.", reply_markup=main_kb)

# Связь с админом
@dp.message_handler(lambda msg: msg.text == "💬 Связаться с администратором")
async def contact_admin(message: types.Message):
    await message.answer("📞 Связаться с администратором: @utah808")

# Категория с иконками
@dp.message_handler(lambda msg: msg.text in ["👟 Обувь", "👕 Одежда", "🎒 Аксессуары"])
async def category_chosen(message: types.Message):
    uid = message.from_user.id
    if "items" not in user_data.get(uid, {}):
        user_data[uid] = {"items": []}

    if len(user_data[uid]["items"]) >= 5:
        await message.answer("❌ Вы уже добавили максимум 5 товаров! Переходим к оформлению.")
        await proceed_to_checkout(message)
        return

    category_name = message.text.split(" ")[1].lower()
    user_data[uid]["current"] = {"category": category_name}
    await message.answer("📎 Пришли ссылку на товар:")

# Ловим всё
@dp.message_handler(lambda msg: True)
async def handle_all(message: types.Message):
    uid = message.from_user.id
    data = user_data.get(uid, {})
    current = data.get("current")

    if data.get("proceeding"):
        if message.text == "✅ Продолжить заказ":
            data["ready_for_details"] = True
            await message.answer("✏️ Введи ФИО:")
            return

        if message.text == "❌ Отменить заказ":
            user_data.pop(uid, None)
            await message.answer("❌ Заказ отменён.", reply_markup=main_kb)
            return

        if data.get("ready_for_details"):
            if "fio" not in data:
                data["fio"] = message.text.strip()
                await message.answer("📞 Введи номер телефона:")
                return

            elif "phone" not in data:
                data["phone"] = message.text.strip()
                await message.answer("🏠 Введи адрес доставки:")
                return

            elif "address" not in data:
                data["address"] = message.text.strip()
                await message.answer("📬 Введи почтовый индекс:")
                return

            elif "index" not in data:
                data["index"] = message.text.strip()
                await save_order(uid, message)
                return

    if message.text == "Добавить ещё товар":
        await message.answer("📂 Выбери категорию нового товара:", reply_markup=main_kb)
        return

    if message.text == "Перейти к оформлению":
        await proceed_to_checkout(message)
        return

    if not current:
        await message.answer("Пожалуйста, выбери категорию товара.", reply_markup=main_kb)
        return

    if "link" not in current:
        url_match = re.search(r'(https?://\S+)', message.text)
        if not url_match:
            await message.answer("❌ Ссылка не найдена, пришли ещё раз.")
            return
        current["link"] = url_match.group(1)
        await message.answer("📏 Введи размер товара:")
        return

    if "size" not in current:
        current["size"] = message.text.strip()
        await message.answer("🎨 Укажи цвет товара:")
        return

    if "color" not in current:
        current["color"] = message.text.strip()
        await message.answer("💴 Укажи цену в юанях:")
        return

    if "price_yuan" not in current:
        if not message.text.strip().isdigit():
            await message.answer("❌ Введи цену числом, например: 699")
            return

        price_yuan = int(message.text.strip())
        cny = get_cny_rate()
        final_price, weight = calculate_price(price_yuan, cny, current["category"])
        delivery_price = round(weight * 700)
        total_price = round(final_price + delivery_price)

        current.update({
            "price_yuan": price_yuan,
            "price_rub": total_price,
            "weight": weight
        })

        user_data[uid]["items"].append(current)
        user_data[uid].pop("current", None)

        if len(user_data[uid]["items"]) >= 5:
            await message.answer("✅ Вы добавили максимум 5 товаров! Переходим к оформлению заказа.")
            await proceed_to_checkout(message)
            return

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Добавить ещё товар", "Перейти к оформлению")
        await message.answer(
            f"💰 Итоговая цена за этот товар: {total_price}₽\n"
            f"📦 Доставка Почтой России оплачивается отдельно!\n\n"
            f"Что дальше?",
            reply_markup=kb
        )
        return

# Финальный расчёт с эмодзи
async def proceed_to_checkout(message):
    uid = message.from_user.id
    user_data[uid]["proceeding"] = True
    user_data[uid]["ready_for_details"] = False

    total = 0
    total_delivery = 0
    cny = get_cny_rate()
    summary = []

    category_icons = {
        "обувь": "👟",
        "одежда": "🧥",
        "аксессуары": "🎒"
    }

    for item in user_data[uid]["items"]:
        icon = category_icons.get(item['category'], "📦")
        delivery = round(item["weight"] * 700)
        total += item["price_rub"]
        total_delivery += delivery

        summary.append(
            f"{icon} {item['category'].capitalize()}: {item['link']}\n"
            f"Размер: {item['size']}, Цвет: {item['color']}, Цена: {item['price_yuan']} юаней"
        )

    text = "\n\n".join(summary)

    await message.answer(
        f"🛒 Товары:\n{text}\n\n"
        f"📈 Актуальный курс: {cny}₽\n"
        f"🚚 Доставка до Уссурийска: {total_delivery}₽\n"
        f"💰 Общая сумма: {total}₽\n"
        f"📦 Доставка Почтой России оплачивается отдельно!",
        disable_web_page_preview=True
    )

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Продолжить заказ", "❌ Отменить заказ")
    await message.answer("Проверь расчёты и выбери, продолжить ли оформление заказа:", reply_markup=kb)

# Сохраняем заказ красиво: каждая вещь — отдельная строка
async def save_order(uid, message):
    data = user_data[uid]

    for item in data["items"]:
        row = [
            data["fio"],
            data["phone"],
            data["address"],
            data["index"],
            item["category"],
            item["link"],
            item["size"],
            item["color"],
            item["price_yuan"],
            item["price_rub"],
            item["weight"]
        ]
        sheet.append_row(row, value_input_option='USER_ENTERED')

    await message.answer("✅ Заказ оформлен и записан! Мы свяжемся с вами.", reply_markup=main_kb)
    user_data.pop(uid, None)

# Ловим любое неизвестное сообщение
@dp.message_handler(lambda msg: msg.text not in [
    "👟 Обувь", "👕 Одежда", "🎒 Аксессуары",
    "🔄 Перезапустить", "❌ Остановить", "💬 Связаться с администратором",
    "Добавить ещё товар", "Перейти к оформлению",
    "✅ Продолжить заказ", "❌ Отменить заказ"
])
async def unknown_message(message: types.Message):
    await message.answer(
        "❓ Я тебя не понял.\nПожалуйста, выбери вариант из меню ниже:",
        reply_markup=main_kb
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)








    





