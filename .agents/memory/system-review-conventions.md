---
name: THMS system-wide conventions
description: Cross-module conventions in the Transport Hire Management System worth staying consistent with when adding features or auditing again.
---

- **Audit logging convention**: every *mutating* POST route writes an `AuditLog` entry (via a local `_log()` helper per blueprint); pure GET/view routes never log page views. Keep new mutations consistent with this — including secondary mutations like `VehicleEvent` creation, which had been missed before.
  **Why:** the Audit Log module's usefulness depends on this being applied uniformly; a silent gap on one route type looks like a real omission during review.
- **Archived/voided records are permanent by design** for Contracts, Payments, and Expenses (no restore route exists, and none should be added) — only Drivers and Vehicles have a restore path back to active status.
  **Why:** voiding a payment/expense or archiving a contract is treated as a final correction that must stay out of totals forever, preserving the audit trail. Don't "fix" the missing restore route for these three — it's intentional.
- **Contract.outstanding_balance is the single source of truth** for a contract's remaining balance (`max(0, total_debt - total_paid)`, where `total_debt` includes extra expenditure and `total_paid` excludes archived/voided payments). Any dashboard or aggregate figure must be computed by summing this property per contract in Python, never by a raw SQL aggregate that reimplements the formula — a prior dashboard bug drifted from Capital Management by ignoring extra expenditure and archived-payment filtering.
- **Expense.reason can be `None`** on records where only `description` was filled in (or vice versa) — always read through `Expense.display_title` / `Expense.display_description`, never concatenate `.reason` or `.description` directly, or a `None + str` crash is possible (hit this in the contract timeline builder).
