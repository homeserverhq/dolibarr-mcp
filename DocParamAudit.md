# Full Audit Report: `/repos/dolibarr-mcp/src/main.py`

**Total tools audited: 299**

---

## VIOLATION 1 (CRITICAL) — Hidden Complexity: `mos_produce_and_consume` (line 3642)

### Issue

Two parameters are typed as bare `Optional[list]` (equivalent to `list[Any]`) but actually expect lists of **dictionaries** with multiple structured fields. This is dictionary-in-disguise — a direct violation of the "simple primitive" rule.

### Function signature

```python
async def mos_produce_and_consume(
    id: int,
    inventorylabel: str,
    inventorycode: str,
    arraytoconsume: Optional[list] = None,    # bare list — no element type
    arraytoproduce: Optional[list] = None,    # bare list — no element type
    autoclose: int = 1,
    ctx: Context = None
) -> dict[str, Any]:
```

### The docstring itself confirms the violation (lines 3651–3652):

```
arraytoconsume: Array of objects to consume, each with objectid (MoLine rowid), qty, fk_warehouse.
arraytoproduce: Array of objects to produce, each with objectid (MoLine rowid), qty, fk_warehouse.
```

These are NOT lists of simple primitives (e.g. `list[int]`, `list[str]`). Each element is a **dict** with keys `objectid`, `qty`, `fk_warehouse`. This should either be split into individual parameters or typed as `list[SomePydanticModel]`.

### Code usage (lines 3655–3662) confirms the dict expectation:

```python
payload = {
    "inventorylabel": inventorylabel,
    "inventorycode": inventorycode,
    "autoclose": autoclose,
    "arraytoconsume": arraytoconsume or [],
    "arraytoproduce": arraytoproduce or [],
}
```

---

## VIOLATION 2 (HIGH) — Missing Docstring Parameter: `invoices_add_payment` (line 2506)

### Issue

`amount: float = 0.0` is present in the function signature but **completely absent** from the Args section of the docstring. A user of this tool has no way to know they can pass an amount.

### Function signature

```python
async def invoices_add_payment(
    id: int,
    datepaye: str,
    paymentid: int,
    accountid: int,
    closepaidinvoices: str = "no",
    num_payment: str = "",
    comment: str = "",
    amount: float = 0.0,         # ← MISSING from docstring
    chqemetteur: str = "",
    chqbank: str = "",
    ctx: Context = None
) -> dict[str, Any]:
```

### Docstring Args section (lines 2509–2518)

```
Args:
    id: The unique ID of the resource (required).
    datepaye: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00) (required).
    paymentid: Payment type ID (required).
    accountid: Account ID (required).
    closepaidinvoices: Close paid invoices flag ("yes" or "no").
    num_payment: Payment number.
    comment: Comment.
    chqemetteur: Check issuer.
    chqbank: Check bank.
```

Note: `amount` is listed nowhere, yet it is used on line 2520 (`amount=amount`).

---

## VIOLATION 3 (LOW) — Mutable Default Argument: `supplier_orders_receive` (line 2995)

### Issue

```python
lines: list[ReceiveLine] = []
```

While `list[ReceiveLine]` with a pydantic model of simple primitives is technically allowed by the audit rules, the **mutable default `[]`** is a well-known Python anti-pattern. The same list object persists across all calls that don't supply `lines`.

---

## Summary Table

| # | Tool | Line | Severity | Issue |
|---|------|------|----------|-------|
| 1 | `mos_produce_and_consume` | 3642 | **CRITICAL** | `arraytoconsume` / `arraytoproduce` typed as bare `Optional[list]` but accept lists of dicts with multiple structured fields. Not a simple primitive, not a list of simple primitives, and not a proper pydantic model. |
| 2 | `invoices_add_payment` | 2506 | **HIGH** | `amount: float = 0.0` present in function signature but completely undocumented in docstring Args. |
| 3 | `supplier_orders_receive` | 2995 | **LOW** | `lines: list[ReceiveLine] = []` uses mutable default argument (shared across calls). |

---

## Verdict

The developer's claim of **full compliance** is **false**. The `mos_produce_and_consume` tool is a clear, unambiguous violation of the SIMPLE primitive requirement. The `invoices_add_payment` tool has a documentation gap that would confuse users.
