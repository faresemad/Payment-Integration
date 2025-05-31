# Stripe Invoice Service

A Python Django package for integrating with Stripe's invoicing system. This service provides a clean, modular architecture for creating invoices and handling webhooks with proper security validation.

## Features

- **Invoice Creation**: Create and manage Stripe invoices
- **Customer Management**: Automatic customer creation and retrieval
- **Invoice Operations**: Send, finalize, and track invoices
- **Webhook Validation**: Secure webhook signature verification
- **Modular Architecture**: Clean separation of concerns with abstract base classes
- **Comprehensive Logging**: Built-in logging for debugging and monitoring
- **Type Safety**: Full type hints for better code reliability

## Installation

1. Install Stripe Python library:

```bash
pip install stripe
```

2. Add the package to your Django project
3. Configure your settings (see Configuration section)

## Configuration

Add the following settings to your Django `settings.py`:

```python
# Stripe Configuration
STRIPE_API_KEY = "sk_test_..." # or "sk_live_..." for production
STRIPE_WEBHOOK_SECRET = "whsec_..." # Your webhook endpoint secret
```

## Quick Start

### Basic Invoice Creation

```python
from apps.services.stripe import StripeService

# Initialize the service
stripe_service = StripeService()

# Create an invoice
line_items = [
    {
        "price_data": {
            "currency": "usd",
            "product_data": {
                "name": "Consulting Service"
            },
            "unit_amount": 10000  # $100.00 in cents
        },
        "quantity": 2
    }
]

invoice = stripe_service.create_invoice(
    customer_email="customer@example.com",
    line_items=line_items,
    description="Monthly consulting invoice",
    days_until_due=30
)

# Finalize and send the invoice
stripe_service.finalize_invoice(invoice.id)
stripe_service.send_invoice(invoice.id)
```

### Webhook Handling

```python
# In your Django view
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def stripe_webhook(request):
    stripe_service = StripeService()
    
    # Get signature from headers
    signature = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    # Process webhook
    event = stripe_service.process_webhook(request.body, signature)
    
    if not event:
        return HttpResponse('Invalid signature', status=400)
    
    # Handle different event types
    event_type = event.get('type')
    
    if event_type == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        # Handle successful payment
        print(f"Payment succeeded for invoice: {invoice['id']}")
        
    elif event_type == 'invoice.payment_failed':
        invoice = event['data']['object']
        # Handle failed payment
        print(f"Payment failed for invoice: {invoice['id']}")
    
    return HttpResponse('OK')
```

## API Reference

### StripeService

The main service class that orchestrates all operations.

#### Methods

##### Invoice Operations

**`create_invoice(customer_email, line_items, currency="usd", description=None, metadata=None, auto_advance=True, days_until_due=30)`**

- Creates a new invoice
- **Parameters:**
  - `customer_email` (str): Customer's email address
  - `line_items` (list): List of invoice line items
  - `currency` (str): Currency code (default: "usd")
  - `description` (str, optional): Invoice description
  - `metadata` (dict, optional): Additional metadata
  - `auto_advance` (bool): Auto-advance invoice through collection flow
  - `days_until_due` (int): Days until invoice is due
- **Returns:** Stripe Invoice object

**`get_invoice(invoice_id)`**

- Retrieves invoice details
- **Parameters:**
  - `invoice_id` (str): Stripe invoice ID
- **Returns:** Stripe Invoice object

**`send_invoice(invoice_id)`**

- Sends invoice to customer via email
- **Parameters:**
  - `invoice_id` (str): Stripe invoice ID
- **Returns:** Stripe Invoice object

**`finalize_invoice(invoice_id)`**

- Finalizes invoice (makes it ready for payment)
- **Parameters:**
  - `invoice_id` (str): Stripe invoice ID
- **Returns:** Stripe Invoice object

##### Webhook Operations

**`verify_webhook_signature(payload, signature, endpoint_secret=None)`**

- Verifies webhook signature for security
- **Parameters:**
  - `payload` (bytes): Raw request body
  - `signature` (str): Stripe-Signature header value
  - `endpoint_secret` (str, optional): Webhook endpoint secret
- **Returns:** Boolean indicating if signature is valid

**`process_webhook(payload, signature, endpoint_secret=None)`**

- Processes webhook and returns event data if valid
- **Parameters:**
  - `payload` (bytes): Raw request body
  - `signature` (str): Stripe-Signature header value
  - `endpoint_secret` (str, optional): Webhook endpoint secret
- **Returns:** Event data dict or None if invalid

## Line Items Format

Line items should follow this structure:

```python
line_items = [
    {
        "price_data": {
            "currency": "usd",
            "product_data": {
                "name": "Product/Service Name",
                "description": "Optional description"
            },
            "unit_amount": 1000  # Amount in cents
        },
        "quantity": 1
    }
]
```

### Alternative: Using Existing Price IDs

```python
line_items = [
    {
        "price_data": {
            "currency": "usd",
            "recurring": {
                "interval": "month"  # For subscription items
            },
            "product_data": {
                "name": "Monthly Subscription"
            },
            "unit_amount": 2000
        },
        "quantity": 1
    }
]
```

## Webhook Events

