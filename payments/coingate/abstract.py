from abc import ABC, abstractmethod

from apps.services.coingate.dto import CreateOrderDTO


class AbstractPaymentGateway(ABC):
    @abstractmethod
    def create_order(self, order_data: CreateOrderDTO) -> dict:
        """Create a payment order with the given details."""
        pass

    @abstractmethod
    def map_status(self, external_status: str):
        """Map a payment provider's status to an internal status."""
        pass
