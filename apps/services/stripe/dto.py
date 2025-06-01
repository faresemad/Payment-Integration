from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class StripeTax:
    display_name: str
    percentage: float
    inclusive: bool
    description: Optional[str] = None
    jurisdiction: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "display_name": self.display_name,
            "percentage": self.percentage,
            "inclusive": self.inclusive,
            "description": self.description,
            "jurisdiction": self.jurisdiction,
        }


@dataclass
class CheckoutItemDTO:
    name: str
    price: int
    description: Optional[str] = None
    quantity: int = 1
    tax_rates: Optional[List[str]] = None
    price_data: Optional[Dict[str, Any]] = None
    tax_behavior: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
        }

        if self.description is not None:
            data["description"] = self.description
        if self.tax_rates is not None:
            data["tax_rates"] = self.tax_rates.copy()
        if self.price_data is not None:
            data["price_data"] = self.price_data.copy()
        if self.tax_behavior is not None:
            data["tax_behavior"] = self.tax_behavior

        return data


@dataclass
class CheckoutSessionRequestDTO:
    order_id: str
    payment_method_types: List[str]
    line_items: List[CheckoutItemDTO]
    mode: str
    payment_intent_data: Dict[str, Any]
    success_url: str
    cancel_url: str
    metadata: Optional[Dict[str, Any]] = None
    expires_at: Optional[int] = None
    client_reference_id: Optional[str] = None
    tax_id_collection: Optional[Dict[str, Any]] = None
    automatic_tax: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "order_id": self.order_id,
            "payment_method_types": self.payment_method_types.copy(),
            "line_items": [item.to_dict() for item in self.line_items],
            "mode": self.mode,
            "payment_intent_data": self.payment_intent_data.copy(),
            "success_url": self.success_url,
            "cancel_url": self.cancel_url,
            "automatic_tax": self.automatic_tax,
        }

        if self.metadata is not None:
            data["metadata"] = self.metadata.copy()
        if self.expires_at is not None:
            data["expires_at"] = self.expires_at
        if self.client_reference_id is not None:
            data["client_reference_id"] = self.client_reference_id
        if self.tax_id_collection is not None:
            data["tax_id_collection"] = self.tax_id_collection.copy()

        return data


@dataclass
class CheckoutSessionResponseDTO:
    session_id: str
    payment_url: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "payment_url": self.payment_url,
        }


@dataclass
class WebhookEventDTO:
    event_type: str
    payload: Dict[str, Any]
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": self.payload.copy(),
            "signature": self.signature,
        }
