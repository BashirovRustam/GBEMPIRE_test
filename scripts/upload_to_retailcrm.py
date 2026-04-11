"""
Шаг 2: Загрузка заказов из mock_orders.json в RetailCRM через API
Запуск: python scripts/upload_to_retailcrm.py
"""

import json
import time
import sys
from pathlib import Path

import httpx

# Добавляем корень проекта в sys.path чтобы импортировать config
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings


# ─── Константы ────────────────────────────────────────────────────────────────

MOCK_ORDERS_PATH = Path(__file__).resolve().parent.parent / "mock_orders.json"

# RetailCRM не любит слишком частые запросы — делаем паузу между ними
REQUEST_DELAY_SEC = 0.3

# Slug сайта в RetailCRM (Settings → Sites)
RETAILCRM_SITE = "Demo_CRM"

# Webhook URL для Telegram-уведомлений
WEBHOOK_URL = "http://localhost:8000/webhook/retailcrm"


# ─── Хелперы ──────────────────────────────────────────────────────────────────

def calc_total(items: list[dict]) -> float:
    """Считаем сумму заказа: quantity * initialPrice по каждой позиции"""
    return sum(item["quantity"] * item["initialPrice"] for item in items)


def map_order_to_retailcrm(order: dict, number: int) -> dict:
    """
    Маппинг полей из mock_orders.json → формат RetailCRM API v5
    Документация: https://docs.retailcrm.ru/Developers/API/APIVersions/APIv5
    """
    total = calc_total(order["items"])

    payload = {
        "number": f"MOCK-{number:04d}",  # уникальный номер заказа
        "orderType": "main",              # дефолтный тип в демо-аккаунте
        "orderMethod": "shopping-cart",
        "status": order.get("status", "new"),

        # Клиент
        "firstName": order["firstName"],
        "lastName": order["lastName"],
        "phone": order["phone"],
        "email": order["email"],

        # Сумма
        "summ": total,

        # Позиции заказа
        "items": [
            {
                "productName": item["productName"],
                "quantity": item["quantity"],
                "initialPrice": item["initialPrice"],
            }
            for item in order["items"]
        ],

        # Доставка
        "delivery": {
            "address": {
                "city": order["delivery"]["address"]["city"],
                "text": order["delivery"]["address"]["text"],
            }
        },

        # UTM-метки через customFields
        "customFields": {
            "utm_source": order.get("customFields", {}).get("utm_source", ""),
        },
    }

    return payload


# ─── Основная логика ──────────────────────────────────────────────────────────

def upload_orders() -> None:
    # 1. Читаем файл
    if not MOCK_ORDERS_PATH.exists():
        print(f"[ERROR] Файл не найден: {MOCK_ORDERS_PATH}")
        sys.exit(1)

    with open(MOCK_ORDERS_PATH, encoding="utf-8") as f:
        orders: list[dict] = json.load(f)

    print(f"[INFO] Загружено {len(orders)} заказов из {MOCK_ORDERS_PATH.name}")
    print(f"[INFO] RetailCRM URL: {settings.retailcrm_api_url}")
    print(f"[INFO] Site: {RETAILCRM_SITE}")
    print("-" * 60)

    base_url = settings.retailcrm_api_url.rstrip("/")
    endpoint = f"{base_url}/api/v5/orders/create"

    success_count = 0
    error_count = 0

    with httpx.Client(timeout=15.0) as client:
        for idx, order in enumerate(orders, start=1):
            payload = map_order_to_retailcrm(order, number=idx)

            try:
                response = client.post(
                    endpoint,
                    data={
                        "apiKey": settings.retailcrm_api_key,
                        "site": RETAILCRM_SITE,
                        "order": json.dumps(payload, ensure_ascii=False),
                    },
                )

                result = response.json()

                if response.status_code == 201 and result.get("success"):
                    crm_id = result.get("id", "?")
                    total = calc_total(order["items"])
                    print(
                        f"[OK]    #{idx:02d} | {order['firstName']} {order['lastName']}"
                        f" | {total:,.0f} ₸ | CRM id={crm_id}"
                    )
                    success_count += 1

                    # Вызываем webhook для Telegram-уведомления если сумма > 50,000
                    if total > 50000:
                        try:
                            print(f"[TELEGRAM] Отправка уведомления для заказа #{crm_id} (сумма: {total} ₸)")
                            webhook_response = client.post(
                                WEBHOOK_URL,
                                json={"order": order},
                                timeout=10.0
                            )
                            print(f"[TELEGRAM] Статус ответа: HTTP {webhook_response.status_code}")
                            if webhook_response.status_code == 200:
                                print(f"[TELEGRAM] Уведомление отправлено для заказа #{crm_id}")
                                print(f"[TELEGRAM] Ответ: {webhook_response.text}")
                            else:
                                print(f"[TELEGRAM] Ошибка отправки: HTTP {webhook_response.status_code}")
                                print(f"[TELEGRAM] Ответ: {webhook_response.text}")
                        except Exception as e:
                            print(f"[TELEGRAM] Ошибка: {e}")
                    else:
                        print(f"[INFO] Сумма заказа {total} ₸ - уведомление не требуется (threshold: 50,000 ₸)")
                else:
                    error_msg = result.get("errorMsg") or result.get("errors") or result
                    print(
                        f"[WARN]  #{idx:02d} | {order['firstName']} {order['lastName']}"
                        f" | HTTP {response.status_code} | {error_msg}"
                    )
                    error_count += 1

            except httpx.RequestError as exc:
                print(f"[ERROR] #{idx:02d} | Сетевая ошибка: {exc}")
                error_count += 1

            # Пауза между запросами — не перегружаем API
            time.sleep(REQUEST_DELAY_SEC)

    # Итог
    print("-" * 60)
    print(f"[DONE] Успешно: {success_count} | Ошибок: {error_count} | Всего: {len(orders)}")


if __name__ == "__main__":
    upload_orders()