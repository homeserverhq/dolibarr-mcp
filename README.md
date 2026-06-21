# Dolibarr MCP Multi-Tenant Proxy Server

This repository contains a Model Context Protocol (MCP) server that acts as a secure, multi-tenant proxy between an AI Assistant and the Dolibarr ERP/CRM backend API. It exposes **295 MCP tools** covering 34 resource domains with full CRUD, domain-specific tools, and relationship management.

## ✨ Features

- **Identity Passthrough** — Extracts the `Authorization: Bearer <token>` header from incoming HTTP requests and forwards it to the Dolibarr API without server-side authentication.
- **Multi-Tenancy** — Uses Python `contextvars` to maintain thread-safe user identity isolation, ensuring all AI-driven actions are scoped to the authenticated user's permissions.
- **Full Dolibarr Coverage** — 295 tools mapped to Dolibarr API endpoints across 34 resource domains.
- **TOON Optimization** — Bulk list responses are automatically compressed using TOON (Token-Optimized Object Notation) to reduce token consumption and maximize context window efficiency.
- **Efficient Gets** — GET responses return only commonly used fields by default. Full objects are available via an `include_all_fields` flag.

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DOLIBARR_BASE_URL` | Yes | Docker-internal URL of the Dolibarr API |
| `MCP_SERVER_PORT` | Yes | Port number the MCP server listens on |

## 📦 Installation & Local Development

1. Ensure you have Python 3.12+ installed.
2. Install dependencies:
    ```bash
    pip install fastmcp httpx pydantic uvicorn toon-mcp-server
    ```
3. Run the server:
    ```bash
    export DOLIBARR_BASE_URL=http://localhost:8040/api/index.php
    export MCP_SERVER_PORT=6033
    python -m src.main
    ```

## 🐳 Docker Deployment

Build and run the server using Docker:

```bash
docker build -t dolibarr-mcp:latest .
docker run -d --name dolibarr-mcp \
    -e DOLIBARR_BASE_URL="http://dolibarr-app:80/api/index.php" \
    -e MCP_SERVER_PORT=6033 \
    dolibarr-mcp:latest
```

The MCP server serves at `http://dolibarr-mcp:6033/mcp` (Streamable HTTP).

## ⚠️ Important Notes

- **`include_all_fields`** — The `include_all_fields` parameter (available on all `get_*` and `list_*` tools) controls whether all available fields are included in responses. Defaults to `False` for performance; set to `True` only when additional fields are needed.
- **TOON Compression** — All bulk list responses are automatically compressed using TOON (Token-Optimized Object Notation) to reduce token consumption by 30-60%.
- **Required Fields & Defaults** — Each `create_*` tool requires specific key fields (e.g. `name` for third parties). All other fields default to empty strings or reasonable values. The owner/user assignment field is automatically set to the authenticated user for most resources.

## 🛠️ API Tool Mapping

The server implements 295 MCP tools organized into the following categories:

### ✅ Status (1 tool)
- `status_get` — Health check endpoint for backend connectivity

### 📄 Documents (1 tool)
- `documents_list` — List documents/attachments for a given element

### 🏢 Third Parties (11 tools)
- `thirdparties_list` — List all third parties
- `thirdparties_get` — Get a third party by ID
- `thirdparties_create` — Create a new third party
- `thirdparties_update` — Update an existing third party
- `thirdparties_delete` — Delete a third party by ID
- `thirdparties_get_outstanding_proposals` — Get outstanding proposals for a third party
- `thirdparties_get_outstanding_orders` — Get outstanding orders for a third party
- `thirdparties_get_outstanding_invoices` — Get outstanding invoices for a third party
- `thirdparties_get_representatives` — Get representatives for a third party
- `thirdparties_get_categories` — Get categories for a third party

