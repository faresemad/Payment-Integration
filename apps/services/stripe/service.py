"""
Main Service Class
Single Responsibility: Orchestrate operations between processors
"""

import json
import logging

from django.conf import settings

from apps.services.stripe.dto import InvoiceLineItem, InvoiceRequest
from apps.services.stripe.implementations import (StripeApiClient,
                                                  StripeInvoiceProcessor,
                                                  StripeSignatureValidator,
                                                  StripeWebhookValidator)


class StripeService:
    """
    Main Stripe service - orchestrates all operations
    Single responsibility: Coordinate between different processors
    """

    def __init__(
        self,
        api_key: str | None = None,
        webhook_secret: str | None = None,
    ):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("Initializing StripeService")

        # Get configuration
        self.api_key = api_key or settings.STRIPE_API_KEY
        self.webhook_secret = webhook_secret or settings.STRIPE_WEBHOOK_SECRET

        # Initialize components
        self._signature_validator = StripeSignatureValidator()
        self._api_client = StripeApiClient(self.api_key)

        # Initialize processors
        self._invoice_processor = StripeInvoiceProcessor(self._api_client)
        self._webhook_validator = StripeWebhookValidator(self._signature_validator)

    # Invoice operations
    def create_invoice(
        self,
        customer_email: str,
        line_items: list[dict],
        currency: str = "usd",
        description: str | None = None,
        metadata: dict[str, str] | None = None,
        auto_advance: bool = True,
        days_until_due: int = 30,
    ) -> dict:
        """Create a new invoice"""
        
        # Convert line items to InvoiceLineItem objects
        invoice_line_items = []
        for item in line_items:
            line_item = InvoiceLineItem(
                price_data=item["price_data"],
                quantity=item.get("quantity", 1)
            )
            invoice_line_items.append(line_item)
        
        invoice_request = InvoiceRequest(
            customer_email=customer_email,
            line_items=invoice_line_items,
            currency=currency,
            description=description,
            metadata=metadata,
            auto_advance=auto_advance,
            days_until_due=days_until_due,
        )
        
        return self._invoice_processor.create_invoice(invoice_request)

    def get_invoice(self, invoice_id: str) -> dict:
        """Get invoice details"""
        return self._invoice_processor.get_invoice(invoice_id)

    def send_invoice(self, invoice_id: str) -> dict:
        """Send invoice to customer"""
        return self._invoice_processor.send_invoice(invoice_id)

    def finalize_invoice(self, invoice_id: str) -> dict:
        """Finalize invoice (make it ready for payment)"""
        return self._invoice_processor.finalize_invoice(invoice_id)

    # Webhook operations
    def verify_webhook_signature(self, payload: bytes, signature: str, endpoint_secret: str | None = None) -> bool:
        """Verify webhook signature for security"""
        secret = endpoint_secret or self.webhook_secret
        return self._webhook_validator.validate_webhook(payload, signature, secret)

    def process_webhook(self, payload: bytes, signature: str, endpoint_secret: str | None = None) -> dict | None:
        """Process webhook and return event data if valid"""
        if not self.verify_webhook_signature(payload, signature, endpoint_secret):
            self.logger.warning("Invalid webhook signature")
            return None
        
        try:
            event_data = json.loads(payload.decode('utf-8'))
            self.logger.info(f"Processing webhook event: {event_data.get('type')}")
            return event_data
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in webhook payload: {str(e)}")
            return None
