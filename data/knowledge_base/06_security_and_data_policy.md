# NileCart — Security and Data-Handling Policy (summary)

> Synthetic document for training. NileCart is a fictional company.

## Legal basis
NileCart processes personal data under Egypt's Personal Data Protection
Law (Law No. 151 of 2020) and its executive regulations. The Data
Protection Officer (DPO) is part of Legal & Compliance.

## Data classes
| Class | Examples | Rules |
|---|---|---|
| Public | Product catalog, prices | No limits |
| Internal | Sales reports, plans | Employees only |
| Personal | Names, phones, addresses, order history, chat transcripts | Need-to-know access, logged, stored in-region |
| Sensitive | National ID copies (for BNPL), payment tokens | Encrypted, very limited access |

## Key rules
1. Customer personal data stays in the approved cloud region. Any transfer
   outside it needs DPO approval.
2. Card data is never stored. Payments are tokenized by the gateways
   (PCI DSS scope kept minimal).
3. Access to personal data follows least privilege and is reviewed every
   quarter.
4. Personal data in chat transcripts is kept for 3 years, then deleted.
5. All vendors that see personal data sign a DPA and pass a security review.

## Use of AI services
- Customer personal data must not be sent to an external AI service
  without DPO approval and a DPA with the provider.
- Personal data should be masked (phones, addresses, names) before any
  text is sent to an AI model when possible.
- AI that answers customers must say that it is an automated assistant
  and must offer a way to reach a human.
- AI must not approve refunds or compensation by itself.

## Incidents (last 3 years)
- 2023: a courier partner leaked a delivery list with names and phone
  numbers. Contract changed; partner audits added.
- 2024: a misconfigured analytics tool collected full addresses. Fixed
  within 5 days; reported to the regulator.
