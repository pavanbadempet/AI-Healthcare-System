# Billing Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add hospital billing operations for service catalogs, invoices, patient billing views, cashier payments, balances, and admin revenue/outstanding metrics.

**Architecture:** Add billable service, invoice, invoice line item, and billing payment persisted records. Add schemas and a `backend/billing.py` router with billing/admin access controls and patient-scoped invoice views.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest.

---

## File Structure

- Modify `backend/models.py`: add billing service, invoice, line item, and payment models.
- Modify `backend/schemas.py`: add billing request/response schemas.
- Add `backend/billing.py`: billing workflow router.
- Modify `backend/main.py`: mount billing router.
- Modify `backend/admin.py`: allow admin assignment of the `billing` role.
- Modify `backend/AGENTS.md` and `backend/CONTEXT.md`: module references.
- Add `tests/unit/test_billing.py`: workflow and access tests.
- Extend `tests/unit/test_admin_security.py`: billing role assignment coverage.
- Add `docs/BILLING_WORKFLOW.md`: product boundary and workflow notes.

---

### Task 1: Add Red Tests

- [x] Patient cannot create billable service.
- [x] Billing staff can create service and invoice totals.
- [x] Patient sees only own invoices.
- [x] Billing staff records payments and invoice balances.
- [x] Payment rejects overpayment.
- [x] Admin billing metrics summarize revenue and outstanding balances.
- [x] Admin can assign billing role.

### Task 2: Add Models And Schemas

- [x] Add `BillableService`.
- [x] Add `Invoice`.
- [x] Add `InvoiceLineItem`.
- [x] Add `BillingPayment`.
- [x] Add service create/response schemas.
- [x] Add invoice create/line item/response schemas.
- [x] Add payment create/response schemas.

### Task 3: Implement Billing Router

- [x] Add service create/list endpoints.
- [x] Add invoice creation endpoint with server-side totals.
- [x] Emit care event for invoice issuance.
- [x] Add patient invoice endpoint.
- [x] Add admin/billing invoice list endpoint.
- [x] Add payment endpoint with balance updates and overpayment guard.
- [x] Emit care event for payment recording.
- [x] Add billing metrics endpoint.
- [x] Mount router in `backend/main.py`.

### Task 4: Documentation

- [x] Add billing workflow doc.
- [x] Update backend module references.
- [x] Update hospital operations roadmap.

### Task 5: Verification

- [x] Run focused billing tests.
- [x] Run compile checks.
- [x] Run related hospital/pharmacy/admin/trust tests.
- [x] Run full unit suite and integration/API tests.
- [x] Run adapter sync and diff checks.
