# Stripe Payment Service

A Django-based Stripe payment integration service that provides a clean, abstracted interface for handling Stripe checkout sessions, tax rates, and webhook events.

## Features

- **Checkout Session Management**: Create and manage Stripe checkout sessions
- **Tax Rate Handling**: Automatically create or retrieve tax rates
- **Webhook Processing**: Handle Stripe webhook events for payment lifecycle management
- **Clean Architecture**: Abstract interface with concrete implementation
- **Type Safety**: Comprehensive DTOs for type-safe data handling

## Installation

1. Install the Stripe Python library:

```bash
pip install stripe
```

2. Add the service package to your Django project structure:

```
apps/
├── services/
│   └── stripe/
│       ├── __init__.py
│       ├── abstract.py
│       ├── dto.py
│       ├── exceptions.py
│       ├── implementations.py
│       └── service.py
```

3. Configure your Django settings:

```python
# settings.py
STRIPE_SECRET_KEY = "sk_test_..."  # Your Stripe secret key
STRIPE_WEBHOOK_SECRET = "whsec_..."  # Your webhook endpoint secret
```

## Quick Start

### 1. Import the Service

```python
from apps.services.stripe import StripeService, CheckoutSessionRequestDTO, CheckoutItemDTO, StripeTax
```

### 2. Create a Checkout Session

```python
# Initialize the service
stripe_service = StripeService()

# Create line items
items = [
    CheckoutItemDTO(
        name="Premium Plan",
        price=2999,  # Price in cents ($29.99)
        description="Monthly subscription",
        quantity=1
    )
]

# Create checkout session request
checkout_request = CheckoutSessionRequestDTO(
    order_id="order_123",
    payment_method_types=["card"],
    line_items=items,
    mode="payment",
    payment_intent_data={"metadata": {"order_id": "order_123"}},
    success_url="https://yoursite.com/success",
    cancel_url="https://yoursite.com/cancel"
)

# Create the session
response = stripe_service.create_checkout_session(checkout_request)
print(f"Payment URL: {response.payment_url}")
```

### 3. Handle Tax Rates

```python
# Create or get existing tax rate
tax_rate = StripeTax(
    display_name="VAT",
    percentage=20.0,
    inclusive=False,
    description="Value Added Tax",
    jurisdiction="EU"
)

tax_rate_id = stripe_service.get_or_create_tax_rate(tax_rate)

# Use tax rate in checkout items
item_with_tax = CheckoutItemDTO(
    name="Taxable Product",
    price=1000,
    tax_rates=[tax_rate_id]
)
```

### 4. Process Webhooks

```python
from apps.services.stripe import WebhookEventDTO

def stripe_webhook_view(request):
    webhook_dto = WebhookEventDTO(
        event_type=request.headers.get('stripe-signature'),
        payload=request.body,
        signature=request.headers.get('stripe-signature')
    )
    
    try:
        success = stripe_service.handle_webhook(webhook_dto)
        return JsonResponse({'status': 'success' if success else 'failed'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
```

## API Reference

### StripeService

Main service class that provides the public interface.

#### Methods

- `get_or_create_tax_rate(tax_dto: StripeTax) -> str`: Creates or retrieves existing tax rate
- `create_checkout_session(request_dto: CheckoutSessionRequestDTO) -> CheckoutSessionResponseDTO`: Creates a new checkout session
- `handle_webhook(webhook_dto: WebhookEventDTO) -> bool`: Processes Stripe webhook events

### Data Transfer Objects (DTOs)

#### CheckoutItemDTO

```python
@dataclass
class CheckoutItemDTO:
    name: str                           # Product name
    price: int                          # Price in cents
    description: Optional[str] = None   # Product description
    quantity: int = 1                   # Quantity
    tax_rates: Optional[List[str]] = None  # Tax rate IDs
    price_data: Optional[Dict] = None   # Additional price data
    tax_behavior: Optional[str] = None  # Tax behavior setting
```

#### CheckoutSessionRequestDTO

