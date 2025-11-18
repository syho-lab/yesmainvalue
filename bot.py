import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import requests
import json

# Загрузка токена
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Получение актуальных курсов
def get_exchange_rates():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        response = requests.get(url)
        data = response.json()
        return data['rates']
    except Exception as e:
        logging.error(f"Error fetching rates: {e}")
        return None

# Генерация клавиатуры с валютами
def get_currency_keyboard():
    rates = get_exchange_rates()
    if not rates:
        return None
    
    popular_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'RUB', 'KZT', 'UAH', 'BTC', 'ETH']
    
    # Создаем кнопки только для популярных валют
    keyboard = []
    row = []
    for currency in popular_currencies:
        if currency in rates:
            rate = rates[currency]
            row.append(InlineKeyboardButton(
                f"{get_currency_flag(currency)} {currency} ({rate:.2f})", 
                callback_data=f"select_{currency}"
            ))
            if len(row) == 2:  # 2 кнопки в строке
                keyboard.append(row)
                row = []
    
    # Кнопка "Все валюты"
    keyboard.append([InlineKeyboardButton("🌍 Все валюты", callback_data="show_all")])
    
    return InlineKeyboardMarkup(keyboard)

def get_currency_flag(currency):
    flags = {
        'USD': '🇺🇸', 'EUR': '🇪🇺', 'GBP': '🇬🇧', 'JPY': '🇯🇵', 'CNY': '🇨🇳',
        'RUB': '🇷🇺', 'KZT': '🇰🇿', 'UAH': '🇺🇦', 'BTC': '₿', 'ETH': '🔶'
    }
    return flags.get(currency, '💱')

# Красивое форматирование сообщения
def format_currency_message(base_currency, target_currency, amount, rates):
    if base_currency not in rates or target_currency not in rates:
        return "❌ Валюта не найдена"
    
    base_rate = rates[base_currency]
    target_rate = rates[target_currency]
    converted_amount = (amount / base_rate) * target_rate
    
    message = f"""
💱 *Конвертер валют*

`{amount:,.2f}` {base_currency} {get_currency_flag(base_currency)} = 
`{converted_amount:,.2f}` {target_currency} {get_currency_flag(target_currency)}

📊 *Курс:* 1 {base_currency} = {target_rate/base_rate:.4f} {target_currency}
🕒 *Обновлено:* сейчас

💡 Выберите валюты для конвертации:
    """
    return message

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🌟 *Добро пожаловать в Universal Currency Converter!* 🌟

💫 *Возможности:*
• 🔄 Конвертация 150+ валют
• ₿ Криптовалюты (BTC, ETH)
• ⚡ Мгновенное обновление курсов
• 🎯 Простой выбор из меню

💡 *Как использовать:*
1. Нажмите кнопку с валютой для конвертации
2. Введите сумму
3. Выберите целевую валюту

📊 *Пример:* `100 USD` → `9,300 RUB`
    """
    
    keyboard = get_currency_keyboard()
    if keyboard:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await update.message.reply_text("❌ Ошибка загрузки курсов. Попробуйте позже.")

# Обработчик инлайн-кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("select_"):
        currency = data.split("_")[1]
        context.user_data['base_currency'] = currency
        await query.edit_message_text(
            f"💎 Выбрана валюта: *{currency}* {get_currency_flag(currency)}\n\n"
            f"💵 *Введите сумму для конвертации:*\n"
            f"Пример: `100` или `500.50`",
            parse_mode='Markdown'
        )
    
    elif data == "show_all":
        rates = get_exchange_rates()
        if rates:
            all_currencies = "\n".join([f"`{curr}` - {rate:.2f}" for curr, rate in list(rates.items())[:20]])
            await query.edit_message_text(
                f"📋 *Доступные валюты (первые 20):*\n\n{all_currencies}\n\n"
                f"💡 Используйте код валюты для ручного ввода\n"
                f"Пример: `100 USD to RUB`",
                parse_mode='Markdown'
            )

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data
    
    try:
        # Если выбрана базовая валюта, ожидаем сумму
        if 'base_currency' in user_data and text.replace('.', '').isdigit():
            amount = float(text)
            user_data['amount'] = amount
            
            rates = get_exchange_rates()
            if rates:
                keyboard = get_currency_keyboard()
                await update.message.reply_text(
                    f"💰 *Сумма:* `{amount:,.2f}` {user_data['base_currency']}\n\n"
                    f"🎯 *Теперь выберите целевую валюту:*",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
        
        # Если есть сумма и базовая валюта, и выбрана целевая валюта через кнопку
        elif 'amount' in user_data and 'base_currency' in user_data:
            # Обработка выбора целевой валюты
            pass
            
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректную сумму")

# Главная функция
def main():
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
