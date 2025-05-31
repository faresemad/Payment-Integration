from apps.orders.models import Order
from apps.services.coingate.dto import CreateOrderDTO
from apps.services.coingate.implementation import CoinGateGateway


class PaymentService:
    def __init__(self):
        self.gateway = CoinGateGateway()

    def create_payment(self, order: Order, cryptocurrency: str):
        dto = CreateOrderDTO(
            order_id=str(order.id),
            price_amount=float(order.total_price),
            price_currency="USD",
            receive_currency=cryptocurrency,
            callback_url=f"{self.gateway.backend_url}/api/orders/webhook/coingate/",
            cancel_url=f"{self.gateway.base_url}/payment/cancel/",
            success_url=f"{self.gateway.base_url}/payment/success/",
            title=f"Order #{order.id}",
            description=f"Payment for Order #{order.id}"
        )
        return self.gateway.create_order(dto)

    def map_payment_status(self, coingate_status: str):
        return self.gateway.map_status(coingate_status)