### 👤 Contacts (6 tools)
- `contacts_list` — List all contacts
- `contacts_get` — Get a contact by ID
- `contacts_create` — Create a new contact
- `contacts_update` — Update an existing contact
- `contacts_delete` — Delete a contact by ID
- `contacts_get_categories` — Get categories for a contact

### 📦 Products (9 tools)
- `products_list` — List all products
- `products_get` — Get a product by ID
- `products_create` — Create a new product
- `products_update` — Update an existing product
- `products_delete` — Delete a product by ID
- `products_get_subproducts` — Get subproducts of a product
- `products_get_categories` — Get categories for a product
- `products_get_stock` — Get stock for a product
- `products_get_contacts` — Get contacts for a product

### 🏭 Warehouses (6 tools)
- `warehouses_list` — List all warehouses
- `warehouses_get` — Get a warehouse by ID
- `warehouses_create` — Create a new warehouse
- `warehouses_update` — Update an existing warehouse
- `warehouses_delete` — Delete a warehouse by ID
- `warehouses_list_products` — List products in a warehouse

### 📊 Stock Movements (5 tools)
- `stockmovements_list` — List all stock movements
- `stockmovements_get` — Get a stock movement by ID
- `stockmovements_create` — Create a new stock movement
- `stockmovements_update` — Update an existing stock movement
- `stockmovements_delete` — Delete a stock movement by ID

### 🏷️ Product Lots (5 tools)
- `productlots_list` — List all product lots
- `productlots_get` — Get a product lot by ID
- `productlots_create` — Create a new product lot
- `productlots_update` — Update an existing product lot
- `productlots_delete` — Delete a product lot by ID

### 📝 Proposals (16 tools)
- `proposals_list` — List all proposals
- `proposals_get` — Get a proposal by ID
- `proposals_create` — Create a new proposal
- `proposals_update` — Update an existing proposal
- `proposals_delete` — Delete a proposal by ID
- `proposals_get_lines` — Get lines of a proposal
- `proposals_create_line` — Create a line on a proposal
- `proposals_update_line` — Update a line on a proposal
- `proposals_delete_line` — Delete a line from a proposal
- `proposals_settodraft` — Set a proposal to draft
- `proposals_validate` — Validate a proposal
- `proposals_close` — Close a proposal
- `proposals_setinvoiced` — Mark a proposal as invoiced
- `proposals_get_contacts` — Get contacts for a proposal
- `proposals_add_contact` — Add a contact to a proposal

### 🛒 Orders (19 tools)
- `orders_list` — List all orders
- `orders_get` — Get an order by ID
- `orders_create` — Create a new order
- `orders_update` — Update an existing order
- `orders_delete` — Delete an order by ID
- `orders_get_lines` — Get lines of an order
- `orders_get_line` — Get a single line from an order
- `orders_create_line` — Create a line on an order
- `orders_update_line` — Update a line on an order
- `orders_delete_line` — Delete a line from an order
- `orders_settodraft` — Set an order to draft
- `orders_validate` — Validate an order
- `orders_close` — Close an order
- `orders_reopen` — Reopen a closed order
- `orders_setinvoiced` — Mark an order as invoiced
- `orders_create_from_proposal` — Create an order from a proposal
- `orders_get_shipments` — Get shipments for an order
- `orders_create_shipment` — Create a shipment from an order
- `orders_get_contacts` — Get contacts for an order

### 🧾 Invoices (21 tools)
- `invoices_list` — List all invoices
- `invoices_get` — Get an invoice by ID
- `invoices_create` — Create a new invoice
- `invoices_update` — Update an existing invoice
- `invoices_delete` — Delete an invoice by ID
- `invoices_get_lines` — Get lines of an invoice
- `invoices_create_line` — Create a line on an invoice
- `invoices_update_line` — Update a line on an invoice
- `invoices_delete_line` — Delete a line from an invoice
- `invoices_create_from_order` — Create an invoice from an order
- `invoices_settodraft` — Set an invoice to draft
- `invoices_validate` — Validate an invoice
- `invoices_settopaid` — Mark an invoice as paid
- `invoices_settounpaid` — Mark an invoice as unpaid
- `invoices_get_payments` — Get payments for an invoice
- `invoices_add_payment` — Add a payment to an invoice
- `invoices_get_contacts` — Get contacts for an invoice
- `invoices_add_contact` — Add a contact to an invoice
- `invoices_delete_contact` — Remove a contact from an invoice
- `invoices_get_discount` — Get available discounts for an invoice
- `invoices_use_discount` — Apply a discount to an invoice

