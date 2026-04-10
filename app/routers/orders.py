from fastapi import APIRouter, HTTPException
from app.services.supabase import SupabaseService

router = APIRouter()


@router.get("/orders")
async def get_orders():
    """
    Получает все заказы из Supabase
    Для использования в дашборде
    """
    try:
        supabase_service = SupabaseService()
        orders = supabase_service.get_orders(limit=1000)
        return orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
