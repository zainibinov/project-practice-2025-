import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

# Состояния пользователей
user_states = {}

# Получение курса валют
def get_exchange_rate(base: str, target='RUB'):
    url = f"https://api.exchangerate-api.com/v4/latest/{base}"
    try:
        response = requests.get(url)
        data = response.json()
        return data['rates'].get(target)
    except:
        return None

# Получение курса криптовалют в USD через CoinGecko
def get_crypto_rate(crypto_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[crypto_id]['usd']
    except:
        return None

# 10 популярных криптовалют
def get_btc_rate(): return get_crypto_rate('bitcoin')
def get_eth_rate(): return get_crypto_rate('ethereum')
def get_bnb_rate(): return get_crypto_rate('binancecoin')
def get_xrp_rate(): return get_crypto_rate('ripple')
def get_sol_rate(): return get_crypto_rate('solana')
def get_ada_rate(): return get_crypto_rate('cardano')
def get_doge_rate(): return get_crypto_rate('dogecoin')
def get_dot_rate(): return get_crypto_rate('polkadot')
def get_trx_rate(): return get_crypto_rate('tron')
def get_link_rate(): return get_crypto_rate('chainlink')

# Главное меню
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Курс валют", callback_data='currency')],
        [InlineKeyboardButton("🪙 Криптовалюта", callback_data='crypto')],
        [InlineKeyboardButton("🔄 Конвертор", callback_data='converter')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Подменю валют
def get_currency_menu():
    keyboard = [
        [InlineKeyboardButton("USD → RUB", callback_data='usd')],
        [InlineKeyboardButton("EUR → RUB", callback_data='eur')],
        [InlineKeyboardButton("GBP → RUB", callback_data='gbp')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Подменю криптовалют
def get_crypto_menu():
    keyboard = [
        [InlineKeyboardButton("BTC", callback_data='btc'), InlineKeyboardButton("ETH", callback_data='eth')],
        [InlineKeyboardButton("BNB", callback_data='bnb'), InlineKeyboardButton("XRP", callback_data='xrp')],
        [InlineKeyboardButton("SOL", callback_data='sol'), InlineKeyboardButton("ADA", callback_data='ada')],
        [InlineKeyboardButton("DOGE", callback_data='doge'), InlineKeyboardButton("DOT", callback_data='dot')],
        [InlineKeyboardButton("TRX", callback_data='trx'), InlineKeyboardButton("LINK", callback_data='link')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='main')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Меню конвертера
def get_converter_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data='main')]])

# /start команда с приветствием
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    name = user.first_name if user.first_name else "пользователь"
    welcome_text = f"👋 Привет, {name}!\n\nВыберите категорию:"
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu())

# Обработка кнопок
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == 'currency':
        await query.edit_message_text("Выберите валюту:", reply_markup=get_currency_menu())

    elif data == 'crypto':
        await query.edit_message_text("Выберите криптовалюту:", reply_markup=get_crypto_menu())

    elif data == 'main':
        await query.edit_message_text("Выберите категорию:", reply_markup=get_main_menu())

    elif data == 'converter':
        user_states[user_id] = 'awaiting_conversion'
        await query.edit_message_text(
            "✏️ Введите сумму и валюты в формате, например:\n`100 USD to RUB` \n (поддерживаемые валюты USD, EUR, RUB, TJS, UZB, KZT, KGS, CNY, GBP)",
            reply_markup=get_converter_menu(),
            parse_mode='Markdown'
        )

    # Курсы валют
    elif data in ['usd', 'eur', 'gbp']:
        base = data.upper()
        rate = get_exchange_rate(base)
        msg = f"💵 1 {base} = {rate} RUB" if rate else f"❌ Не удалось получить курс {base}"
        await query.edit_message_text(msg, reply_markup=get_currency_menu())

    # Курсы криптовалют
    crypto_map = {
        'btc': get_btc_rate,
        'eth': get_eth_rate,
        'bnb': get_bnb_rate,
        'xrp': get_xrp_rate,
        'sol': get_sol_rate,
        'ada': get_ada_rate,
        'doge': get_doge_rate,
        'dot': get_dot_rate,
        'trx': get_trx_rate,
        'link': get_link_rate,
    }

    if data in crypto_map:
        rate = crypto_map[data]()
        msg = f"💸 1 {data.upper()} = {rate} USD" if rate else f"❌ Не удалось получить курс {data.upper()}"
        await query.edit_message_text(msg, reply_markup=get_crypto_menu())

# Обработка текстовых сообщений
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_states.get(user_id) == 'awaiting_conversion':
        text = update.message.text.strip().upper()
        try:
            # Разделяем текст по пробелам и извлекаем сумму, исходную валюту и целевую валюту
            parts = text.split()
            amount = float(parts[0])
            base = parts[1]
            target = parts[3] if parts[2] == 'TO' else None

            if not target:
                raise ValueError

            rate = get_exchange_rate(base, target)
            if rate:
                converted = round(amount * rate, 2)
                await update.message.reply_text(f"🔁 {amount} {base} = {converted} {target}")
                user_states[user_id] = None  # Сброс состояния после успешной конвертации

                # Отправляем основное меню после конвертации
                await update.message.reply_text(
                    "Выберите, что вы хотите сделать далее:",
                    reply_markup=get_main_menu()
                )
            else:
                await update.message.reply_text("❌ Не удалось получить курс для этих валют.")
        except:
            await update.message.reply_text("⚠️ Неверный формат. Пример:\n`100 USD to RUB`", parse_mode='Markdown')

    else:
        # Если пользователь не в режиме конвертации, отвечаем ошибкой
        await update.message.reply_text("⚠️ Неверный формат. Пожалуйста, выберите опцию из меню или введите корректную команду.")

# Запуск
def main():
    app = Application.builder().token("7970175320:AAH7qIeyad1JzplEab_WytyLgrPflNcvtL0").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()
