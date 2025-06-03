import logging

import requests
from django.conf import settings
from requests.exceptions import RequestException

from apps.services.nowpayment.abstract import NowPaymentAbstract
from apps.services.nowpayment.exceptions import NowPaymentsAPIError

logger = logging.getLogger(__name__)


class NowPaymentServiceImpl(NowPaymentAbstract):
    DEFAULT_API_URL = "https://api-sandbox.nowpayments.io/v1"
    PAYMENT_URL_TEMPLATE = "https://nowpayments.io/payment/?iid={}"
    QR_CODE_URL_TEMPLATE = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={}"

    def __init__(self):
        self.api_key = getattr(settings, "NOWPAYMENTS_API_KEY", None)
        self.api_url = getattr(settings, "NOWPAYMENTS_API_URL", self.DEFAULT_API_URL)
        if not self.api_key:
            raise ValueError("NOWPAYMENTS_API_KEY is not set in settings.")

    def _get_headers(self) -> dict[str, str]:
        return {"x-api-key": self.api_key, "Content-Type": "application/json"}

    def _get_payment_url(self, payment_id: str) -> str:
        return self.PAYMENT_URL_TEMPLATE.format(payment_id)

    def _get_qr_code_url(self, payment_url: str) -> str:
        return self.QR_CODE_URL_TEMPLATE.format(payment_url)

    def create_invoice(self, dto):
        url = f"{self.api_url}/payment"
        try:
            response = requests.post(url, json=dto, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            response_data = response.json()

            payment_id = response_data.get("payment_id")
            if not payment_id:
                raise NowPaymentsAPIError("Payment ID not found in response")

            payment_url = self._get_payment_url(payment_id)
            qr_code_url = self._get_qr_code_url(payment_url)

            response_data.update({"payment_url": payment_url, "qr_code_url": qr_code_url})

            return response_data
        except RequestException as e:
            logger.error("NowPayments API request failed", exc_info=e)
            if e.response is not None:
                logger.error("Response content: %s", e.response.text)
            raise NowPaymentsAPIError("Failed to create payment")

    def verify_webhook(self, dto):
        if not dto.payment_id or not dto.payment_status:
            logger.warning("Invalid webhook payload received: %s", dto)
            return {"error": "Invalid webhook data"}
        status_map = {
            "waiting": "waiting for paying",
            "confirming": "confirming checkout",
            "finished": "payed successfully",
            "expired": "checkout expired",
            "failed": "checkout faild",
            "refunded": "amount refunded",
        }
        return status_map.get(dto.payment_status.lower())
