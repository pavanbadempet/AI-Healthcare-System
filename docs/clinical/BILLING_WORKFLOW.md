# Billing Workflow

This module adds the commercial operations layer hospitals and clinics expect: billable service catalog, invoice issuance, patient billing visibility, cashier payment collection, and revenue/outstanding metrics.

## Product Boundary

Safe positioning:

> Hospital billing workflow management for service catalogs, invoices, payments, balances, and administrator metrics.

Do not claim:

- automated insurance adjudication
- guaranteed tax compliance
- autonomous financial reconciliation
- replacement of accounting review
- regulatory billing certification

## Core Concepts

| Concept | Purpose |
| --- | --- |
| Billable Service | Reusable catalog item with code, name, type, optional department, and unit price |
| Invoice | Patient bill tied to an optional encounter/admission with server-calculated totals |
| Invoice Line Item | Service or custom charge with quantity, unit price, and line total |
| Billing Payment | Cashier-collected payment against an invoice |
| Balance | Remaining amount due after collected payments |
| Metrics | Billed, collected, outstanding, invoice status mix, and service count |

## Implemented API Surface

Services:

- `POST /billing/services` - admin/billing creates a billable service
- `GET /billing/services` - admin/billing lists service catalog

Invoices:

- `POST /billing/invoices` - admin/billing issues a patient invoice
- `GET /billing/patient/invoices` - current patient sees own invoices
- `GET /billing/admin/invoices` - admin/billing lists invoices

Payments:

- `POST /billing/invoices/{invoice_id}/payments` - admin/billing records a payment and updates balance

Metrics:

- `GET /billing/admin/metrics` - billing operations summary

## Workflow

1. Admin or billing staff creates billable services.
2. Billing staff issues an invoice for a patient and optional encounter/admission.
3. Totals are calculated server-side from line items, discount, and tax.
4. Patient can see only their own invoices.
5. Billing staff records one or more payments.
6. Invoice status moves from `issued` to `partially_paid` to `paid`.
7. Metrics summarize billed, collected, and outstanding balances.

## Safety Language

Use:

- "invoice issued"
- "payment recorded"
- "outstanding balance"
- "cashier workflow"
- "finance team review"

Avoid:

- "tax certified"
- "insurance approved"
- "automatic claims settlement"
- "accounting replacement"

## Roadmap

Next billing capabilities:

- Package pricing for common OPD/IPD workflows.
- Refunds, reversals, and receipt numbering.
- GST/tax configuration by legal entity and jurisdiction.
- Insurance/TPA claim workflow.
- Discharge billing closure.
- Export to accounting systems.
