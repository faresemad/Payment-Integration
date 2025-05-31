"""
Abstract Base Classes
Single Responsibility: Define contracts/interfaces
"""

from abc import ABC, abstractmethod

from apps.services.stripe.dto import InvoiceRequest


class SignatureValidator(ABC):
    """Abstract signature validator"""

    @abstractmethod
    def verify_webhook_signature(self, payload: bytes, signature: str, endpoint_secret: str) -> bool:
        """Verify webhook signature"""
        pass


class HttpClient(ABC):
    """Abstract HTTP client"""

    @abstractmethod
    def post(self, url: str, data: dict, headers: dict[str, str]) -> dict:
        """Send POST request"""
        pass

    @abstractmethod
    def get(self, url: str, headers: dict[str, str]) -> dict:
        """Send GET request"""
        pass


class InvoiceProcessor(ABC):
    """Abstract invoice processor"""

    @abstractmethod
    def create_invoice(self, request: InvoiceRequest) -> dict:
        """Create invoice"""
        pass

    @abstractmethod
    def get_invoice(self, invoice_id: str) -> dict:
        """Get invoice details"""
        pass

    @abstractmethod
    def send_invoice(self, invoice_id: str) -> dict:
        """Send invoice to customer"""
        pass

    @abstractmethod
    def finalize_invoice(self, invoice_id: str) -> dict:
        """Finalize invoice"""
        pass


class WebhookValidator(ABC):
    """Abstract webhook validator"""

    @abstractmethod
    def validate_webhook(self, payload: bytes, signature: str, endpoint_secret: str) -> bool:
        """Validate webhook"""
        pass


class ApiClient(ABC):
    """Abstract API client"""

    @abstractmethod
    def make_request(self, method: str, endpoint: str, data: dict | None = None) -> dict:
        """Make API request"""
        pass
