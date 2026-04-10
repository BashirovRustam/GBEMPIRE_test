from telegram import Bot
from telegram.error import TelegramError
from typing import Dict, Any
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
    
    def send_order_notification(self, order_data: Dict[str, Any]) -> bool:
        """Отправляет уведомление о заказе в Telegram"""
        if not self.bot or not self.chat_id:
            print("Telegram bot not configured")
            return False
        
        try:
            # Формируем сообщение
            order_id = order_data.get("id") or order_data.get("externalId")
            status = order_data.get("status", "unknown")
            first_name = order_data.get("firstName", "Не указано")
            last_name = order_data.get("lastName", "")
            total_price = order_data.get("sum", 0)
            
            message = (
                f"🛒 <b>Новый заказ #{order_id}</b>\n\n"
                f"👤 Клиент: {first_name} {last_name}\n"
                f"📧 Email: {order_data.get('email', 'Не указан')}\n"
                f"📱 Телефон: {order_data.get('phone', 'Не указан')}\n"
                f"💰 Сумма: {total_price} ₽\n"
                f"📊 Статус: {status}\n"
                f"📅 Создан: {order_data.get('createdAt', 'Не указано')}\n\n"
                f"🚚 Доставка: {order_data.get('delivery', {}).get('type', 'Не указан')}\n"
                f"📍 Адрес: {order_data.get('delivery', {}).get('address', 'Не указан')}"
            )
            
            self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML"
            )
            
            print(f"Telegram notification sent for order {order_id}")
            return True
            
        except TelegramError as e:
            print(f"Error sending Telegram notification: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending Telegram notification: {e}")
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
