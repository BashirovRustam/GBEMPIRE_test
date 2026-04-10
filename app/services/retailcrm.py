import httpx
from typing import Optional, Dict, Any
from app.config import settings


class RetailCRMService:
    """Клиент для работы с RetailCRM API"""
    
    def __init__(self):
        self.api_url = settings.retailcrm_api_url
        self.api_key = settings.retailcrm_api_key
        self.timeout = 30.0
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Получает заказ по ID"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.api_url}/orders/{order_id}",
                    params={"apiKey": self.api_key}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("order")
                return None
                
            except Exception as e:
                print(f"Error fetching order {order_id}: {e}")
                return None
    
    async def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Создает новый заказ в RetailCRM"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/orders/create",
                    params={"apiKey": self.api_key},
                    json={"order": order_data}
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
            except Exception as e:
                print(f"Error creating order: {e}")
                return None
    
    async def update_order(self, order_id: str, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновляет заказ в RetailCRM"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/orders/{order_id}/edit",
                    params={"apiKey": self.api_key},
                    json={"order": order_data}
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
            except Exception as e:
                print(f"Error updating order {order_id}: {e}")
                return None
    
    async def get_orders(self, limit: int = 50, page: int = 1) -> list:
        """Получает список заказов"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.api_url}/orders",
                    params={
                        "apiKey": self.api_key,
                        "limit": limit,
                        "page": page
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("orders", [])
                return []
                
            except Exception as e:
                print(f"Error fetching orders: {e}")
                return []
