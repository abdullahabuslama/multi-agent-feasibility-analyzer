# NileCart — APIs and Integrations

> Synthetic document for training. NileCart is a fictional company.

## Internal APIs
All internal APIs are REST over HTTPS with JSON. Service-to-service calls
use OAuth 2.0 client credentials. Default rate limit: 100 requests per
second per client.

| API | Main operations | Notes |
|---|---|---|
| Orders API | Get order, order status, delivery tracking, cancel | Read access is easy; write access needs Core team review |
| Customers API | Get profile, addresses, order history | Returns personal data; access logged and limited |
| Catalog API | Search products, product details, stock level | Public data, high rate limit |
| Returns API | Create return, return status, refund status | Refunds above EGP 5,000 need a human approval |
| Payments API | Payment status, refund trigger | Card data never passes through it |

## External integrations
- **Payment gateways**: two local gateways for cards and mobile wallets.
  Card data is tokenized by the gateways; NileCart never stores card numbers.
- **BNPL partners**: three partners connected by redirect checkout.
- **Couriers**: own fleet in main cities plus two courier partners for
  other governorates. Tracking updates arrive by webhook.
- **Messaging**: SMS provider and WhatsApp Business API for notifications
  and support chats.
- **Help desk**: SaaS tool with a REST API and webhooks for new tickets.

## Rules for new integrations
1. Every new vendor needs a security review (about 2–4 weeks).
2. Webhooks must be signed and retried with back-off.
3. Vendors that process customer personal data must sign a data
   processing agreement (DPA).
4. New integrations must not add more than 200 ms to checkout.
