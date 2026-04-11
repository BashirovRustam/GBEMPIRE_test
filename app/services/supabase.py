import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from app.config import settings


class SupabaseService:
    def __init__(self):
        if not settings.supabase_url:
            raise ValueError("SUPABASE_URL not configured")

        self.url = settings.supabase_url
        self.key = settings.supabase_service_role_key or settings.supabase_anon_key
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def get_orders(self, limit: int = 1000, offset: int = 0) -> list:
        with httpx.Client() as client:
            response = client.get(
                f"{self.url}/rest/v1/Orders",
                headers=self.headers,
                params={"select": "*", "limit": limit, "offset": offset, "order": "created_at.desc"}
            )
            response.raise_for_status()
            return response.json()

    def save_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        external_id = order_data.get("id") or order_data.get("externalId")
        if not external_id:
            raise ValueError("Order must have id or externalId")

        transformed = {
            "external_id": external_id,
            "first_name": order_data.get("firstName"),
            "last_name": order_data.get("lastName"),
            "email": order_data.get("email"),
            "phone": order_data.get("phone"),
            "status": order_data.get("status"),
            "total_price": order_data.get("sum", 0),
            "created_at": order_data.get("createdAt"),
            "synced_at": datetime.utcnow().isoformat(),
            "raw_data": order_data,
        }

        with httpx.Client() as client:
            response = client.post(
                f"{self.url}/rest/v1/Orders",
                headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                json=transformed
            )
            response.raise_for_status()
            return transformed

    def get_order(self, external_id: str) -> Optional[Dict[str, Any]]:
        with httpx.Client() as client:
            response = client.get(
                f"{self.url}/rest/v1/Orders",
                headers=self.headers,
                params={"external_id": f"eq.{external_id}", "select": "*"}
            )
            response.raise_for_status()
            data = response.json()
            return data[0] if data else None