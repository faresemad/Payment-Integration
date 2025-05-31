"""
Data Transfer Objects
Single Responsibility: Handle data structures
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class InvoiceLineItem:
    """Invoice line item data"""
    
    price_data: dict
    quantity: int = 1
    
    def to_dict(self) -> dict:
        return {
            "price_data": self.price_data,
            "quantity": self.quantity
        }


@dataclass
class InvoiceRequest:
    """Invoice request data"""

    customer_email: str
    line_items: List[InvoiceLineItem]
    currency: str = "usd"
    description: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    auto_advance: bool = True
    collection_method: str = "send_invoice"
    days_until_due: int = 30

    def to_dict(self) -> dict:
        result = {
            "customer": self.customer_email,
            "currency": self.currency,
            "auto_advance": self.auto_advance,
            "collection_method": self.collection_method,
            "days_until_due": self.days_until_due,
        }
        
        if self.description:
            result["description"] = self.description
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
