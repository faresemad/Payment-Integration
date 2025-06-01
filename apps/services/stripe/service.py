from apps.services.stripe.dto import CheckoutSessionResponseDTO
from apps.services.stripe.implementations import StripePaymentServiceImpl


class StripeService:
    def __init__(self, implementation=None):
        self.implementation = implementation or StripePaymentServiceImpl()

    def get_or_create_tax_rate(self, tax_dto) -> str:
        return self.implementation.get_or_create_tax_rate(tax_dto)

    def create_checkout_session(self, request_dto) -> CheckoutSessionResponseDTO:
        return self.implementation.create_checkout_session(request_dto)

    def handle_webhook(self, webhook_dto) -> bool:
        return self.implementation.handle_webhook_event(webhook_dto)