### 💳 Payments (4 tools)
- `payments_list` — List all payments
- `payments_get` — Get a payment by ID
- `payments_update` — Update an existing payment
- `payments_delete` — Delete a payment by ID

### 🏦 Bank Accounts (12 tools)
- `bankaccounts_list` — List all bank accounts
- `bankaccounts_get` — Get a bank account by ID
- `bankaccounts_create` — Create a new bank account
- `bankaccounts_update` — Update an existing bank account
- `bankaccounts_delete` — Delete a bank account by ID
- `bankaccounts_transfer` — Transfer funds between accounts
- `bankaccounts_get_lines` — Get lines of a bank account
- `bankaccounts_create_line` — Create a line on a bank account
- `bankaccounts_get_line` — Get a single bank account line
- `bankaccounts_update_line` — Update a bank account line
- `bankaccounts_delete_line` — Delete a bank account line
- `bankaccounts_get_balance` — Get the balance of a bank account

### 🚚 Supplier Orders (13 tools)
- `supplier_orders_list` — List all supplier orders
- `supplier_orders_get` — Get a supplier order by ID
- `supplier_orders_create` — Create a new supplier order
- `supplier_orders_update` — Update an existing supplier order
- `supplier_orders_delete` — Delete a supplier order by ID
- `supplier_orders_create_line` — Create a line on a supplier order
- `supplier_orders_get_contacts` — Get contacts for a supplier order
- `supplier_orders_add_contact` — Add a contact to a supplier order
- `supplier_orders_delete_contact` — Remove a contact from a supplier order
- `supplier_orders_validate` — Validate a supplier order
- `supplier_orders_approve` — Approve a supplier order
- `supplier_orders_receive` — Receive a supplier order

### 📋 Supplier Invoices (15 tools)
- `supplier_invoices_list` — List all supplier invoices
- `supplier_invoices_get` — Get a supplier invoice by ID
- `supplier_invoices_create` — Create a new supplier invoice
- `supplier_invoices_update` — Update an existing supplier invoice
- `supplier_invoices_delete` — Delete a supplier invoice by ID
- `supplier_invoices_get_lines` — Get lines of a supplier invoice
- `supplier_invoices_create_line` — Create a line on a supplier invoice
- `supplier_invoices_update_line` — Update a line on a supplier invoice
- `supplier_invoices_delete_line` — Delete a line from a supplier invoice
- `supplier_invoices_validate` — Validate a supplier invoice
- `supplier_invoices_settopaid` — Mark a supplier invoice as paid
- `supplier_invoices_get_payments` — Get payments for a supplier invoice
- `supplier_invoices_add_payment` — Add a payment to a supplier invoice

### 🤝 Supplier Proposals (5 tools)
- `supplier_proposals_list` — List all supplier proposals
- `supplier_proposals_get` — Get a supplier proposal by ID
- `supplier_proposals_create` — Create a new supplier proposal
- `supplier_proposals_update` — Update an existing supplier proposal
- `supplier_proposals_delete` — Delete a supplier proposal by ID

### 📜 Contracts (12 tools)
- `contracts_list` — List all contracts
- `contracts_get` — Get a contract by ID
- `contracts_create` — Create a new contract
- `contracts_update` — Update an existing contract
- `contracts_delete` — Delete a contract by ID
- `contracts_get_lines` — Get lines of a contract
- `contracts_create_line` — Create a line on a contract
- `contracts_update_line` — Update a line on a contract
- `contracts_activate_line` — Activate a contract line
- `contracts_delete_line` — Delete a line from a contract
- `contracts_validate` — Validate a contract
- `contracts_close` — Close a contract

