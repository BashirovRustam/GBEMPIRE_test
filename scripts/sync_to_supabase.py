"""
Шаг 3: Синхронизация заказов из RetailCRM → Supabase
Запуск: python scripts/sync_to_supabase.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

import httpx
from supabase import create_client, Client

# Добавляем корень проекта в sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings


# ─── Константы ────────────────────────────────────────────────────────────────

RETAILCRM_SITE = "Demo_CRM"
PAGE_LIMIT = 50  # максимум заказов за один запрос


# ─── Клиенты ──────────────────────────────────────────────────────────────────

def get_supabase() -> Client:
    key = settings.supabase_service_role_key or settings.supabase_anon_key
    if not settings.supabase_service_role_key:
        print("[WARN] Используется anon_key (не service_role_key).")
        print("[WARN] Для обхода RLS добавьте SUPABASE_SERVICE_ROLE_KEY в .env")
    return create_client(
        settings.supabase_url,
        key,
    )


# ─── RetailCRM ────────────────────────────────────────────────────────────────

def fetch_orders_from_retailcrm() -> list[dict]:
    """
    Забирает все заказы из RetailCRM постранично.
    GET /api/v5/orders
    """
    base_url = settings.retailcrm_api_url.rstrip("/")
    endpoint = f"{base_url}/api/v5/orders"

    all_orders: list[dict] = []
    page = 1

    with httpx.Client(timeout=30.0) as client:
        while True:
            response = client.get(
                endpoint,
                params={
                    "apiKey": settings.retailcrm_api_key,
                    "site": RETAILCRM_SITE,
                    "limit": PAGE_LIMIT,
                    "page": page,
                },
            )

            if response.status_code != 200:
                print(f"[ERROR] RetailCRM вернул {response.status_code}: {response.text}")
                break

            data = response.json()

            if not data.get("success"):
                print(f"[ERROR] RetailCRM: {data.get('errorMsg')}")
                break

            orders = data.get("orders", [])
            all_orders.extend(orders)

            print(f"[INFO] Страница {page}: получено {len(orders)} заказов")

            # Проверяем есть ли следующая страница
            pagination = data.get("pagination", {})
            total_pages = pagination.get("totalPageCount", 1)

            if page >= total_pages:
                break

            page += 1

    print(f"[INFO] Всего получено из RetailCRM: {len(all_orders)} заказов")
    return all_orders


# ─── Трансформация ────────────────────────────────────────────────────────────

def calc_total(items: list[dict]) -> float:
    """Считаем сумму: quantity * initialPrice по каждой позиции"""
    total = 0.0
    for item in items:
        qty = item.get("quantity") or item.get("count") or 1
        price = item.get("initialPrice") or item.get("price") or 0
        total += qty * price
    return total


def transform_order(order: dict) -> dict:
    """
    Маппинг полей RetailCRM → схема таблицы orders в Supabase

    Схема:
        id bigint primary key  -- id из RetailCRM
        first_name text
        last_name  text
        phone      text
        email      text
        city       text
        status     text
        total_sum  numeric
        utm_source text
        items      jsonb
        created_at timestamptz
    """
    items = order.get("items", [])
    total_sum = calc_total(items)

    # city может быть в delivery.address.city
    city = (
        order.get("delivery", {})
             .get("address", {})
             .get("city", "")
    )

    # utm_source хранится в customFields
    custom_fields = order.get("customFields", {})
    utm_source = custom_fields.get("utm_source", "") if isinstance(custom_fields, dict) else ""
    
    # Debug: выводим заказы с utm_source
    if utm_source:
        print(f"[DEBUG] Order {order.get('id')}: utm_source={utm_source}")

    # created_at — берём из RetailCRM, fallback на текущее время
    created_at = order.get("createdAt") or datetime.now(timezone.utc).isoformat()

    return {
        "id": order["id"],
        "first_name": order.get("firstName", ""),
        "last_name": order.get("lastName", ""),
        "phone": order.get("phone", ""),
        "email": order.get("email", ""),
        "city": city,
        "status": order.get("status", ""),
        "total_sum": total_sum,
        "utm_source": utm_source,
        "items": items,          # jsonb — передаём как список
        "created_at": created_at,
    }


# ─── Supabase ─────────────────────────────────────────────────────────────────

def sync_to_supabase(orders: list[dict], supabase: Client) -> None:
    """
    Upsert заказов в Supabase.
    Если заказ с таким id уже есть — обновляем, иначе — вставляем.
    """
    if not orders:
        print("[WARN] Нет заказов для синхронизации")
        return

    rows = []
    for order in orders:
        try:
            rows.append(transform_order(order))
        except Exception as exc:
            print(f"[WARN] Не удалось трансформировать заказ id={order.get('id')}: {exc}")

    print(f"[INFO] Подготовлено к upsert: {len(rows)} записей")
    print("-" * 60)

    # Upsert батчами по 50 — Supabase имеет лимиты на размер запроса
    batch_size = 50
    success_count = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            result = (
                supabase.table("Orders")
                .upsert(batch, on_conflict="id")
                .execute()
            )
            success_count += len(batch)
            print(f"[OK] Батч {i // batch_size + 1}: upsert {len(batch)} записей")
        except Exception as exc:
            print(f"[ERROR] Батч {i // batch_size + 1} не удался: {exc}")

    print("-" * 60)
    print(f"[DONE] Синхронизировано: {success_count}/{len(rows)} заказов")


# ─── Точка входа ──────────────────────────────────────────────────────────────

def main() -> None:
    print("[INFO] Старт синхронизации RetailCRM → Supabase")
    print(f"[INFO] RetailCRM: {settings.retailcrm_api_url}")
    print(f"[INFO] Supabase:  {settings.supabase_url}")
    print("-" * 60)

    # 1. Забираем заказы из RetailCRM
    orders = fetch_orders_from_retailcrm()

    if not orders:
        print("[WARN] Заказов нет — выходим")
        return

    # 2. Кладём в Supabase
    supabase = get_supabase()
    sync_to_supabase(orders, supabase)


if __name__ == "__main__":
    main()