```python
@dataclass
class CheckoutSessionRequestDTO:
    order_id: str                       # Your internal order ID
    payment_method_types: List[str]     # Accepted payment methods
    line_items: List[CheckoutItemDTO]   # Items to purchase
    mode: str                           # "payment", "subscription", etc.
    payment_intent_data: Dict           # Payment intent metadata
    success_url: str                    # Redirect URL on success
    cancel_url: str                     # Redirect URL on cancel
    metadata: Optional[Dict] = None     # Additional metadata
    expires_at: Optional[int] = None    # Session expiration timestamp
    client_reference_id: Optional[str] = None  # Client reference
    tax_id_collection: Optional[Dict] = None   # Tax ID collection settings
    automatic_tax: bool = False         # Enable automatic tax calculation
```

#### StripeTax

```python
@dataclass
class StripeTax:
    display_name: str                   # Tax rate display name
    percentage: float                   # Tax percentage (e.g., 20.0 for 20%)
    inclusive: bool                     # Whether tax is inclusive
    description: Optional[str] = None   # Tax description
    jurisdiction: Optional[str] = None  # Tax jurisdiction
```

## Webhook Events Handled

The service automatically handles these Stripe webhook events:

- `checkout.session.completed`: Marks order as paid and triggers order processing
- `payment_intent.succeeded`: Logs successful payment
- `charge.succeeded`: Logs successful charge
- `payment_intent.created`: Logs payment intent creation
- `checkout.session.expired`: Marks order as expired and cancels it

## Advanced Usage

### Custom Implementation

You can provide your own implementation by extending `AbstractPaymentService`:

```python
from apps.services.stripe.abstract import AbstractPaymentService

class CustomStripeService(AbstractPaymentService):
    def get_or_create_tax_rate(self, dto: StripeTax) -> str:
        # Your custom implementation
        pass
    
    def create_checkout_session(self, dto: CheckoutSessionRequestDTO) -> CheckoutSessionResponseDTO:
        # Your custom implementation
        pass
    
    def handle_webhook_event(self, dto: WebhookEventDTO) -> bool:
        # Your custom implementation
        pass

# Use custom implementation
stripe_service = StripeService(implementation=CustomStripeService())
```

### Error Handling

The service raises `StripeServiceException` for Stripe-related errors:

```python
from apps.services.stripe.exceptions import StripeServiceException

try:
    response = stripe_service.create_checkout_session(request_dto)
except StripeServiceException as e:
    logger.error(f"Stripe error: {e}")
    # Handle error appropriately
```

### Logging

The service uses Python's logging module. Configure logging in your Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'stripe.log',
        },
    },
    'loggers': {
        'apps.services.stripe.implementations': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Django Integration Example

### View Example

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@require_http_methods(["POST"])
def create_payment(request):
    data = json.loads(request.body)
    
    items = [
        CheckoutItemDTO(
            name=item['name'],
            price=item['price'],
            quantity=item['quantity']
        ) for item in data['items']
    ]
    
    checkout_request = CheckoutSessionRequestDTO(
        order_id=data['order_id'],
        payment_method_types=["card"],
        line_items=items,
        mode="payment",
        payment_intent_data={"metadata": {"order_id": data['order_id']}},
        success_url=f"{request.build_absolute_uri('/')}/success",
        cancel_url=f"{request.build_absolute_uri('/')}/cancel"
    )
    
    try:
        response = stripe_service.create_checkout_session(checkout_request)
        return JsonResponse({
            'session_id': response.session_id,
            'payment_url': response.payment_url
        })
    except StripeServiceException as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    webhook_dto = WebhookEventDTO(
        event_type=request.headers.get('stripe-signature'),
        payload=request.body,
        signature=request.headers.get('stripe-signature')
    )
    
    try:
        stripe_service.handle_webhook(webhook_dto)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
```

### URL Configuration

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create-payment/', views.create_payment, name='create_payment'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
```

## Requirements

- Python 3.7+
- Django 3.2+
- stripe (Python library)
- Active Stripe account with API keys

## Security Notes

- Always validate webhook signatures
- Use HTTPS in production
- Keep your Stripe secret keys secure
- Implement proper error handling and logging
- Validate all input data before processing

## Support

For Stripe-specific issues, refer to the [Stripe Documentation](https://stripe.com/docs).
For bugs or feature requests related to this service implementation, please check your project's issue tracking system.