Common webhook events you might want to handle:

- `invoice.created` - Invoice was created
- `invoice.finalized` - Invoice was finalized
- `invoice.sent` - Invoice was sent to customer
- `invoice.payment_succeeded` - Invoice was paid
- `invoice.payment_failed` - Payment attempt failed
- `invoice.voided` - Invoice was voided

## Django Integration Examples

### Complete Webhook View

```python
import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from apps.services.stripe import StripeService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def stripe_webhook(request):
    stripe_service = StripeService()
    signature = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not signature:
        logger.warning("Missing Stripe signature")
        return HttpResponse('Missing signature', status=400)
    
    event = stripe_service.process_webhook(request.body, signature)
    
    if not event:
        logger.warning("Invalid webhook signature")
        return HttpResponse('Invalid signature', status=400)
    
    try:
        handle_webhook_event(event)
        return HttpResponse('OK')
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return HttpResponse('Processing error', status=500)

def handle_webhook_event(event):
    """Handle different webhook event types"""
    event_type = event.get('type')
    
    if event_type == 'invoice.payment_succeeded':
        handle_payment_succeeded(event['data']['object'])
    elif event_type == 'invoice.payment_failed':
        handle_payment_failed(event['data']['object'])
    elif event_type == 'invoice.sent':
        handle_invoice_sent(event['data']['object'])

def handle_payment_succeeded(invoice):
    """Handle successful invoice payment"""
    logger.info(f"Payment succeeded for invoice {invoice['id']}")
    # Update your database, send confirmation email, etc.

def handle_payment_failed(invoice):
    """Handle failed invoice payment"""
    logger.warning(f"Payment failed for invoice {invoice['id']}")
    # Notify customer, retry payment, etc.

def handle_invoice_sent(invoice):
    """Handle invoice sent to customer"""
    logger.info(f"Invoice {invoice['id']} sent to customer")
    # Track invoice delivery, update status, etc.
```

### Invoice Creation API

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

@csrf_exempt
@require_POST
def create_invoice_api(request):
    try:
        data = json.loads(request.body)
        stripe_service = StripeService()
        
        invoice = stripe_service.create_invoice(
            customer_email=data['customer_email'],
            line_items=data['line_items'],
            description=data.get('description'),
            days_until_due=data.get('days_until_due', 30)
        )
        
        # Finalize and send
        stripe_service.finalize_invoice(invoice.id)
        stripe_service.send_invoice(invoice.id)
        
        return JsonResponse({
            'success': True,
            'invoice_id': invoice.id,
            'hosted_invoice_url': invoice.hosted_invoice_url
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
```

## Error Handling

The service includes comprehensive error handling:

```python
try:
    invoice = stripe_service.create_invoice(
        customer_email="customer@example.com",
        line_items=line_items
    )
except stripe.error.CardError as e:
    # Card was declined
    logger.error(f"Card declined: {e}")
except stripe.error.RateLimitError as e:
    # Too many requests
    logger.error(f"Rate limit exceeded: {e}")
except stripe.error.InvalidRequestError as e:
    # Invalid parameters
    logger.error(f"Invalid request: {e}")
except stripe.error.AuthenticationError as e:
    # Authentication failed
    logger.error(f"Authentication error: {e}")
except stripe.error.APIConnectionError as e:
    # Network communication failed
    logger.error(f"Network error: {e}")
except stripe.error.StripeError as e:
    # Generic Stripe error
    logger.error(f"Stripe error: {e}")
```

## Security Best Practices

1. **Webhook Verification**: Always verify webhook signatures
2. **HTTPS**: Use HTTPS for all webhook endpoints
3. **API Keys**: Store API keys securely in environment variables
4. **Logging**: Log webhook events for monitoring and debugging
5. **Error Handling**: Don't expose sensitive error details to clients

## Testing

### Unit Test Example

```python
import unittest
from unittest.mock import Mock, patch
from apps.services.stripe import StripeService

class TestStripeService(unittest.TestCase):
    def setUp(self):
        self.service = StripeService(
            api_key="sk_test_123",
            webhook_secret="whsec_test_123"
        )
    
    @patch('stripe.Invoice.create')
    @patch('stripe.Customer.create')
    def test_create_invoice(self, mock_customer, mock_invoice):
        # Mock customer creation
        mock_customer.return_value = Mock(id='cus_123')
        
        # Mock invoice creation
        mock_invoice.return_value = Mock(id='in_123')
        
        line_items = [{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Test Product"},
                "unit_amount": 1000
            }
        }]
        
        result = self.service.create_invoice(
            customer_email="test@example.com",
            line_items=line_items
        )
        
        self.assertEqual(result.id, 'in_123')
```

## Production Considerations

1. **Environment Variables**: Use environment variables for API keys
2. **Webhook Endpoints**: Set up proper webhook endpoints in Stripe Dashboard
3. **Monitoring**: Monitor webhook delivery and processing
4. **Error Handling**: Implement proper error handling and alerting
5. **Idempotency**: Handle duplicate webhooks gracefully

## Support

For Stripe API issues, consult the [official Stripe documentation](https://stripe.com/docs). For issues with this implementation, check the logs and error messages for debugging information.
