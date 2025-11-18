import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import requests
import json
from datetime import datetime

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

def get_currency_flag(currency):
    flags = {
        'USD': '🇺🇸', 'EUR': '🇪🇺', 'GBP': '🇬🇧', 'JPY': '🇯🇵', 'CNY': '🇨🇳',
        'RUB': '🇷🇺', 'KZT': '🇰🇿', 'UAH': '🇺🇦', 'BTC': '₿', 'ETH': '🔶',
        'AED': '🇦🇪', 'AFN': '🇦🇫', 'ALL': '🇦🇱', 'AMD': '🇦🇲', 'ANG': '🇳🇱',
        'AOA': '🇦🇴', 'ARS': '🇦🇷', 'AUD': '🇦🇺', 'AWG': '🇦🇼', 'AZN': '🇦🇿',
        'BAM': '🇧🇦', 'BBD': '🇧🇧', 'BDT': '🇧🇩', 'BGN': '🇧🇬', 'BHD': '🇧🇭',
        'BIF': '🇧🇮', 'BMD': '🇧🇲', 'BND': '🇧🇳', 'BOB': '🇧🇴'
    }
    return flags.get(currency, '💱')

# Генерация основной клавиатуры
def get_main_keyboard():
    rates = get_exchange_rates()
    if not rates:
        return None
    
    popular_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'RUB', 'KZT', 'UAH', 'BTC', 'ETH']
    
    keyboard = []
    row = []
    for currency in popular_currencies:
        if currency in rates:
            rate = rates[currency]
            row.append(InlineKeyboardButton(
                f"{get_currency_flag(currency)} {currency}", 
                callback_data=f"select_base_{currency}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
    
    if row:  # Добавляем оставшиеся кнопки
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🌍 Все валюты", callback_data="show_all")])
    return InlineKeyboardMarkup(keyboard)

# Генерация клавиатуры для выбора целевой валюты
def get_target_currency_keyboard(base_currency):
    rates = get_exchange_rates()
    if not rates:
        return None
    
    popular_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'RUB', 'KZT', 'UAH', 'BTC', 'ETH']
    
    keyboard = []
    row = []
    for currency in popular_currencies:
        if currency != base_currency and currency in rates:
            row.append(InlineKeyboardButton(
                f"{get_currency_flag(currency)} {currency}", 
                callback_data=f"select_target_{currency}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
    
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🌍 Все валюты", callback_data="show_all_target")])
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

# Красивое форматирование результата
def format_conversion_result(base_currency, target_currency, amount, rates):
    if base_currency not in rates or target_currency not in rates:
        return "❌ Валюта не найдена"
    
    base_rate = rates[base_currency]
    target_rate = rates[target_currency]
    converted_amount = (amount / base_rate) * target_rate
    exchange_rate = target_rate / base_rate
    
    message = f"""
💫 *Результат конвертации*

`{amount:,.2f}` {base_currency} {get_currency_flag(base_currency)} = 
*`{converted_amount:,.2f}`* {target_currency} {get_currency_flag(target_currency)}

📊 **Курс:** 1 {base_currency} = {exchange_rate:.4f} {target_currency}
🔄 **Обратный курс:** 1 {target_currency} = {1/exchange_rate:.4f} {base_currency}
⏰ *Обновлено:* {datetime.now().strftime('%d.%m.%Y %H:%M')}

💡 Для нового расчета нажмите /start
    """
    return message

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищаем данные пользователя
    context.user_data.clear()
    
    welcome_text = """
🌟 *Добро пожаловать в Universal Currency Converter!* 🌟

💫 *Возможности:*
• 🔄 Конвертация 150+ валют
• ₿ Криптовалюты (BTC, ETH)
• ⚡ Мгновенное обновление курсов
• 🎯 Простой выбор из меню

💡 *Как использовать:*
1. Нажмите кнопку с исходной валютой
2. Введите сумму
3. Выберите целевую валюту

📊 *Пример:* `100 USD` → `9,300 RUB`
    """
    
    keyboard = get_main_keyboard()
    if keyboard:
        if update.message:
            await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=keyboard)
        else:
            await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown', reply_markup=keyboard)
    else:
        if update.message:
            await update.message.reply_text("❌ Ошибка загрузки курсов. Попробуйте позже.")
        else:
            await update.callback_query.edit_message_text("❌ Ошибка загрузки курсов. Попробуйте позже.")

# Обработчик инлайн-кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_data = context.user_data
    
    if data.startswith("select_base_"):
        # Выбор базовой валюты
        currency = data.split("_")[2]
        user_data['base_currency'] = currency
        user_data['step'] = 'waiting_amount'
        
        await query.edit_message_text(
            f"💎 *Выбрана исходная валюта:* *{currency}* {get_currency_flag(currency)}\n\n"
            f"💵 *Введите сумму для конвертации:*\n"
            f"Пример: `100` или `500.50`",
            parse_mode='Markdown'
        )
    
    elif data.startswith("select_target_"):
        # Выбор целевой валюты и расчет
        target_currency = data.split("_")[2]
        base_currency = user_data.get('base_currency')
        amount = user_data.get('amount')
        
        if base_currency and amount:
            rates = get_exchange_rates()
            if rates:
                result = format_conversion_result(base_currency, target_currency, amount, rates)
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Новый расчет", callback_data="back_to_main")
                ]])
                await query.edit_message_text(result, parse_mode='Markdown', reply_markup=keyboard)
            else:
                await query.edit_message_text("❌ Ошибка получения курсов")
        else:
            await query.edit_message_text("❌ Данные не найдены. Начните заново /start")
    
    elif data == "show_all" or data == "show_all_target":
        # Показать все валюты
        rates = get_exchange_rates()
        if rates:
            all_currencies = "\n".join([f"`{curr}` - {rate:.2f}" for curr, rate in list(rates.items())[:20]])
            message = f"📋 *Доступные валюты (первые 20):*\n\n{all_currencies}\n\n"
            
            if data == "show_all_target":
                message += "💡 Выберите целевую валюту:"
                keyboard = get_target_currency_keyboard(user_data.get('base_currency', ''))
            else:
                message += "💡 Используйте код валюты для ручного ввода\nПример: `100 USD to RUB`"
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("↩️ Назад", callback_data="back_to_main")
                ]])
            
            await query.edit_message_text(message, parse_mode='Markdown', reply_markup=keyboard)
    
    elif data == "back_to_main":
        # Возврат в главное меню
        await start(update, context)

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data
    
    try:
        # Обработка ручного ввода: "100 USD to RUB"
        if ' to ' in text.upper():
            parts = text.upper().split(' TO ')
            if len(parts) == 2:
                amount_part = parts[0].strip()
                currencies_part = parts[1].strip()
                
                # Извлекаем сумму и валюты
                amount_str = ''.join(filter(lambda x: x.isdigit() or x == '.', amount_part))
                amount = float(amount_str)
                
                base_currency = ''.join(filter(str.isalpha, amount_part)).upper()
                target_currency = currencies_part.strip().upper()
                
                rates = get_exchange_rates()
                if rates and base_currency in rates and target_currency in rates:
                    result = format_conversion_result(base_currency, target_currency, amount, rates)
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Новый расчет", callback_data="back_to_main")
                    ]])
                    await update.message.reply_text(result, parse_mode='Markdown', reply_markup=keyboard)
                    return
                else:
                    await update.message.reply_text("❌ Неверные коды валют. Проверьте и попробуйте снова.")
                    return
        
        # Обработка суммы после выбора базовой валюты
        if user_data.get('step') == 'waiting_amount' and user_data.get('base_currency'):
            amount = float(text)
            user_data['amount'] = amount
            user_data['step'] = 'waiting_target'
            
            keyboard = get_target_currency_keyboard(user_data['base_currency'])
            await update.message.reply_text(
                f"💰 *Сумма:* `{amount:,.2f}` {user_data['base_currency']}\n\n"
                f"🎯 *Теперь выберите целевую валюту:*",
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите корректную сумму")
    except Exception as e:
        logging.error(f"Error in handle_message: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте снова /start")

# Главная функция
def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()
