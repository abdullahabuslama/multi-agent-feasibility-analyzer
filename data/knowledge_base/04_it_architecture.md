# NileCart — IT Architecture and Systems

> Synthetic document for training. NileCart is a fictional company.

## Overview
The platform is a modular monolith written in Python (Django) plus a few
separate services. It runs on Kubernetes in a public cloud region in the
Middle East. Customer personal data is stored only in that region.

## Main systems
| System | Technology | Owner team | Notes |
|---|---|---|---|
| Storefront website | Next.js | Web | Server-side rendering for SEO |
| Mobile apps | Flutter (Android & iOS) | Mobile | Release every 2 weeks |
| Core platform (orders, customers, payments) | Django, PostgreSQL | Core | Order module is old and hard to change |
| Catalog & search | Separate service, OpenSearch | Discovery | Arabic and English search |
| Pricing service | Separate service | Commercial tech | Handles campaign prices |
| Event bus | Kafka | Platform | Order and delivery events |
| Cache | Redis | Platform | Sessions and hot data |
| Data warehouse | Cloud data warehouse, daily loads | Data | Dashboards for all departments |
| Help desk | SaaS help desk tool | Support | Tickets from all channels |
| Warehouse management | Third-party WMS | Operations | Integrated by API |

## Data available
- Order history since 2017, customer profiles, delivery events.
- Support tickets and chat transcripts since 2023 (about 1.2 million
  conversations), stored in the help desk tool.
- Product catalog: about 450,000 items with Arabic and English text.

## Capacity and constraints
- Normal load: about 1,500 requests per second; White Friday peak about
  9,000 requests per second.
- No production changes are allowed from 1 November to 5 December
  (campaign freeze).
- The team has no machine-learning engineers in production roles today;
  the data team has 8 people (analysts and 2 data engineers).
- Monthly cloud spend: about EGP 3.1 million.

## Known technical debt
- The order module has few automated tests. Changes take 2–3x longer
  than in other modules.
- The help desk tool and the core platform share data only through a
  nightly export, not in real time.
