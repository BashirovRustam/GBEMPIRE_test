from datetime import datetime
from typing import Optional, Dict, Any
from supabase import create_client, Client
from app.config import settings


class SupabaseService:
    """Клиент для работы с Supabase"""
    
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key or settings.supabase_anon_key
        )
    
    def save_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Сохраняет или обновляет заказ в Supabase"""
        external_id = order_data.get("id") or order_data.get("externalId")
        
        if not external_id:
            raise ValueError("Order must have id or externalId")
        
        # Преобразуем данные в формат Supabase
        transformed_data = {
            "external_id": external_id,
            "first_name": order_data.get("firstName"),
            "last_name": order_data.get("lastName"),
            "email": order_data.get("email"),
            "phone": order_data.get("phone"),
            "status": order_data.get("status"),
            "total_price": order_data.get("sum", 0),
            "created_at": order_data.get("createdAt"),
            "delivery_address": order_data.get("delivery", {}).get("address"),
            "delivery_type": order_data.get("delivery", {}).get("type"),
            "synced_at": datetime.utcnow().isoformat(),
            "raw_data": order_data  # Сохраняем сырые данные
        }
        
        # Проверяем, существует ли заказ
        existing = self.client.table("Orders").select("id").eq("external_id", external_id).execute()
        
        if existing.data:
            # Обновляем существующий заказ
            result = self.client.table("Orders").update(transformed_data).eq("external_id", external_id).execute()
            return result.data[0] if result.data else None
        else:
            # Создаём новый заказ
            result = self.client.table("Orders").insert(transformed_data).execute()
            return result.data[0] if result.data else None
    
    def get_order(self, external_id: str) -> Optional[Dict[str, Any]]:
        """Получает заказ по external_id"""
        result = self.client.table("Orders").select("*").eq("external_id", external_id).execute()
        return result.data[0] if result.data else None

    def get_orders(self, limit: int = 50, offset: int = 0) -> list:
        """Получает список заказов"""
        result = self.client.table("Orders").select("*").range(offset, offset + limit - 1).order("created_at", desc=True).execute()
        return result.data

    def get_orders_by_status(self, status: str, limit: int = 50) -> list:
        """Получает заказы по статусу"""
        result = self.client.table("Orders").select("*").eq("status", status).limit(limit).order("created_at", desc=True).execute()
        return result.data

    def delete_order(self, external_id: str) -> bool:
        """Удаляет заказ"""
        result = self.client.table("Orders").delete().eq("external_id", external_id).execute()
        return len(result.data) > 0
