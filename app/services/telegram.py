from telegram import Bot
from telegram.error import TelegramError
from typing import Dict, Any
from datetime import datetime
from app.config import settings


class TelegramService:
    """Сервис для отправки уведомлений в Telegram"""
    
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
        else:
            self.bot = None
    
    async def send_order_notification(self, order_data: Dict[str, Any]) -> bool:
        """Отправляет уведомление о заказе в Telegram"""
        print(f"[TELEGRAM] Bot configured: {self.bot is not None}")
        print(f"[TELEGRAM] Chat ID: {self.chat_id}")

        if not self.bot or not self.chat_id:
            print("[TELEGRAM] Bot not configured - missing token or chat_id")
            return False

        try:
            # Формируем сообщение
            order_id = order_data.get("id") or order_data.get("externalId", "Не указан")
            status_raw = order_data.get("status", "new")
            # Переводим статус
            status_map = {
                "new": "Новый",
                "processing": "В обработке",
                "completed": "Выполнен",
                "cancelled": "Отменён"
            }
            status = status_map.get(status_raw, status_raw)

            first_name = order_data.get("firstName", "Не указано")
            last_name = order_data.get("lastName", "")

            # Рассчитываем сумму из items
            items = order_data.get("items", [])
            total_price = sum(item.get("quantity", 0) * item.get("initialPrice", 0) for item in items)

            # Используем текущую дату сервера
            created_at = datetime.now().strftime("%d.%m.%Y %H:%M")
            utm_source = order_data.get("customFields", {}).get("utm_source", "Не указан")
            order_type = order_data.get("orderType", "Не указан")
            order_method = order_data.get("orderMethod", "Не указан")
            delivery = order_data.get("delivery", {})
            address_raw = delivery.get("address", "Не указан")

            # Форматируем адрес
            if isinstance(address_raw, dict):
                city = address_raw.get("city", "")
                text = address_raw.get("text", "")
                address = f"г: {city}, {text}" if city and text else text or city or "Не указано"
            else:
                address = str(address_raw) if address_raw else "Не указано"

            # Формируем список товаров
            items_list = []
            for item in items[:5]:  # Показываем максимум 5 товаров
                product_name = item.get("productName", "Не указано")
                quantity = item.get("quantity", 1)
                price = item.get("initialPrice", 0)
                items_list.append(f"• {product_name} x{quantity} ({price} ₸)")
            items_text = "\n".join(items_list) if items_list else "Нет товаров"

            message = (
                f"🛒 Новый заказ\n"
                f"Номер: {order_id}\n\n"
                f"👤 Клиент: {first_name} {last_name}\n"
                f"📧 Email: {order_data.get('email', 'Не указан')}\n"
                f"📱 Телефон: {order_data.get('phone', 'Не указан')}\n"
                f"💰 Сумма: {total_price} тенге\n"
                f"📊 Статус: {status}\n"
                f"📅 Создан: {created_at}\n"
                f"Источник UTM: {utm_source}\n"
                f"Тип заказа: {order_type}\n"
                f"Метод заказа: {order_method}\n\n"
                f"📦 Товары:\n{items_text}\n\n"
                f"📍 Адрес: {address}"
            )

            print(f"[TELEGRAM] Отправка сообщения в chat_id={self.chat_id}")
            result = await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML"
            )

            print(f"[TELEGRAM] Успешно отправлено! Message ID: {result.message_id}")
            return True

        except TelegramError as e:
            print(f"[TELEGRAM] TelegramError: {e}")
            return False
        except Exception as e:
            print(f"[TELEGRAM] Unexpected error: {e}")
            return False
    
    def send_message(self, text: str) -> bool:
        """Отправляет простое текстовое сообщение"""
        if not self.bot or not self.chat_id:
            print("Telegram bot not configured")
            return False
        
        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=text
            )
            return True
            
        except TelegramError as e:
            print(f"Error sending Telegram message: {e}")
            return False
