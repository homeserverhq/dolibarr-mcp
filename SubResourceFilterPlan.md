# Sub-Resource Field Filtering Plan

## Goal
Add server-side `properties` filtering to all sub-resource list-returning methods in `client.py` to return only descriptive common fields instead of all fields.

## New Constants (5) — add to `client.py` after existing constants

```python
LINE_COMMON = "id,product_label,qty,subprice,total_ht,total_ttc,tva_tx,desc"
BOM_LINE_COMMON = "id,ref,fk_product,qty"
EXPENSE_LINE_COMMON = "id,type_fees_libelle,qty,total_ht,total_ttc,tva_tx,date,projet_title"
BANK_LINE_COMMON = "id,ref,label,amount,dateo,bank_account_label"
PAYMENT_LINE_COMMON = "id,ref,amount,type,date"
```

## Methods to Modify (27 total)

Each method gets `params = {"properties": CONSTANT}` added, passing `params` to the `self.get()` call.

### LINE_COMMON (4 methods)
1. `orders_get_lines` (line 486)
2. `proposals_get_lines` (line 413)
3. `invoices_get_lines` (line 570)
4. `supplier_invoices_get_lines` (line 801)

### BOM_LINE_COMMON (1 method)
5. `boms_get_lines` (line 949)

### EXPENSE_LINE_COMMON (1 method)
6. `expense_reports_get_lines` (line 1253)

### BANK_LINE_COMMON (1 method)
7. `bankaccounts_get_lines` (line 684)

### PAYMENT_LINE_COMMON (2 methods)
8. `invoices_get_payments` (line 604)
9. `supplier_invoices_get_payments` (line 825)

### BASE_COMMON (9 methods)
10. `thirdparties_get_outstanding_proposals` (line 178)
11. `thirdparties_get_outstanding_orders` (line 183)
12. `thirdparties_get_outstanding_invoices` (line 188)
13. `thirdparties_get_categories` (line 198) — has existing params
14. `contacts_get_categories` (line 236) — has existing params
15. `products_get_categories` (line 278) — has existing params
16. `products_get_subproducts` (line 275)
17. `projects_get_tasks` (line 1019) — has `includetimespent` param
18. `multi_currencies_get_rates` (line 1482)

### CONTACT_COMMON (8 methods)
19. `products_get_contacts` (line 291) — has `type` param
20. `orders_get_contacts` (line 532) — has `type` param
21. `invoices_get_contacts` (line 610) — has `type` param
22. `supplier_orders_get_contacts` (line 742) — has `type` param
23. `interventions_get_contacts` (line 1219) — has `type` param
24. `tasks_get_contacts` (line 1079) — has `type` param
25. `projects_get_contacts` (line 1032) — has `type` param
26. `thirdparties_get_representatives` (line 193) — has `mode` param

### GROUP_COMMON (1 method)
27. `users_get_user_groups` (line 1621)

## Methods Skipped

| Method | Reason |
|---|---|
| `orders_get_line` (singular) | Already has `include_all_fields` + `_filter_fields` |
| `invoices_get_discount` | Returns single discount object |
| `bankaccounts_get_balance` | Returns single scalar value |
| `products_get_stock` | Returns single dict with summary (stock_reel, stock_theorique, stock_warehouses) |
| `orders_get_shipments` | Returns 404 (no shipments) or single shipment dict |
| `tasks_get_timespent` | Returns 404 or single time entry dict |
| `projects_get_timespent` | Returns 1-element list with summary (min_date, max_date, total_duration) |
| `interventions_get_lines` | Endpoint returns 404 (doesn't exist) |
| `warehouses_list_products` | Already uses `properties` via `include_all_fields` |
| `contracts_get_lines` | Already uses `properties` via `include_all_fields` |
| `users_list_groups` | Already uses `properties` via `include_all_fields` |

## No main.py Changes

None of these methods expose `include_all_fields` to the agent. Tool signatures stay as-is.

## Build & Test

```
docker build -t dolibarr-mcp:latest .
docker rm -f dolibarr-mcp
docker run -d --name dolibarr-mcp --network dock-ext -e DOLIBARR_BASE_URL="http://dolibarr-app:80/api/index.php" -e MCP_SERVER_PORT=6033 -p 6033:6033 dolibarr-mcp:latest
API_KEY=jIk18AYfdVXlRaC5IwXybX20C537fg24 python src/test_runner.py
```
