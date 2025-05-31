"""
Data Transfer Objects
Single Responsibility: Handle data structures
"""

from dataclasses import dataclass


@dataclass
class PaymentRequest:
    """Payment request data"""

    amount: float
    currency: str
    order_id: str
    lifetime: int = 15 * 60
    additional_params: dict | None = None

    def to_dict(self) -> dict:
        result = {
            "amount": str(self.amount),
            "currency": self.currency,
            "order_id": self.order_id,
            "lifetime": self.lifetime,
        }
        if self.additional_params:
            result.update(self.additional_params)
        return result


@dataclass
class PayoutRequest:
    """Payout request data"""

    amount: float
    currency: str
    to_wallet: str
    network: str | None = None
    order_id: str | None = None

    def to_dict(self) -> dict:
        result = {"amount": str(self.amount), "currency": self.currency, "to": self.to_wallet}
        if self.network:
            result["network"] = self.network
        if self.order_id:
            result["order_id"] = self.order_id
        return result
