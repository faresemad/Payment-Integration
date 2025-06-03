from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class CreateInvoiceDto:
    """
    Data transfer object (DTO) representing the parameters for creating a new invoice in the NowPayments payment system.

    Attributes:
        price_amount (float): The total amount to be paid.
        price_currency (str): The currency of the payment.
        order_id (str): Unique identifier for the order.
        order_description (Optional[str], optional): Description of the order. Defaults to None.
        ipn_callback_url (str): Instant Payment Notification (IPN) callback URL.
        success_url (str): URL to redirect after successful payment.
        cancel_url (str): URL to redirect if payment is cancelled.
        partially_paid_url (Optional[str], optional): URL for partially paid invoices. Defaults to None.
        is_fixed_rate (Optional[bool], optional): Flag for fixed rate pricing. Defaults to None.
        is_fee_paid_by_user (Optional[bool], optional): Flag indicating who pays the transaction fees. Defaults to None.
    """
    price_amount: float
    price_currency: str
    order_id: str
    order_description: Optional[str] = None
    ipn_callback_url: str
    success_url: str
    cancel_url: str
    partially_paid_url: Optional[str] = None
    is_fixed_rate: Optional[bool] = None
    is_fee_paid_by_user: Optional[bool] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class ResponseInvoiceDto:
    """
    Data transfer object (DTO) representing the response from creating an invoice in the NowPayments payment system.

    Attributes:
        payment_id (str): Unique identifier for the created payment.
        payment_url (str): URL for the payment transaction.
    """
    payment_id: str
    payment_url: str

    def to_dict(self):
        return asdict(self)


@dataclass
class WebhookDto:
    """
    Data transfer object (DTO) representing a webhook payload from the NowPayments payment system.

    Attributes:
        payment_id (str): Unique identifier for the payment.
        payment_status (str): Current status of the payment transaction.
    """
    payment_id: str
    payment_status: str

    def to_dict(self):
        return asdict(self)
