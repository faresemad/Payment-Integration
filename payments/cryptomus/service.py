"""
Main Service Class
Single Responsibility: Orchestrate operations between processors
"""

import logging

from django.conf import settings

from ..cryptomus.dto import PaymentRequest, PayoutRequest
from ..cryptomus.implementations import (
    CryptomusApiClient,
    CryptomusPaymentProcessor,
    CryptomusPayoutProcessor,
    CryptomusSignatureGenerator,
    CryptomusWebhookValidator,
    RequestsHttpClient,
)


class CryptomusService:
    """
    Main Cryptomus service - orchestrates all operations
    Single responsibility: Coordinate between different processors
    """

    def __init__(
        self,
        api_key: str | None = None,
        merchant_id: str | None = None,
        base_url: str = "https://api.cryptomus.com/v1",
    ):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Initializing CryptomusService")

        # Get configuration
        self.api_key = api_key or settings.CRYPTOMUS_API_KEY
        self.merchant_id = merchant_id or settings.CRYPTOMUS_MERCHANT_ID
        self.base_url = base_url

        # Initialize components
        self._signature_generator = CryptomusSignatureGenerator(self.api_key)
        self._http_client = RequestsHttpClient()
        self._api_client = CryptomusApiClient(
            self.base_url, self.merchant_id, self._signature_generator, self._http_client
        )

        # Initialize processors
        self._payment_processor = CryptomusPaymentProcessor(self._api_client)
        self._payout_processor = CryptomusPayoutProcessor(self._api_client)
        self._webhook_validator = CryptomusWebhookValidator(self._signature_generator)

    # Payment operations
    def create_payment(self, amount: float, currency: str, order_id: str, lifetime: int = 15 * 60, **kwargs) -> dict:
        """Create a new payment request"""
        payment_request = PaymentRequest(
            amount=amount,
            currency=currency,
            order_id=order_id,
            lifetime=lifetime,
            additional_params=kwargs if kwargs else None,
        )
        return self._payment_processor.create_payment(payment_request)

    def get_payment_status(self, payment_uuid: str) -> dict:
        """Check payment status using payment UUID"""
        return self._payment_processor.get_payment_status(payment_uuid)

    # Payout operations
    def create_payout(
        self, amount: float, currency: str, to_wallet: str, network: str | None = None, order_id: str | None = None
    ) -> dict:
        """Create a payout request to user's wallet"""
        payout_request = PayoutRequest(
            amount=amount, currency=currency, to_wallet=to_wallet, network=network, order_id=order_id
        )
        return self._payout_processor.create_payout(payout_request)

    def get_payout_status(self, payout_uuid: str) -> dict:
        """Check payout status using payout UUID"""
        return self._payout_processor.get_payout_status(payout_uuid)

    # Webhook operations
    def verify_signature(self, request_body: bytes, provided_signature: str) -> bool:
        """Verify webhook signature for security"""
        return self._webhook_validator.validate_webhook(request_body, provided_signature)
