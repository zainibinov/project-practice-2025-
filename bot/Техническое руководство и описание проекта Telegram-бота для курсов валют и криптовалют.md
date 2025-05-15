# Техническое руководство и описание проекта Telegram-бота для курсов валют и криптовалют

  

## 1.

## 1. Введение

Данный Telegram-бот позволяет пользователям:

- Просматривать текущие курсы популярных валют (USD, EUR, GBP) относительно RUB.
- Просматривать курсы популярных криптовалют (BTC, ETH, BNB, XRP, SOL, ADA, DOGE, DOT, TRX, LINK) в USD.
- Конвертировать сумму из одной валюты в другую (поддерживаются основные мировые валюты).

---

## 2. Исследование предметной области

### 2.1. Источники данных

- Для курсов валют используется API [ExchangeRate-API](https://www.exchangerate-api.com/).
- Для курсов криптовалют — API CoinGecko (https://api.coingecko.com/api/v3/simple/price).

### 2.2. Анализ пользовательских сценариев

- Пользователь запускает бота командой /start.
- Пользователь выбирает категорию: курсы валют, курсы криптовалют, конвертор валют.
- В зависимости от выбора, бот отображает соответствующее меню.
- При выборе конкретной валюты или криптовалюты бот запрашивает актуальный курс и показывает его.
- В режиме конвертора пользователь вводит запрос в формате: 100 USD to RUB, бот возвращает результат конвертации.

---

## 3. Архитектура и структура бота

### 3.1. Компоненты

- **API-запросы:** функции get_exchange_rate и get_crypto_rate для получения данных с внешних API.
- **Меню и клавиатуры:** функции, возвращающие инлайн-клавиатуры с кнопками (get_main_menu, get_currency_menu, get_crypto_menu, get_converter_menu).
- **Обработчики:** функции start, button и handle_message обрабатывают пользовательские команды и действия.
- **Состояния пользователя:** словарь user_states хранит, в каком состоянии находится пользователь (например, ожидает ввод для конвертации).

---

### 3.2. Диаграмма архитектуры (UML диаграмма компонентов)

```javascript
plaintext
```


```javascript
+----------------+
|    Telegram    |
|     User       |
+--------+-------+
         |
         v
+----------------+
|  Telegram Bot  |
| (Application)  |
+-------+--------+
        |
        +--------------------+
        |                    |
        v                    v
+--------------+     +------------------+
| API запросы  |     |   Обработчики    |
| (exchange,   |     | (start, button,  |
|  crypto)     |     |  handle_message) |
+--------------+     +------------------+
        |
        v
+----------------+
| Внешние API    |
| (ExchangeRate, |
|  CoinGecko)    |
+----------------+
```

---

## 4. Техническое руководство по созданию бота

### 4.1. Установка и подготовка

- Убедитесь, что установлен Python 3.8+.
- Установите необходимые библиотеки:

```javascript
bash
```


```javascript
pip install python-telegram-bot requests
```

- Зарегистрируйте бота у BotFather и получите токен.

---

### 4.2. Основные шаги создания бота

#### Шаг 1: Импорт библиотек и объявление глобальных переменных

```javascript
python
```


```javascript
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters

user_states = {}  # Хранит состояние каждого пользователя
```

#### Шаг 2: Функции для получения курсов валют и криптовалют

```javascript
python
```


```javascript
def get_exchange_rate(base: str, target='RUB'):
    url = f"https://api.exchangerate-api.com/v4/latest/{base}"
    try:
        response = requests.get(url)
        data = response.json()
        return data['rates'].get(target)
    except:
        return None

def get_crypto_rate(crypto_id):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[crypto_id]['usd']
    except:
        return None
```

#### Шаг 3: Создание меню с кнопками

```javascript
python
```


```javascript
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Курс валют", callback_data='currency')],
        [InlineKeyboardButton("🪙 Криптовалюта", callback_data='crypto')],
        [InlineKeyboardButton("🔄 Конвертор", callback_data='converter')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Аналогично создаются get_currency_menu, get_crypto_menu и get_converter_menu
```

#### Шаг 4: Обработчик команды /start

```javascript
python
```


```javascript
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    name = user.first_name if user.first_name else "пользователь"
    welcome_text = f"👋 Привет, {name}!\n\nВыберите категорию:"
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu())
```

#### Шаг 5: Обработка нажатий кнопок

```javascript
python
```


```javascript
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == 'currency':
        await query.edit_message_text("Выберите валюту:", reply_markup=get_currency_menu())
    # ... остальные условия по коду
```

#### Шаг 6: Обработка текстовых сообщений для конвертации

```javascript
python
```


```javascript
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_states.get(user_id) == 'awaiting_conversion':
        text = update.message.text.strip().upper()
        try:
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
                user_states[user_id] = None
                await update.message.reply_text("Выберите, что вы хотите сделать далее:", reply_markup=get_main_menu())
            else:
                await update.message.reply_text("❌ Не удалось получить курс для этих валют.")
        except:
            await update.message.reply_text("⚠️ Неверный формат. Пример:\n`100 USD to RUB`", parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ Неверный формат. Пожалуйста, выберите опцию из меню или введите корректную команду.")
```

#### Шаг 7: Запуск бота

```javascript
python
```


```javascript
def main():
    app = Application.builder().token("ВАШ_ТОКЕН").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()
```

---

## 5. Иллюстрации

### 5.1. Диаграмма переходов по меню пользователя

```javascript
plaintext
```


```javascript
[Старт] --> [Главное меню]
            |           |          |
            v           v          v
     [Курс валют]  [Криптовалюта] [Конвертор]
            |           |          |
       [Выбор валюты] [Выбор крипты] [Ввод суммы]
```


