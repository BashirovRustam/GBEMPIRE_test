
## 📝 Промпты для разработки

### Промпт импорта JSON в CRM

> У меня есть `mock_orders.json` с 50 заказами в структурированном формате. Напиши скрипт на языке Python который читает файл и загружает каждый заказ в RetailCRM через `POST /api/v5/orders/create`. API key передаётся как query param. Добавь задержку 300мс между запросами чтобы не словить rate limit. Выводи логи в консоли бэкенда.
>
> **Примечание:** Столкнулся с проблемой что кастомное поле из JSON `utm_source` не отображается по умолчанию в CRM. Пришлось потратить время на изучение документации сайта.

### Промпт для загрузки в таблицу Supabase

> Напиши скрипт на языке Python для записи в таблицу `Orders` по следующим параметрам:
> 
> 1. Забирай заказы из RetailCRM постранично (`GET /api/v5/orders`)
> 2. Трансформирует данные в схему таблицы Supabase:
>    - `id`, `first_name`, `last_name`, `phone`, `email`
>    - `city` (из `delivery.address.city`)
>    - `status`, `total_sum` (расчитывается из items)
>    - `utm_source` (из `customFields`)
>    - `items` (jsonb массив)
>    - `created_at`
> 
> Выводи логи в консоли бэкенда.

### Промпт для уведомлений в бот

> Используй настройку `config.py` в котором лежат настройки из секретных ключей telegram bot key и чат id бота. Напиши вебхук для уведомления в бот по условию: если при появлении нового заказа на сумму более 50,000 — вызови вэбхук для уведомления в бот по следующему шаблону:
> 
> ```
> 🛒 Новый заказ
> Номер: {order_id}
> 
> 👤 Клиент: {first_name} {last_name}
> 📧 Email: {email}
> 📱 Телефон: {phone}
> 💰 Сумма: {total_price} тенге
> 📊 Статус: {status}
> 📅 Создан: {created_at}
> Источник UTM: {utm_source}
> Тип заказа: {order_type}
> Метод заказа: {order_method}
> 
> 📦 Товары:
> • {productName} x{quantity} ({initialPrice} ₸)
> • {productName} x{quantity} ({initialPrice} ₸)
> ...
> 
> 📍 Адрес: г: {city}, {text}
> ```

## 📁 Структура проекта

```
GBEMPIRE_test/
├── app/
│   ├── config.py              # Конфигурация приложения
│   ├── main.py                # Точка входа FastAPI
│   ├── routers/
│   │   ├── orders.py          # API роутер для заказов
│   │   └── webhook.py         # Webhook для RetailCRM
│   └── services/
│       ├── retailcrm.py       # Сервис для работы с RetailCRM
│       ├── supabase.py        # Сервис для работы с Supabase
│       └── telegram.py        # Сервис для Telegram-бота
├── frontend/
│   └── index.html             # Дашборд с аналитикой
├── scripts/
│   ├── upload_to_retailcrm.py # Загрузка заказов в RetailCRM
│   └── sync_to_supabase.py    # Синхронизация с Supabase
├── api/
│   └── index.py               # Vercel serverless entry point
├── mock_orders.json           # Тестовые данные заказов
├── requirements.txt           # Зависимости Python
├── vercel.json                # Конфигурация Vercel
├── .env.example              # Пример переменных окружения
└── README.md                 # Документация
```