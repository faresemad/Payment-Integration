from abc import ABC, abstractmethod

from apps.services.nowpayment.dto import CreateInvoiceDto, ResponseInvoiceDto, WebhookDto


class NowPaymentAbstract(ABC):
    @abstractmethod
    def create_invoice(self, dto: CreateInvoiceDto) -> ResponseInvoiceDto:
        pass

    @abstractmethod
    def verify_webhook(self, dto: WebhookDto) -> str:
        pass
