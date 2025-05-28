"""
Concrete Implementations
Single Responsibility: Implement abstract classes for Cryptomus
"""

import base64
import hashlib
import hmac
import json
import logging

import requests

from ..cryptomus.abstracts import (
    ApiClient,
    HttpClient,
    PaymentProcessor,
    PayoutProcessor,
    SignatureGenerator,
    WebhookValidator,
)
from ..cryptomus.dto import PaymentRequest, PayoutRequest


class CryptomusSignatureGenerator(SignatureGenerator):
    """Cryptomus signature generator implementation"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def generate_request_signature(self, payload: dict) -> str:
        """Generate MD5 signature for API requests"""
        self.logger.debug(f"Generating signature for payload: {payload}")
        payload_str = json.dumps(payload, separators=(",", ":"))
        base64_data = base64.b64encode(payload_str.encode("utf-8")).decode("utf-8")
        signature = hashlib.md5((base64_data + self.api_key).encode("utf-8")).hexdigest()
        self.logger.debug("Signature generated successfully")
        return signature

    def verify_webhook_signature(self, data: bytes, signature: str) -> bool:
        """Verify HMAC signature for webhooks"""
        self.logger.info("Verifying webhook signature")
        generated_signature = hmac.new(key=self.api_key.encode(), msg=data, digestmod=hashlib.sha256).hexdigest()
        is_valid = hmac.compare_digest(generated_signature, signature)
        self.logger.info(f"Signature verification result: {is_valid}")
        return is_valid


class RequestsHttpClient(HttpClient):
    """HTTP client using requests library"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def post(self, url: str, data: str, headers: dict[str, str]) -> dict:
        """Send POST request using requests"""
        self.logger.info(f"Making POST request to: {url}")

        try:
            response = requests.post(url, data=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            self.logger.debug(f"Response received: {result}")
            return result
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request failed: {str(e)}")
            raise


class CryptomusApiClient(ApiClient):
    """Cryptomus API client implementation"""

    def __init__(
        self, base_url: str, merchant_id: str, signature_generator: SignatureGenerator, http_client: HttpClient
    ):
        self.base_url = base_url
        self.merchant_id = merchant_id
        self.signature_generator = signature_generator
        self.http_client = http_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def make_request(self, endpoint: str, payload: dict) -> dict:
        """Make API request to Cryptomus"""
        self.logger.info(f"Making API request to endpoint: {endpoint}")

        url = f"{self.base_url}/{endpoint}"
        data_json = json.dumps(payload, separators=(",", ":"))

        headers = {
            "merchant": self.merchant_id,
            "sign": self.signature_generator.generate_request_signature(payload),
            "Content-Type": "application/json",
        }

        return self.http_client.post(url, data_json, headers)


class CryptomusPaymentProcessor(PaymentProcessor):
    """Cryptomus payment processor implementation"""

    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def create_payment(self, request: PaymentRequest) -> dict:
        """Create payment using Cryptomus API"""
        self.logger.info(f"Creating payment: amount={request.amount}, currency={request.currency}")
        return self.api_client.make_request("payment", request.to_dict())

    def get_payment_status(self, payment_uuid: str) -> dict:
        """Get payment status using Cryptomus API"""
        self.logger.info(f"Checking payment status for UUID: {payment_uuid}")
        return self.api_client.make_request("payment/info", {"uuid": payment_uuid})


class CryptomusPayoutProcessor(PayoutProcessor):
    """Cryptomus payout processor implementation"""

    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def create_payout(self, request: PayoutRequest) -> dict:
        """Create payout using Cryptomus API"""
        self.logger.info(f"Creating payout: amount={request.amount}, currency={request.currency}")
        return self.api_client.make_request("payout", request.to_dict())

    def get_payout_status(self, payout_uuid: str) -> dict:
        """Get payout status using Cryptomus API"""
        self.logger.info(f"Checking payout status for UUID: {payout_uuid}")
        return self.api_client.make_request("payout/info", {"uuid": payout_uuid})


class CryptomusWebhookValidator(WebhookValidator):
    """Cryptomus webhook validator implementation"""

    def __init__(self, signature_generator: SignatureGenerator):
        self.signature_generator = signature_generator
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def validate_webhook(self, data: bytes, signature: str) -> bool:
        """Validate webhook signature"""
        return self.signature_generator.verify_webhook_signature(data, signature)
