from dataclasses import dataclass
from typing import Optional


@dataclass
class CoinGatePayment:
    """Data transfer object for CoinGate payment details.
    This class encapsulates the necessary information to create a payment order
    with CoinGate, including order ID, price, currency, and optional fields for
    title, description, callback URLs, token, and purchaser email.
    Attributes:
        order_id (str): Unique identifier for the order.
        price_amount (float): Amount to be paid.
        price_currency (str): Currency of the payment amount.
        receive_currency (str): Cryptocurrency to be received.
        title (Optional[str]): Title of the payment order.
        description (Optional[str]): Description of the payment order.
        callback_url (Optional[str]): URL for CoinGate to call back after payment.
        cancel_url (Optional[str]): URL to redirect to if the payment is cancelled.
        success_url (Optional[str]): URL to redirect to after successful payment.
        token (Optional[str]): Optional token for additional security.
        purchaser_email (Optional[str]): Email of the purchaser for notifications.
    """
    order_id: str
    price_amount: float
    price_currency: str
    receive_currency: str
    title: Optional[str] = None
    description: Optional[str] = None
    callback_url: Optional[str] = None
    cancel_url: Optional[str] = None
    success_url: Optional[str] = None
    token: Optional[str] = None
    purchaser_email: Optional[str] = None
