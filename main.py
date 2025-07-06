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

# Главное меню клавиатура
main_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add("Обувь", "Одежда", "Аксессуары")
main_kb.add("Перезапустить", "Остановить")
main_kb.add("💬 Связаться с администратором")

# /start
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("👋 Привет! Выбери категорию товара:", reply_markup=main_kb)

# Перезапустить
@dp.message_handler(lambda msg: msg.text == "Перезапустить")
async def restart(message: types.Message):
    uid = message.from_user.id
    user_data.pop(uid, None)
    await start_cmd(message)

# Остановить
@dp.message_handler(lambda msg: msg.text == "Остановить")
async def cancel(message: types.Message):
    uid = message.from_user.id
    user_data.pop(uid, None)
    await message.answer("❌ Заказ отменён.", reply_markup=main_kb)

# Связь с админом (ставим ПЕРЕД handle_all!)
@dp.message_handler(lambda msg: msg.text == "💬 Связаться с администратором")
async def contact_admin(message: types.Message):
    await message.answer("📞 Связаться с администратором: @utah808")

# Категория
@dp.message_handler(lambda msg: msg.text in ["Обувь", "Одежда", "Аксессуары"])
async def category_chosen(message: types.Message):
    uid = message.from_user.id
    user_data[uid] = {"category": message.text.lower()}
    await message.answer("📎 Пришли ссылку на товар:")

# Ловим всё остальное
@dp.message_handler(lambda msg: True)
async def handle_all(message: types.Message):
    uid = message.from_user.id

    # Размер
    if uid in user_data and user_data[uid].get("link") and not user_data[uid].get("size"):
        user_data[uid]["size"] = message.text.strip()
        await message.answer("🎨 Укажи цвет товара:")
        return

    # Цвет
    if uid in user_data and user_data[uid].get("size") and not user_data[uid].get("color"):
        user_data[uid]["color"] = message.text.strip()
        await message.answer("💴 Укажи цену в юанях:")
        return

    # Цена
    if uid in user_data and user_data[uid].get("color") and not user_data[uid].get("price_yuan"):
        if not message.text.strip().isdigit():
            await message.answer("❌ Введи цену числом, например: 699")
            return
        price_yuan = int(message.text.strip())
        user_data[uid]["price_yuan"] = price_yuan

        cny = get_cny_rate()
        category = user_data[uid]["category"]
        raw_final_price, weight = calculate_price(price_yuan, cny, category)

        delivery_price = round(weight * 700)
        final_price = round(raw_final_price + delivery_price)

        user_data[uid]["price_rub"] = final_price
        user_data[uid]["weight"] = weight

        await message.answer(
            f"📦 Категория: {category}\n"
            f"📈 Актуальный курс: {cny}₽\n"
            f"🚚 Доставка до Уссурийска: {delivery_price}₽\n"
            f"💰 Итоговая цена: {final_price}₽\n\n"
            f"📦 Важно: доставка в ваш город Почтой России оплачивается отдельно!\n\n"
            f"✏️ Введи ФИО:"
        )
        return

    # ФИО
    if uid in user_data and user_data[uid].get("price_rub") and not user_data[uid].get("fio"):
        user_data[uid]["fio"] = message.text.strip()
        await message.answer("📞 Введи номер телефона:")
        return

    # Телефон
    if uid in user_data and user_data[uid].get("fio") and not user_data[uid].get("phone"):
        user_data[uid]["phone"] = message.text.strip()
        await message.answer("🏠 Введи адрес доставки:")
        return

    # Адрес
    if uid in user_data and user_data[uid].get("phone") and not user_data[uid].get("address"):
        user_data[uid]["address"] = message.text.strip()
        await message.answer("📬 Введи почтовый индекс:")
        return

    # Индекс
    if uid in user_data and user_data[uid].get("address") and not user_data[uid].get("index"):
        user_data[uid]["index"] = message.text.strip()

        # Запись
        data = user_data[uid]
        row = [
            data.get("fio") or "", data.get("phone") or "", data.get("address") or "", data.get("index") or "",
            data.get("link") or "", data.get("size") or "", data.get("color") or "",
            data.get("price_yuan") or "", data.get("price_rub") or "", data.get("weight") or ""
        ]
        sheet.append_row(row, value_input_option='USER_ENTERED')

        await message.answer("✅ Заказ сохранён! Мы свяжемся с вами.", reply_markup=main_kb)
        user_data.pop(uid, None)
        return

    # Поиск ссылки
    if uid not in user_data or not user_data[uid].get("link"):
        url_match = re.search(r'(https?://\S+)', message.text)
        if not url_match:
            await message.answer("❌ Ссылка не найдена, пришли ещё раз.")
            return
        link = url_match.group(1)
        user_data.setdefault(uid, {})["link"] = link
        await message.answer(f"🔗 Ссылка сохранена: {link}\n\n📏 Введи размер:")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


    





