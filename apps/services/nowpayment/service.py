from apps.services.nowpayment.implementations import NowPaymentServiceImpl


class NowPaymentService:
    def __init__(self, implementation=None):
        self.implementation = implementation or NowPaymentServiceImpl()

    def create_invoice(self, invoice_data):
        return self.implementation.create_invoice(invoice_data)

    def verify_webhook(self, webhook_data):
        return self.implementation.verify_webhook(webhook_data)