### ⚙️ BOMs (8 tools)
- `boms_list` — List all bills of materials
- `boms_get` — Get a BOM by ID
- `boms_create` — Create a new BOM
- `boms_update` — Update an existing BOM
- `boms_delete` — Delete a BOM by ID
- `boms_get_lines` — Get lines of a BOM
- `boms_create_line` — Create a line on a BOM
- `boms_delete_line` — Delete a line from a BOM

### 🏗️ Manufacturing Orders (7 tools)
- `mos_list` — List all manufacturing orders
- `mos_get` — Get a manufacturing order by ID
- `mos_create` — Create a new manufacturing order
- `mos_update` — Update an existing manufacturing order
- `mos_delete` — Delete a manufacturing order by ID
- `mos_produce_and_consume` — Produce and consume for an MO
- `mos_get_categories` — Get categories for a manufacturing order

### 🎯 Projects (10 tools)
- `projects_list` — List all projects
- `projects_get` — Get a project by ID
- `projects_create` — Create a new project
- `projects_update` — Update an existing project
- `projects_delete` — Delete a project by ID
- `projects_get_tasks` — Get tasks for a project
- `projects_create_task` — Create a task in a project
- `projects_get_timespent` — Get time spent on a project
- `projects_validate` — Validate a project
- `projects_get_contacts` — Get contacts for a project

### 📌 Tasks (10 tools)
- `tasks_list` — List all tasks
- `tasks_get` — Get a task by ID
- `tasks_create` — Create a new task
- `tasks_update` — Update an existing task
- `tasks_delete` — Delete a task by ID
- `tasks_get_timespent` — Get time spent on a task
- `tasks_add_timespent` — Add time spent to a task
- `tasks_update_timespent` — Update time spent on a task
- `tasks_delete_timespent` — Delete time spent from a task
- `tasks_get_contacts` — Get contacts for a task

### 📦 Shipments (10 tools)
- `shipments_list` — List all shipments
- `shipments_get` — Get a shipment by ID
- `shipments_create` — Create a new shipment
- `shipments_update` — Update an existing shipment
- `shipments_delete` — Delete a shipment by ID
- `shipments_create_from_order` — Create a shipment from an order
- `shipments_validate` — Validate a shipment
- `shipments_close` — Close a shipment
- `shipments_setinvoiced` — Mark a shipment as invoiced
- `shipments_get_lines` — Get lines of a shipment

### 📥 Receptions (8 tools)
- `receptions_list` — List all receptions
- `receptions_get` — Get a reception by ID
- `receptions_create` — Create a new reception
- `receptions_update` — Update an existing reception
- `receptions_delete` — Delete a reception by ID
- `receptions_validate` — Validate a reception
- `receptions_close` — Close a reception
- `receptions_get_lines` — Get lines of a reception

### 🔧 Interventions (13 tools)
- `interventions_list` — List all interventions
- `interventions_get` — Get an intervention by ID
- `interventions_create` — Create a new intervention
- `interventions_update` — Update an existing intervention
- `interventions_delete` — Delete an intervention by ID
- `interventions_get_lines` — Get lines of an intervention
- `interventions_create_line` — Create a line on an intervention
- `interventions_update_line` — Update a line on an intervention
- `interventions_delete_line` — Delete a line from an intervention
- `interventions_settodraft` — Set an intervention to draft
- `interventions_validate` — Validate an intervention
- `interventions_close` — Close an intervention
- `interventions_get_contacts` — Get contacts for an intervention

