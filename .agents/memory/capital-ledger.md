---
name: Capital Management ledger design
description: How the Capital Management module's transaction ledger and dashboard totals are computed, for consistency in future related work.
---

The Capital Transactions ledger is NOT a stored table. It is built at request time by merging
Vehicle purchases, Payments, Expenses, and a small new CapitalAdjustment table (the only new
DB table added), sorted chronologically ascending to compute a true running balance, then
reversed for newest-first display, then filtered/paginated in memory.

**Why:** avoids migrating/duplicating existing financial data into a new ledger table that could
drift out of sync; the six dashboard summary cards and the transaction list are guaranteed
consistent because both are derived from the same live queries every time.

**How to apply:** any new feature that writes a new capital-affecting transaction type (e.g. a new
expense category, a new payment type) must be added to both the dashboard summary formula AND the
ledger-merge function, or the two will silently disagree. The formula is:
Current Capital = Vehicle Purchase Cost + Manual Capital Added − Extra Expenditure + Payments Received − Capital Withdrawals.

Expense categories are mapped to the spec's required transaction-type labels via a best-effort
dict (e.g. spare_parts → "Tyres", vehicle_repairs/accident_repairs → "Repair") since the underlying
Expense model doesn't have native categories matching every required label 1:1.

"Performed by" for vehicle purchases is resolved by looking up the AuditLog ADD_VEHICLE entry for
that vehicle (prefetched into a dict, not per-row queries) rather than adding a new column to Vehicle.
