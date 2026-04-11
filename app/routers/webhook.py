from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.retailcrm import RetailCRMService
from app.services.supabase import SupabaseService
from app.services.telegram import TelegramService
from app.config import settings

router = APIRouter()


class WebhookPayload(BaseModel):
    """Модель для валидации вебхука от RetailCRM"""
    order: Dict[str, Any]
    site: Optional[str] = None


@router.post("/retailcrm")
async def retailcrm_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks
):
    """
    Обрабатывает вебхук от RetailCRM при изменении заказа

    Flow:
    1. Получает данные заказа из вебхука
    2. Сохраняет/обновляет заказ в Supabase (если есть креденшиалы)
    3. Отправляет уведомление в Telegram для заказов > 50,000 ₸
    """
    try:
        order_data = payload.order
        order_id = order_data.get("id") or order_data.get("externalId")

        # Если нет ID, генерируем временный для тестирования
        if not order_id:
            order_id = f"test_{hash(str(order_data)) % 10000}"
            print(f"[WEBHOOK] ID отсутствует, сгенерирован временный: {order_id}")
            # Добавляем ID в order_data для Telegram
            order_data["id"] = order_id

        # Инициализируем сервисы
        try:
            supabase_service = SupabaseService()
            supabase_service.save_order(order_data)
        except ValueError as e:
            print(f"[WEBHOOK] Supabase не настроен: {e}")
            # Продолжаем без Supabase
        except Exception as e:
            print(f"[WEBHOOK] Ошибка Supabase: {e}")
            # Продолжаем без Supabase

        telegram_service = TelegramService()

        # Рассчитываем сумму заказа
        items = order_data.get("items", [])
        total_sum = sum(item.get("quantity", 0) * item.get("initialPrice", 0) for item in items)

        print(f"[WEBHOOK] Заказ #{order_id}, сумма: {total_sum} ₸")

        # Отправляем уведомление в Telegram только для заказов > 50,000 ₸
        if settings.telegram_bot_token and settings.telegram_chat_id and total_sum > 50000:
            print(f"[WEBHOOK] Отправка уведомления в Telegram...")
            import asyncio
            # Вызываем async функцию напрямую в фоне
            loop = asyncio.get_event_loop()
            loop.create_task(telegram_service.send_order_notification(order_data))
        else:
            print(f"[WEBHOOK] Уведомление не отправлено (threshold: 50,000 ₸, telegram configured: {bool(settings.telegram_bot_token)})")

        return {
            "status": "success",
            "order_id": order_id,
            "total_sum": total_sum,
            "message": "Order processed successfully"
        }

    except Exception as e:
        print(f"[WEBHOOK] Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_webhook():
    """Тестовый эндпоинт для проверки работы вебхука"""
    return {
        "status": "ok",
        "message": "Webhook endpoint is working"
    }
