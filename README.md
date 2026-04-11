# 📊 Order Dashboard — AI Tools Specialist

> Мини-дашборд заказов на базе RetailCRM + Supabase + Vercel + Telegram Bot

---

## 🔗 Ссылки

| | |
|---|---|
| 🌐 Дашборд | [gbempire-test.vercel.app](https://gbempire-test.vercel.app) |

---

## 🏗️ Архитектура

```
mock_orders.json
      │
      ▼
scripts/upload_to_retailcrm.py ──► RetailCRM API
                                         │
                                         ▼
                              scripts/sync_to_supabase.py
                                         │
                                         ▼
                                 Supabase (PostgreSQL)
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                     Vercel (FastAPI)         RetailCRM Webhook
                     frontend/index.html            │
                     [Дашборд + графики]             ▼
                                            Telegram Bot
                                      (уведомления > 50 000 ₸)
```

---

## ⚙️ Стек

- **RetailCRM** — источник заказов
- **Supabase** — PostgreSQL база данных
- **Vercel** — деплой FastAPI + статика
- **Telegram Bot API** — уведомления о крупных заказах
- **Python / FastAPI** — бэкенд и serverless функции
- **Claude Code CLI** — AI-ассистент при разработке

---



### 3. Загрузить заказы в RetailCRM

```bash
python scripts/upload_to_retailcrm.py
```

Читает `mock_orders.json` и загружает 50 заказов через `POST /api/v5/orders/create`.

### 4. Синхронизировать RetailCRM → Supabase

```bash
python scripts/sync_to_supabase.py
```

### 5. Запустить локально

```bash
uvicorn app.main:app --reload
# открыть http://localhost:8000
```

---

## 📁 Структура проекта

```
GBEMPIRE_test/
├── app/
│   ├── config.py              # Конфигурация через переменные окружения
│   ├── main.py                # Точка входа FastAPI
│   ├── routers/
│   │   ├── orders.py          # GET /api/orders
│   │   └── webhook.py         # Webhook от RetailCRM
│   └── services/
│       ├── retailcrm.py       # Клиент RetailCRM API
│       ├── supabase.py        # Клиент Supabase (через httpx)
│       └── telegram.py        # Отправка уведомлений
├── frontend/
│   └── index.html             # Дашборд с Chart.js
├── scripts/
│   ├── upload_to_retailcrm.py # Загрузка mock_orders.json → RetailCRM
│   └── sync_to_supabase.py    # Синхронизация RetailCRM → Supabase
├── api/
│   └── index.py               # Vercel serverless entry point (Mangum)
├── mock_orders.json           # 50 тестовых заказов
├── requirements.txt
├── vercel.json
├── .env.example
└── README.md
```

---

## 🤖 Claude Code — промпты, застревания, решения

### Шаг 1 — Загрузка заказов в RetailCRM

**Промпт:**
```
У меня есть mock_orders.json с 50 заказами в структурированном формате.
Напиши скрипт на Python который читает файл и загружает каждый заказ
в RetailCRM через POST /api/v5/orders/create. API key передаётся
как query param. Добавь задержку 300мс между запросами чтобы не
словить rate limit. Выводи логи в консоли бэкенда.
```

Скрипт заработал, но кастомное поле `utm_source` не отображалось в CRM — пришлось изучить документацию и разобраться как передавать данные через `customFields`.

---

### Шаг 2 — Синхронизация RetailCRM → Supabase

**Промпт:**
```
Напиши скрипт на Python для записи в таблицу Orders по параметрам:
1. Забирай заказы из RetailCRM постранично (GET /api/v5/orders)
2. Трансформируй данные в схему Supabase:
   - id, first_name, last_name, phone, email
   - city (из delivery.address.city)
   - status, total_sum (рассчитывается из items)
   - utm_source (из customFields)
   - items (jsonb массив)
   - created_at
Выводи логи в консоли.
```

---

### Шаг 3 — Telegram-бот

**Промпт:**
```
Используй config.py в котором лежат telegram bot key и chat id.
Напиши webhook для уведомления в бот: если при появлении нового
заказа сумма более 50 000 ₸ — отправь сообщение по шаблону:

🛒 Новый заказ
Номер: {order_id}
👤 Клиент: {first_name} {last_name}
💰 Сумма: {total_price} тенге
📊 Статус: {status}
📦 Товары: • {productName} x{quantity} ({initialPrice} ₸)
📍 Адрес: г. {city}, {text}
```

---

### 🪨 Застревание — Supabase обновил формат ключей

Это самый неожиданный блокер в проекте. После деплоя на Vercel дашборд возвращал `{"detail":"Invalid API key"}`. Локально всё работало.

Потратил несколько часов: проверял переменные окружения, смотрел логи Vercel, пробовал разные версии библиотек. В логах было видно `No outgoing requests` и время выполнения 4ms — функция падала до того как делала любой запрос к Supabase.

Добавил отладочный эндпоинт чтобы убедиться что переменные доходят:

```python
@app.get("/api/debug")
def debug():
    return {
        "supabase_url": os.environ.get("SUPABASE_URL", "NOT SET"),
        "key_length": len(os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")),
    }
```

Ключ был, длина правильная — но Supabase всё равно отвечал `Invalid API key`.

**Причина:** Supabase перешёл на новый формат ключей `sb_secret_...` вместо старого `eyJ...` (JWT). Библиотека `supabase-py 2.3.4` не поддерживает новый формат. Обновить библиотеку тоже не получилось — конфликт зависимостей: `supabase 2.9.1` требовал `httpx>=0.26`, а `python-telegram-bot 20.7` жёстко требовал `httpx==0.25.2`.

**Решение:** убрал `supabase-py` полностью и реализовал запросы к Supabase напрямую через `httpx`:

```python
headers = {
    "apikey": self.key,
    "Authorization": f"Bearer {self.key}",
    "Content-Type": "application/json",
}
response = httpx.get(f"{self.url}/rest/v1/Orders", headers=headers)
```

Новый формат ключей работает если передавать его напрямую в заголовках — без обёртки библиотеки.

**Вывод:** при дебаге на Vercel сразу добавляй `/api/debug` эндпоинт который проверяет переменные и делает тестовый запрос к зависимостям. Это экономит часы гадания. Также стоит проверять совместимость версий библиотек до деплоя — `pip check` в локальном окружении поймал бы конфликт сразу.

---
