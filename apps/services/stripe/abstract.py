from abc import ABC, abstractmethod

from apps.services.stripe.dto import CheckoutSessionRequestDTO, CheckoutSessionResponseDTO, StripeTax, WebhookEventDTO


class AbstractPaymentService(ABC):
    @abstractmethod
    def get_or_create_tax_rate(self, dto: StripeTax) -> str:
        pass

    @abstractmethod
    def create_checkout_session(self, dto: CheckoutSessionRequestDTO) -> CheckoutSessionResponseDTO:
        pass

    @abstractmethod
    def handle_webhook_event(self, dto: WebhookEventDTO) -> bool:
        pass
