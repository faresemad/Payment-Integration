"""
Concrete Implementations
Single Responsibility: Implement abstract classes for Stripe
"""

import hashlib
import hmac
import json
import logging
import time

import stripe

from apps.services.stripe.abstracts import (
    ApiClient,
    HttpClient,
    InvoiceProcessor,
    SignatureValidator,
    WebhookValidator,
)
from apps.services.stripe.dto import InvoiceRequest


class StripeSignatureValidator(SignatureValidator):
    """Stripe signature validator implementation"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def verify_webhook_signature(self, payload: bytes, signature: str, endpoint_secret: str) -> bool:
        """Verify Stripe webhook signature"""
        self.logger.info("Verifying webhook signature")
        
        try:
            # Parse signature header
            elements = signature.split(',')
            timestamp = None
            signatures = []
            
            for element in elements:
                key, value = element.split('=', 1)
                if key == 't':
                    timestamp = int(value)
                elif key.startswith('v'):
                    signatures.append(value)
            
            if not timestamp or not signatures:
                self.logger.error("Invalid signature format")
                return False
            
            # Check timestamp (reject if older than 5 minutes)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:
                self.logger.error("Timestamp too old")
                return False
            
            # Generate expected signature
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_signature = hmac.new(
                endpoint_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            for signature in signatures:
                if hmac.compare_digest(expected_signature, signature):
                    self.logger.info("Signature verification successful")
                    return True
            
            self.logger.warning("Signature verification failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Signature verification error: {str(e)}")
            return False


class StripeHttpClient(HttpClient):
    """HTTP client using stripe library"""

    def __init__(self, api_key: str):
        stripe.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def post(self, url: str, data: dict, headers: dict[str, str]) -> dict:
        """Not used directly - Stripe SDK handles HTTP"""
        raise NotImplementedError("Use Stripe SDK methods directly")

    def get(self, url: str, headers: dict[str, str]) -> dict:
        """Not used directly - Stripe SDK handles HTTP"""
        raise NotImplementedError("Use Stripe SDK methods directly")


class StripeApiClient(ApiClient):
    """Stripe API client implementation"""

    def __init__(self, api_key: str):
        stripe.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def make_request(self, method: str, endpoint: str, data: dict | None = None) -> dict:
        """Make API request to Stripe using SDK"""
        self.logger.info(f"Making {method} request to: {endpoint}")
        
        try:
            if method.upper() == "POST" and endpoint == "invoices":
                return stripe.Invoice.create(**data)
            elif method.upper() == "GET" and endpoint.startswith("invoices/"):
                invoice_id = endpoint.split("/")[1]
                return stripe.Invoice.retrieve(invoice_id)
            elif method.upper() == "POST" and endpoint.endswith("/send"):
                invoice_id = endpoint.split("/")[1]
                invoice = stripe.Invoice.retrieve(invoice_id)
                return invoice.send_invoice()
            elif method.upper() == "POST" and endpoint.endswith("/finalize"):
                invoice_id = endpoint.split("/")[1]
                invoice = stripe.Invoice.retrieve(invoice_id)
                return invoice.finalize_invoice()
            else:
                raise ValueError(f"Unsupported endpoint: {endpoint}")
                
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe API error: {str(e)}")
            raise


class StripeInvoiceProcessor(InvoiceProcessor):
    """Stripe invoice processor implementation"""

    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def create_invoice(self, request: InvoiceRequest) -> dict:
        """Create invoice using Stripe API"""
        self.logger.info(f"Creating invoice for customer: {request.customer_email}")
        
        try:
            # First, create or get customer
            customer = self._get_or_create_customer(request.customer_email)
            
            # Create invoice
            invoice_data = request.to_dict()
            invoice_data["customer"] = customer.id
            
            # Create invoice items first
            for line_item in request.line_items:
                stripe.InvoiceItem.create(
                    customer=customer.id,
                    **line_item.to_dict()
                )
            
            # Create the invoice
            return self.api_client.make_request("POST", "invoices", invoice_data)
            
        except Exception as e:
            self.logger.error(f"Invoice creation failed: {str(e)}")
            raise

    def get_invoice(self, invoice_id: str) -> dict:
        """Get invoice details using Stripe API"""
        self.logger.info(f"Retrieving invoice: {invoice_id}")
        return self.api_client.make_request("GET", f"invoices/{invoice_id}")

    def send_invoice(self, invoice_id: str) -> dict:
        """Send invoice to customer"""
        self.logger.info(f"Sending invoice: {invoice_id}")
        return self.api_client.make_request("POST", f"invoices/{invoice_id}/send")

    def finalize_invoice(self, invoice_id: str) -> dict:
        """Finalize invoice"""
        self.logger.info(f"Finalizing invoice: {invoice_id}")
        return self.api_client.make_request("POST", f"invoices/{invoice_id}/finalize")

    def _get_or_create_customer(self, email: str):
        """Get existing customer or create new one"""
        try:
            # Try to find existing customer
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                return customers.data[0]
            
            # Create new customer
            return stripe.Customer.create(email=email)
            
        except stripe.error.StripeError as e:
            self.logger.error(f"Customer creation/retrieval failed: {str(e)}")
            raise


class StripeWebhookValidator(WebhookValidator):
    """Stripe webhook validator implementation"""

    def __init__(self, signature_validator: SignatureValidator):
        self.signature_validator = signature_validator
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def validate_webhook(self, payload: bytes, signature: str, endpoint_secret: str) -> bool:
        """Validate webhook signature"""
        return self.signature_validator.verify_webhook_signature(payload, signature, endpoint_secret)
