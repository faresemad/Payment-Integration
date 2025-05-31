# payment/dto.py
from dataclasses import dataclass


@dataclass
class CreateOrderDTO:
    order_id: str
    price_amount: float
    price_currency: str
    receive_currency: str
    callback_url: str
    cancel_url: str
    success_url: str
    title: str
    description: str
