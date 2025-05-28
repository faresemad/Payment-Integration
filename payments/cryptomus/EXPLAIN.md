# Cryptomus Payment Service

A Python Django package for integrating with the Cryptomus cryptocurrency payment gateway. This service provides a clean, modular architecture for handling payments, payouts, and webhook validation.

## Features

- **Payment Processing**: Create and monitor cryptocurrency payments
- **Payout Management**: Send cryptocurrency payouts to user wallets
- **Webhook Validation**: Secure webhook signature verification
- **Modular Architecture**: Clean separation of concerns with abstract base classes
- **Comprehensive Logging**: Built-in logging for debugging and monitoring
- **Type Safety**: Full type hints for better code reliability

## Installation

1. Add the package to your Django project
2. Configure your settings (see Configuration section)
3. Import and use the service

## Configuration

Add the following settings to your Django `settings.py`:

```python
# Cryptomus API Configuration
CRYPTOMUS_API_KEY = "your_cryptomus_api_key"
CRYPTOMUS_MERCHANT_ID = "your_merchant_id"
```

## Quick Start

### Basic Usage

```python
from apps.services.cryptomus import CryptomusService

# Initialize the service
cryptomus = CryptomusService()

# Create a payment
payment_response = cryptomus.create_payment(
    amount=100.0,
    currency="USD",
    order_id="ORDER_123",
    lifetime=900  # 15 minutes
)

# Check payment status
status = cryptomus.get_payment_status(payment_response['uuid'])

# Create a payout
payout_response = cryptomus.create_payout(
    amount=50.0,
    currency="USDT",
    to_wallet="TXyz123...",
    network="TRC20"
)

# Verify webhook signature
is_valid = cryptomus.verify_signature(request_body, signature)
```

### Advanced Usage

```python
# Initialize with custom parameters
cryptomus = CryptomusService(
    api_key="custom_api_key",
    merchant_id="custom_merchant_id",
    base_url="https://api.cryptomus.com/v1"
)

# Create payment with additional parameters
payment = cryptomus.create_payment(
    amount=100.0,
    currency="USD",
    order_id="ORDER_123",
    lifetime=1800,  # 30 minutes
    # Additional parameters
    success_url="https://example.com/success",
    fail_url="https://example.com/fail",
    callback_url="https://example.com/webhook"
)
```

## API Reference

### CryptomusService

The main service class that orchestrates all operations.

#### Methods

##### Payment Operations

**`create_payment(amount, currency, order_id, lifetime=900, **kwargs)`**

- Creates a new payment request
- **Parameters:**
  - `amount` (float): Payment amount
  - `currency` (str): Currency code (e.g., "USD", "EUR")
  - `order_id` (str): Unique order identifier
  - `lifetime` (int): Payment lifetime in seconds (default: 15 minutes)
  - `**kwargs`: Additional parameters (success_url, fail_url, etc.)
- **Returns:** Dict with payment details including UUID

**`get_payment_status(payment_uuid)`**

- Retrieves payment status
- **Parameters:**
  - `payment_uuid` (str): Payment UUID from create_payment response
- **Returns:** Dict with payment status information

##### Payout Operations

**`create_payout(amount, currency, to_wallet, network=None, order_id=None)`**

- Creates a payout to user's wallet
- **Parameters:**
  - `amount` (float): Payout amount
  - `currency` (str): Currency code
  - `to_wallet` (str): Destination wallet address
  - `network` (str, optional): Blockchain network (e.g., "TRC20", "ERC20")
  - `order_id` (str, optional): Unique order identifier
- **Returns:** Dict with payout details including UUID

**`get_payout_status(payout_uuid)`**

- Retrieves payout status
- **Parameters:**
  - `payout_uuid` (str): Payout UUID from create_payout response
- **Returns:** Dict with payout status information

##### Webhook Operations

**`verify_signature(request_body, provided_signature)`**

