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
    2. Сохраняет/обновляет заказ в Supabase
    3. Отправляет уведомление в Telegram (если настроено)
    """
    try:
        order_data = payload.order
        order_id = order_data.get("id") or order_data.get("externalId")
        
        if not order_id:
            raise HTTPException(status_code=400, detail="Order ID is required")
        
        # Инициализируем сервисы
        supabase_service = SupabaseService()
        telegram_service = TelegramService()
        
        # Сохраняем заказ в Supabase
        supabase_service.save_order(order_data)
        
        # Отправляем уведомление в Telegram в фоне
        if settings.telegram_bot_token and settings.telegram_chat_id:
            background_tasks.add_task(
                telegram_service.send_order_notification,
                order_data
            )
        
        return {
            "status": "success",
            "order_id": order_id,
            "message": "Order processed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_webhook():
    """Тестовый эндпоинт для проверки работы вебхука"""
    return {
        "status": "ok",
        "message": "Webhook endpoint is working"
    }