### 💸 Expense Reports (15 tools)
- `expense_reports_list` — List all expense reports
- `expense_reports_get` — Get an expense report by ID
- `expense_reports_create` — Create a new expense report
- `expense_reports_update` — Update an existing expense report
- `expense_reports_delete` — Delete an expense report by ID
- `expense_reports_get_lines` — Get lines of an expense report
- `expense_reports_create_line` — Create a line on an expense report
- `expense_reports_update_line` — Update a line on an expense report
- `expense_reports_delete_line` — Delete a line from an expense report
- `expense_reports_settodraft` — Set an expense report to draft
- `expense_reports_validate` — Validate an expense report
- `expense_reports_approve` — Approve an expense report
- `expense_reports_deny` — Deny an expense report
- `expense_reports_setpaid` — Mark an expense report as paid
- `expense_reports_cancel` — Cancel an expense report

### 🏖️ Holidays (9 tools)
- `holidays_list` — List all holidays
- `holidays_get` — Get a holiday by ID
- `holidays_create` — Create a new holiday request
- `holidays_update` — Update an existing holiday request
- `holidays_delete` — Delete a holiday request by ID
- `holidays_validate` — Validate a holiday request
- `holidays_approve` — Approve a holiday request
- `holidays_cancel` — Cancel a holiday request
- `holidays_refuse` — Refuse a holiday request

### 📅 Agenda Events (5 tools)
- `agenda_events_list` — List all agenda events
- `agenda_events_get` — Get an agenda event by ID
- `agenda_events_create` — Create a new agenda event
- `agenda_events_update` — Update an existing agenda event
- `agenda_events_delete` — Delete an agenda event by ID

### 🗂️ Categories (10 tools)
- `categories_list` — List all categories
- `categories_get` — Get a category by ID
- `categories_create` — Create a new category
- `categories_update` — Update an existing category
- `categories_delete` — Delete a category by ID
- `categories_get_types` — Get category types
- `categories_get_for_object` — Get categories for an object
- `categories_link_object_by_id` — Link an object to a category by ID
- `categories_link_object_by_ref` — Link an object to a category by ref
- `categories_unlink_object` — Unlink an object from a category

### 📧 Mailings (6 tools)
- `mailings_list` — List all mailings
- `mailings_get` — Get a mailing by ID
- `mailings_create` — Create a new mailing
- `mailings_update` — Update an existing mailing
- `mailings_delete` — Delete a mailing by ID
- `mailings_validate` — Validate a mailing

### 💱 Multi Currencies (6 tools)
- `multi_currencies_list` — List all multi-currencies
- `multi_currencies_get` — Get a multi-currency by ID
- `multi_currencies_create` — Create a new multi-currency
- `multi_currencies_update` — Update an existing multi-currency
- `multi_currencies_delete` — Delete a multi-currency by ID
- `multi_currencies_get_rates` — Get rates for a multi-currency

### 🎫 Tickets (8 tools)
- `tickets_list` — List all tickets
- `tickets_get` — Get a ticket by ID
- `tickets_create` — Create a new ticket
- `tickets_update` — Update an existing ticket
- `tickets_delete` — Delete a ticket by ID
- `tickets_create_message` — Create a message on a ticket
- `tickets_add_contact` — Add a contact to a ticket
- `tickets_delete_contact` — Remove a contact from a ticket

### 🖥️ Workstations (2 tools)
- `workstations_list` — List all workstations
- `workstations_get` — Get a workstation by ID

### 🔗 Object Links (4 tools)
- `object_links_get` — Get an object link by ID
- `object_links_create` — Create a new object link
- `object_links_get_by_values` — Get object links by values
- `object_links_delete` — Delete an object link by ID

### 👥 Users (8 tools)
- `users_list` — List all users
- `users_get` — Get a user by ID
- `users_get_by_login` — Get a user by login
- `users_get_by_email` — Get a user by email
- `users_get_group` — Get a user group by ID
- `users_get_info` — Get current user info
- `users_list_groups` — List all user groups
- `users_get_user_groups` — Get groups for a user