- Verifies webhook signature for security
- **Parameters:**
  - `request_body` (bytes): Raw request body
  - `provided_signature` (str): Signature from webhook headers
- **Returns:** Boolean indicating if signature is valid

## Architecture

The service follows a clean architecture pattern with clear separation of concerns:

### Core Components

- **`CryptomusService`**: Main orchestrator class
- **`PaymentRequest/PayoutRequest`**: Data transfer objects
- **Abstract Base Classes**: Define contracts for implementations
- **Concrete Implementations**: Cryptomus-specific implementations

### Key Abstractions

- **`SignatureGenerator`**: Handles API signature generation and webhook verification
- **`HttpClient`**: Manages HTTP communications
- **`PaymentProcessor`**: Handles payment operations
- **`PayoutProcessor`**: Handles payout operations
- **`WebhookValidator`**: Validates incoming webhooks
- **`ApiClient`**: Manages API requests to Cryptomus

## Webhook Integration

### Django View Example

```python
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

@csrf_exempt
@require_POST
def cryptomus_webhook(request):
    # Get signature from headers
    signature = request.META.get('HTTP_SIGN')
    
    # Verify signature
    cryptomus = CryptomusService()
    if not cryptomus.verify_signature(request.body, signature):
        return HttpResponse('Invalid signature', status=400)
    
    # Process webhook data
    webhook_data = json.loads(request.body)
    
    # Handle different webhook types
    if webhook_data.get('type') == 'payment':
        # Handle payment webhook
        payment_uuid = webhook_data.get('uuid')
        status = webhook_data.get('status')
        # Update your database
        
    return HttpResponse('OK')
```

## Error Handling

The service includes comprehensive error handling:

- **HTTP Errors**: Automatically handled by requests library
- **Signature Validation**: Secure HMAC comparison
- **Logging**: Detailed logging at different levels

### Example Error Handling

```python
try:
    payment = cryptomus.create_payment(100.0, "USD", "ORDER_123")
except requests.exceptions.RequestException as e:
    logger.error(f"Payment creation failed: {e}")
    # Handle error appropriately
```

## Logging

The service provides comprehensive logging. Configure Django logging to capture service logs:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'cryptomus.log',
        },
    },
    'loggers': {
        'apps.services.cryptomus': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Security Considerations

- **API Keys**: Store API keys securely in environment variables or Django settings
- **Webhook Validation**: Always verify webhook signatures before processing
- **HTTPS**: Use HTTPS for all webhook endpoints
- **Rate Limiting**: Consider implementing rate limiting for webhook endpoints

## Testing

### Unit Test Example

```python
import unittest
from unittest.mock import Mock, patch
from apps.services.cryptomus import CryptomusService

class TestCryptomusService(unittest.TestCase):
    def setUp(self):
        self.service = CryptomusService(
            api_key="test_key",
            merchant_id="test_merchant"
        )
    
    @patch('apps.services.cryptomus.implementations.requests.post')
    def test_create_payment(self, mock_post):
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {'uuid': 'test-uuid'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test payment creation
        result = self.service.create_payment(100.0, "USD", "ORDER_123")
        
        self.assertEqual(result['uuid'], 'test-uuid')
        mock_post.assert_called_once()
```

## Troubleshooting

### Common Issues

1. **Invalid Signature Errors**
   - Verify API key is correct
   - Ensure payload is not modified before signature generation
   - Check base64 encoding and JSON formatting

2. **HTTP Errors**
   - Check API endpoint URLs
   - Verify merchant ID configuration
   - Review API rate limits

3. **Webhook Issues**
   - Ensure webhook URL is accessible
   - Verify signature validation logic
   - Check request body handling

## Contributing

1. Follow the existing architecture patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure proper error handling and logging

## Support

For issues related to this implementation, please check the troubleshooting section or review the logs. For Cryptomus API issues, consult the official Cryptomus documentation.
