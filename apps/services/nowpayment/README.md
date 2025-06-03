# NowPayment Service

A Django service package for integrating with the NowPayments API to handle cryptocurrency payments.

## Features

- Create payment invoices
- Handle webhook notifications
- Verify payment status
- Generate QR codes for payments
- Clean architecture with dependency injection
- Comprehensive error handling

## Architecture

The service follows a clean architecture pattern with:

- **Abstract Layer**: Defines the contract (`NowPaymentAbstract`)
- **Implementation Layer**: Contains the actual API integration (`NowPaymentServiceImpl`)
- **Service Layer**: Provides a simple interface (`NowPaymentService`)
- **DTOs**: Data Transfer Objects for type safety and validation
- **Exceptions**: Custom exception handling

## Installation & Setup

### 1. Dependencies

Add these to your `requirements.txt`:

```txt
requests>=2.31.0
Django>=4.0.0
```

### 2. Django Settings

Add the following to your Django settings:

```python
# settings.py

# NowPayments Configuration
NOWPAYMENTS_API_KEY = "your-api-key-here"
NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"  # Production
# NOWPAYMENTS_API_URL = "https://api-sandbox.nowpayments.io/v1"  # Sandbox

# Add to INSTALLED_APPS if this is a separate app
INSTALLED_APPS = [
    # ... other apps
    'apps.services.nowpayment',
]
```

### 3. Environment Variables (Recommended)

```bash
# .env
NOWPAYMENTS_API_KEY=your-api-key-here
NOWPAYMENTS_API_URL=https://api.nowpayments.io/v1
```

Load in settings:

```python
import os
from dotenv import load_dotenv

load_dotenv()

NOWPAYMENTS_API_KEY = os.getenv('NOWPAYMENTS_API_KEY')
NOWPAYMENTS_API_URL = os.getenv('NOWPAYMENTS_API_URL')
```

## Usage in Django Views/ViewSets

### Basic ViewSet Example

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse

from apps.services.nowpayment import NowPaymentService, CreateInvoiceDto, WebhookDto
from apps.services.nowpayment.exceptions import NowPaymentsAPIError


class PaymentViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.payment_service = NowPaymentService()

    @action(detail=False, methods=['post'], url_path='create-invoice')
    def create_payment_invoice(self, request):
        """
        Create a new payment invoice
        
        Expected payload:
        {
            "price_amount": 100.0,
            "price_currency": "USD",
            "order_id": "ORDER-123",
            "order_description": "Premium subscription",
            "success_url": "https://yoursite.com/success",
            "cancel_url": "https://yoursite.com/cancel"
        }
        """
        try:
            # Create DTO from request data
            invoice_dto = CreateInvoiceDto(
                price_amount=request.data.get('price_amount'),
                price_currency=request.data.get('price_currency'),
                order_id=request.data.get('order_id'),
                order_description=request.data.get('order_description'),
                ipn_callback_url=f"{request.build_absolute_uri('/api/payments/webhook/')}",
                success_url=request.data.get('success_url'),
                cancel_url=request.data.get('cancel_url'),
                is_fee_paid_by_user=True
            )
            
            # Create invoice
            result = self.payment_service.create_invoice(invoice_dto.to_dict())
            
            return Response({
                'success': True,
                'payment_id': result.get('payment_id'),
                'payment_url': result.get('payment_url'),
                'qr_code_url': result.get('qr_code_url'),
                'message': 'Invoice created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except NowPaymentsAPIError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='webhook')
    def handle_webhook(self, request):
        """
        Handle NowPayments webhook notifications
        
        Expected payload from NowPayments:
        {
            "payment_id": "12345",
            "payment_status": "finished"
        }
        """
        try:
            # Create webhook DTO
            webhook_dto = WebhookDto(
                payment_id=request.data.get('payment_id'),
                payment_status=request.data.get('payment_status')
            )
            
            # Verify and process webhook
            status_message = self.payment_service.verify_webhook(webhook_dto)
            
            if isinstance(status_message, dict) and 'error' in status_message:
                return HttpResponse('Invalid webhook data', status=400)
            
            # Process the payment status change
            self._process_payment_status_change(
                webhook_dto.payment_id, 
                webhook_dto.payment_status,
                status_message
            )
            
            return HttpResponse('OK', status=200)
            
        except Exception as e:
            # Log the error but return 200 to prevent webhook retries
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Webhook processing error: {str(e)}")
            return HttpResponse('OK', status=200)
    
    def _process_payment_status_change(self, payment_id, status, status_message):
        """
        Process payment status changes based on webhook data
        """
        # Implementation depends on your business logic
        # Example:
        if status.lower() == 'finished':
            # Payment completed - activate user subscription, send confirmation email, etc.
            self._handle_successful_payment(payment_id)
        elif status.lower() == 'expired':
            # Payment expired - notify user, cleanup pending orders, etc.
            self._handle_expired_payment(payment_id)
        elif status.lower() == 'failed':
            # Payment failed - notify user, log for investigation, etc.
            self._handle_failed_payment(payment_id)
    
    def _handle_successful_payment(self, payment_id):
        # Your business logic for successful payments
        pass
    
    def _handle_expired_payment(self, payment_id):
        # Your business logic for expired payments
        pass
    
    def _handle_failed_payment(self, payment_id):
        # Your business logic for failed payments
        pass
```

### Advanced ViewSet with Order Management

```python
from django.shortcuts import get_object_or_404
from myapp.models import Order, Payment


class OrderPaymentViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.payment_service = NowPaymentService()

    @action(detail=True, methods=['post'], url_path='pay')
    def create_payment_for_order(self, request, pk=None):
        """
        Create payment for a specific order
        """
        try:
            order = get_object_or_404(Order, pk=pk, user=request.user)
            
            # Check if order is already paid or has pending payment
            if order.status in ['paid', 'pending_payment']:
                return Response({
                    'error': 'Order already paid or has pending payment'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create invoice DTO
            invoice_dto = CreateInvoiceDto(
                price_amount=float(order.total_amount),
                price_currency=order.currency,
                order_id=str(order.id),
                order_description=f"Payment for Order #{order.id}",
                ipn_callback_url=request.build_absolute_uri(f'/api/orders/{order.id}/webhook/'),
                success_url=f"{request.scheme}://{request.get_host()}/orders/{order.id}/success/",
                cancel_url=f"{request.scheme}://{request.get_host()}/orders/{order.id}/cancel/",
                is_fee_paid_by_user=True
            )
            
            # Create payment
            result = self.payment_service.create_invoice(invoice_dto.to_dict())
            
            # Save payment record
            payment = Payment.objects.create(
                order=order,
                payment_id=result.get('payment_id'),
                amount=order.total_amount,
                currency=order.currency,
                status='pending'
            )
            
            # Update order status
            order.status = 'pending_payment'
            order.save()
            
            return Response({
                'success': True,
                'payment_id': result.get('payment_id'),
                'payment_url': result.get('payment_url'),
                'qr_code_url': result.get('qr_code_url'),
                'order_id': order.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
```

### URL Configuration

```python
# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, OrderPaymentViewSet

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'orders', OrderPaymentViewSet, basename='order-payments')

urlpatterns = [
    path('api/', include(router.urls)),
]
```

## Payment Status Mapping

The service maps NowPayments statuses to human-readable messages:

| NowPayments Status | Mapped Message |
|-------------------|----------------|
| `waiting` | waiting for paying |
| `confirming` | confirming checkout |
| `finished` | payed successfully |
| `expired` | checkout expired |
| `failed` | checkout faild |
| `refunded` | amount refunded |

## Error Handling

The service provides custom exception handling:

```python
from apps.services.nowpayment.exceptions import NowPaymentsAPIError

try:
    result = payment_service.create_invoice(invoice_data)
except NowPaymentsAPIError as e:
    # Handle API-specific errors
    logger.error(f"NowPayments API Error: {str(e)}")
except Exception as e:
    # Handle general errors
    logger.error(f"Unexpected error: {str(e)}")
```

## Testing

### Unit Test Example

```python
import unittest
from unittest.mock import Mock, patch
from apps.services.nowpayment import NowPaymentService, CreateInvoiceDto


class TestNowPaymentService(unittest.TestCase):
    def setUp(self):
        self.service = NowPaymentService()
    
    @patch('requests.post')
    def test_create_invoice_success(self, mock_post):
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {'payment_id': '12345'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test data
        invoice_dto = CreateInvoiceDto(
            price_amount=100.0,
            price_currency='USD',
            order_id='TEST-001',
            ipn_callback_url='https://example.com/webhook',
            success_url='https://example.com/success',
            cancel_url='https://example.com/cancel'
        )
        
        # Execute
        result = self.service.create_invoice(invoice_dto.to_dict())
        
        # Assert
        self.assertIn('payment_id', result)
        self.assertIn('payment_url', result)
        self.assertIn('qr_code_url', result)
```

## Security Considerations

1. **API Key Security**: Store API keys in environment variables, never in code
2. **Webhook Validation**: Implement proper webhook signature validation in production
3. **HTTPS Only**: Always use HTTPS for webhook URLs and redirect URLs
4. **Input Validation**: Validate all input data before creating DTOs
5. **Rate Limiting**: Implement rate limiting for payment creation endpoints

## Production Checklist

- [ ] API keys stored securely in environment variables
- [ ] Webhook endpoints are properly secured
- [ ] Error logging is configured
- [ ] Payment status changes are properly handled
- [ ] Database transactions are used for payment processing
- [ ] Monitoring and alerting is set up for payment failures
- [ ] API rate limiting is implemented
- [ ] SSL certificates are properly configured

## Support

For NowPayments API documentation and support:

- [NowPayments API Documentation](https://documenter.getpostman.com/view/7907941/S1a32n38)
- [NowPayments Support](https://nowpayments.io/help)

## License

This implementation is provided as-is for integration with the NowPayments service.
