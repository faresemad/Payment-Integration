import logging

import requests
from apps.orders.models import Transaction
from apps.services.coingate.abstract import AbstractPaymentGateway
from apps.services.coingate.dto import CreateOrderDTO
from django.conf import settings

logger = logging.getLogger(__name__)


class CoinGateGateway(AbstractPaymentGateway):
    def __init__(self):
        self.api_key = settings.COINGATE_API_KEY
        self.sandbox = settings.COINGATE_SANDBOX
        self.base_url = settings.BASE_URL
        self.backend_url = settings.BACKEND_URL
        self.api_url = (
            "https://api-sandbox.coingate.com/v2/orders"
            if self.sandbox
            else "https://api.coingate.com/v2/orders"
        )

    def create_order(self, order_data: CreateOrderDTO) -> dict:
        try:
            data = {
                "order_id": order_data.order_id,
                "price_amount": order_data.price_amount,
                "price_currency": order_data.price_currency,
                "receive_currency": order_data.receive_currency,
                "callback_url": order_data.callback_url,
                "cancel_url": order_data.cancel_url,
                "success_url": order_data.success_url,
                "title": order_data.title,
                "description": order_data.description,
            }

            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.post(self.api_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()

            logger.info(f"Created CoinGate order #{order_data.order_id}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"CoinGate API Error: {str(e)}")
            if hasattr(e.response, "text"):
                logger.error(f"CoinGate Error Details: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in CoinGate order: {str(e)}")
            return None

    def map_status(self, external_status: str):
        status_mapping = {
            "paid": Transaction.PaymentStatus.COMPLETED,
            "confirmed": Transaction.PaymentStatus.COMPLETED,
            "pending": Transaction.PaymentStatus.PENDING,
            "invalid": Transaction.PaymentStatus.FAILED,
            "expired": Transaction.PaymentStatus.FAILED,
            "canceled": Transaction.PaymentStatus.FAILED,
        }
        return status_mapping.get(external_status, Transaction.PaymentStatus.FAILED)
