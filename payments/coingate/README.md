# CoinGate Payment Integration (Django)

This module provides a clean and reusable integration with the [CoinGate Cryptocurrency Payment Gateway](https://coingate.com/), structured with SOLID principles for maintainability and extensibility.

## 📁 Structure

```
coingate/
├── dto.py                # Data Transfer Object (CreateOrderDTO)
├── abstract.py           # Abstract base class for payment gateways
├── implementation.py     # CoinGate-specific implementation
└── service.py            # Application-facing service to use the gateway
```

## ✅ Features

- Create cryptocurrency payment orders via CoinGate
- Map CoinGate payment statuses to your internal transaction system
- Decoupled architecture for easy testing and extensibility

## ⚙️ Usage

### 1. Create a payment order

```python
from payment.service import PaymentService

payment_service = PaymentService()
response = payment_service.create_payment(order, "BTC")
```

### 2. Map payment status

```python
status = payment_service.map_payment_status("paid")
```

## 🧩 Requirements

- Django project
- `requests` library
- `apps.orders.models.Order` and `Transaction` model with `PaymentStatus` Enum

## 🔐 Settings

Ensure the following are set in your Django settings:

```python
COINGATE_API_KEY = "your_coingate_api_key"
COINGATE_SANDBOX = True  # or False for production
BASE_URL = "https://your-frontend.com"
BACKEND_URL = "https://your-backend.com"
```

## 🧪 Extending

To support other gateways (e.g., Stripe, PayPal):

1. Create a new class that implements `AbstractPaymentGateway`.
2. Inject the new class into `PaymentService`.
