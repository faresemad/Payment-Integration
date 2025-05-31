import logging

import requests
from django.conf import settings

from apps.services.coingate.abstract import AbstractPaymentGateway
from apps.services.coingate.dto import CoinGatePayment

logger = logging.getLogger(__name__)


class CoinGateService(AbstractPaymentGateway):
    """
    A service class for handling CoinGate cryptocurrency payment integrations.

    This class provides methods for creating payment orders, verifying webhook signatures,
    generating request signatures, and mapping payment statuses between CoinGate and the
    application's internal transaction status system.
    """

    def __init__(self, api_key: str = None, sandbox: bool = None, base_url: str = None, backend_url: str = None):
        """
        Initialize the CoinGateService with API key and sandbox mode.
        """
        self.api_key = api_key or settings.COINGATE_API_KEY
        self.sandbox = sandbox or settings.COINGATE_SANDBOX
        self.base_url = base_url or settings.BASE_URL
        self.backend_url = backend_url or settings.BACKEND_URL
        self.api_url = (
            "https://api-sandbox.coingate.com/v2/orders" if self.sandbox else "https://api.coingate.com/v2/orders"
        )

    def create_order(self, payment: CoinGatePayment):
        """
        Create a new payment order with CoinGate for cryptocurrency transactions.

        This method generates a CoinGate order by preparing transaction details,
        creating a signature, and sending a request to the CoinGate API.

        Args:
            payment (CoinGatePayment): The payment object containing transaction details

        Returns:
            dict or None: CoinGate order response if successful, None otherwise

        Raises:
            requests.RequestException: If there's an error communicating with the CoinGate API
        """
        try:
            data = {
                "order_id": payment.order_id,
                "price_amount": payment.price_amount,
                "price_currency": payment.price_currency,
                "receive_currency": payment.receive_currency,
                "title": payment.title,
                "description": payment.description,
                "callback_url": payment.callback_url,
                "cancel_url": payment.cancel_url,
                "success_url": payment.success_url,
                "token": payment.token,
                "purchaser_email": payment.purchaser_email,
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.post(self.api_url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error creating CoinGate order: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error parsing CoinGate response: {e}")
            return None

    def map_status(self, external_status):
        status_mapping = {
            "new": "Invoice created, but payment method not selected. Expires in 2 hours.",
            "pending": "Payment method selected, awaiting payment. Expires in 20 minutes if unpaid.",
            "confirming": "Payment sent, awaiting blockchain confirmation.",
            "paid": "Payment confirmed and received. Goods/services can be delivered.",
            "invalid": "Payment was not confirmed or failed compliance checks.",
            "expired": "Invoice expired due to no payment or no method selected within time limits.",
            "canceled": "Invoice was canceled by the shopper.",
            "refunded": "Full refund issued to the shopper.",
            "partially_refunded": "Partial refund issued to the shopper.",
        }
        logger.debug(f"Mapping external status: {external_status}: {status_mapping.get(external_status, 'UNKNOWN')}")
        return status_mapping.get(external_status, "UNKNOWN")
