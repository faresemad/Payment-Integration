"""
Abstract Base Classes
Single Responsibility: Define contracts/interfaces
"""

from abc import ABC, abstractmethod

from ..cryptomus.dto import PaymentRequest, PayoutRequest


class SignatureGenerator(ABC):
    """Abstract signature generator"""

    @abstractmethod
    def generate_request_signature(self, payload: dict) -> str:
        """Generate signature for API requests"""
        pass

    @abstractmethod
    def verify_webhook_signature(self, data: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        pass


class HttpClient(ABC):
    """Abstract HTTP client"""

    @abstractmethod
    def post(self, url: str, data: str, headers: dict[str, str]) -> dict:
        """Send POST request"""
        pass


class PaymentProcessor(ABC):
    """Abstract payment processor"""

    @abstractmethod
    def create_payment(self, request: PaymentRequest) -> dict:
        """Create payment"""
        pass

    @abstractmethod
    def get_payment_status(self, payment_uuid: str) -> dict:
        """Get payment status"""
        pass


class PayoutProcessor(ABC):
    """Abstract payout processor"""

    @abstractmethod
    def create_payout(self, request: PayoutRequest) -> dict:
        """Create payout"""
        pass

    @abstractmethod
    def get_payout_status(self, payout_uuid: str) -> dict:
        """Get payout status"""
        pass


class WebhookValidator(ABC):
    """Abstract webhook validator"""

    @abstractmethod
    def validate_webhook(self, data: bytes, signature: str) -> bool:
        """Validate webhook"""
        pass


class ApiClient(ABC):
    """Abstract API client"""

    @abstractmethod
    def make_request(self, endpoint: str, payload: dict) -> dict:
        """Make API request"""
        pass
