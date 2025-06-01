import logging

import stripe
from django.conf import settings

from apps.order.models import Order
from apps.services.orders import OrderService
from apps.services.stripe.abstract import AbstractPaymentService
from apps.services.stripe.dto import CheckoutSessionRequestDTO, CheckoutSessionResponseDTO, StripeTax, WebhookEventDTO
from apps.services.stripe.exceptions import StripeServiceException

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentServiceImpl(AbstractPaymentService):
    def get_or_create_tax_rate(self, dto: StripeTax) -> str:
        try:
            tax_rates = stripe.TaxRate.list(limit=100)
            for rate in tax_rates.data:
                if rate.percentage == dto.percentage and rate.active:
                    return rate.id
            tax_rate = stripe.TaxRate.create(
                display_name=dto.display_name,
                description=dto.description,
                jurisdiction=dto.jurisdiction,
                percentage=dto.percentage,
                inclusive=dto.inclusive,
            )
            return tax_rate.id
        except Exception as e:
            logger.exception(f"Error creating/retrieving tax rate: {e}")
            return None

    def create_checkout_session(self, dto: CheckoutSessionRequestDTO) -> CheckoutSessionResponseDTO:
        try:
            line_items = []
            for item in dto.line_items:
                price_data = {
                    "currency": "usd",
                    "product_data": {
                        "name": item.name,
                    },
                    "unit_amount": item.price,
                }

                if item.description:
                    price_data["product_data"]["description"] = item.description

                if item.tax_behavior:
                    price_data["tax_behavior"] = item.tax_behavior

                if item.price_data:
                    price_data = {**price_data, **item.price_data}

                line_item = {
                    "price_data": price_data,
                    "quantity": item.quantity,
                }

                if item.tax_rates:
                    line_item["tax_rates"] = item.tax_rates

                line_items.append(line_item)

            session_params = {
                "payment_method_types": ["card"],
                "line_items": line_items,
                "mode": "payment",
                "customer_email": dto.customer_email,
                "metadata": {"order_id": dto.order_id},
                "success_url": dto.success_url,
                "cancel_url": dto.cancel_url,
                "automatic_tax": {
                    "enabled": dto.automatic_tax
                },
            }

            session = stripe.checkout.Session.create(**session_params)
            return CheckoutSessionResponseDTO(
                session_id=session.id,
                payment_url=session.url
            )
        except Exception as e:
            raise StripeServiceException(f"Checkout creation failed: {str(e)}")

    def handle_webhook_event(self, dto: WebhookEventDTO) -> bool:
        try:
            event = stripe.Webhook.construct_event(
                dto.payload,
                dto.signature,
                settings.STRIPE_WEBHOOK_SECRET
            )

            event_handlers = {
                "checkout.session.completed": self.__handle_checkout_session_completed(event),
                "payment_intent.succeeded": self.__handle_payment_intent_succeeded(event),
                "charge.succeeded": self.__handle_charge_succeeded(event),
                "payment_intent.created": self.__handle_payment_intent_created(event),
                "checkout.session.expired": self.__handle_checkout_session_expired(event),
            }

            handler = event_handlers.get(event["type"])
            if handler:
                handler(event)
            else:
                logger.warning(f"Unhandled Stripe event type: {event['type']}")

            return True
        except Exception as e:
            raise StripeServiceException(f"Webhook processing failed: {str(e)}")

    def __handle_checkout_session_completed(self, event):
        session = event["data"]["object"]
        order_id = session["metadata"].get("order_id")

        if not order_id:
            logger.error("Checkout session completed but order_id is missing.")
            return
        order = Order.objects.filter(id=order_id).first()
        if not order:
            logger.error(f"Order with ID {order_id} not found.")
            return
        order_service = OrderService()
        order_service._handle_successful_payment(order)
        order_service._handle_order_transaction(order)
        order_service._create_chat(order)

    def __handle_payment_intent_succeeded(self, event):
        payment_intent = event["data"]["object"]
        order_id = payment_intent.get("metadata", {}).get("order_id")

        if not order_id:
            logger.error("Payment intent succeeded but order_id is missing.")
            return

        logger.info(f"Payment received for Order {order_id}, marking as paid.")

    def __handle_charge_succeeded(self, event):
        charge = event["data"]["object"]
        logger.info(f"Charge succeeded: Amount {charge['amount']}, Charge ID {charge['id']}.")

    def __handle_payment_intent_created(self, event):
        payment_intent = event["data"]["object"]
        logger.info(f"Payment Intent created with ID {payment_intent['id']}.")

    def __handle_checkout_session_expired(self, event):
        session = event["data"]["object"]
        order_id = session["metadata"].get("order_id")

        if not order_id:
            logger.error("Checkout session expired but order_id is missing.")
            return

        try:
            order = Order.objects.get(id=order_id)
            order.status = Order.OrderStatus.EXPIRED
            order.cancel_order()
            order.delete()
            logger.info(f"Order {order_id} marked as expired.")
        except Order.DoesNotExist:
            logger.error(f"Order with ID {order_id} not found in database.")
