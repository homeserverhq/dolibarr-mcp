"""Fix all tool docstrings in main.py per spec Section 3E and 3I."""

import re
import sys

FILE = "src/main.py"

with open(FILE) as f:
    content = f.read()

lines = content.split("\n")
output = []
i = 0
tool_count = 0
fixed_count = 0

DATETIME_PARAMS = {
    "date", "date_debut", "date_fin", "date_start", "date_end",
    "datep", "datep2", "datepaye", "datev", "datem",
    "sellBy", "eatBy", "sellby", "eatby",
    "date_contrat", "date_planned", "date_delivery",
    "birthday", "datestart", "dateend", "delivery_date",
}

DESCS = {
    "id": "The unique ID of the resource",
    "lineid": "The line ID",
    "ref": "Reference",
    "label": "Label",
    "name": "Name",
    "lastname": "Last name",
    "firstname": "First name",
    "socid": "Third party ID",
    "fk_user": "User ID",
    "fk_user_author": "Author user ID",
    "fk_user_assign": "Assigned user ID",
    "fk_user_intervenant": "Intervening user ID",
    "fk_product": "Product ID",
    "fk_project": "Project ID",
    "fk_soc": "Third party ID",
    "fk_c_type_fees": "Fee type ID",
    "fk_source": "Source object ID",
    "fk_target": "Target object ID",
    "fk_type": "Leave type ID",
    "fk_socpeople": "Contact ID",
    "fk_warehouse": "Warehouse ID",
    "type": "Type",
    "type_code": "Event type code",
    "subject": "Subject",
    "title": "Title",
    "description": "Description",
    "address": "Street address",
    "zip": "Postal/ZIP code",
    "town": "City/town",
    "country_id": "Country ID",
    "country_code": "Country code",
    "phone": "Phone number",
    "phone_mobile": "Mobile phone number",
    "email": "Email address",
    "url": "Website URL",
    "skype": "Skype ID",
    "note": "Note",
    "note_public": "Public note",
    "note_private": "Private note",
    "status": "Status (1=active, 0=inactive)",
    "client": "Is a customer (1=yes, 0=no)",
    "fournisseur": "Is a supplier (1=yes, 0=no)",
    "code_client": "Customer code",
    "code_fournisseur": "Supplier code",
    "capital": "Company capital",
    "siren": "SIREN number",
    "siret": "SIRET number",
    "ape": "APE code",
    "tva_intra": "Intra-community VAT number",
    "parent": "Parent ID",
    "price_level": "Price level",
    "outstanding_limit": "Outstanding bill limit",
    "multicurrency_code": "Multi-currency code",
    "multicurrency_price": "Multi-currency price",
    "price": "Unit price",
    "total_ht": "Total before tax",
    "total_tva": "Total VAT",
    "total_ttc": "Total including tax",
    "price_base_type": "Price base type (HT or TTC)",
    "pmb": "PMP (average cost price)",
    "weight": "Weight",
    "weight_units": "Weight units",
    "length": "Length",
    "width": "Width",
    "height": "Height",
    "surface": "Surface area",
    "volume": "Volume",
    "barcode": "Barcode",
    "tva_tx": "VAT rate",
    "stock": "Stock quantity",
    "pmp": "Average cost price",
    "seuil_stock_alerte": "Stock alert threshold",
    "desiredstock": "Desired stock level",
    "accountancy_code_sell": "Accounting code for sales",
    "accountancy_code_buy": "Accounting code for purchases",
    "customcode": "Customs code",
    "duration_value": "Duration value",
    "duration_unit": "Duration unit",
    "duration": "Duration",
    "qty": "Quantity",
    "subprice": "Unit price",
    "remise_percent": "Discount percentage",
    "remise": "Discount amount",
    "product_type": "Product type (0=product, 1=service)",
    "rang": "Line position",
    "mode": "Filter mode",
    "category": "Category ID filter",
    "sqlfilters": "Dolibarr SQL filter syntax",
    "sortfield": "Field to sort by",
    "sortorder": "Sort order (ASC or DESC)",
    "limit": "Maximum number of results",
    "page": "Page number (0-based)",
    "include_all_fields": "When False (default), returns only commonly used fields. Set to True to retrieve all available fields.",
    "thirdparty_ids": "Comma-separated third party IDs",
    "modulepart": "Module type (e.g. invoice, order, product)",
    "variant_filter": "Variant filter",
    "selected_warehouse_id": "Warehouse ID filter",
    "batch": "Batch number",
    "warehouse_id": "Warehouse ID",
    "movementcode": "Movement code",
    "origin_type": "Origin object type",
    "origin_id": "Origin object ID",
    "comment": "Comment",
    "efficiency": "Efficiency rate",
    "budget_amount": "Budget amount",
    "usage_opportunity": "Usage opportunity flag",
    "usage_task": "Usage task flag",
    "usage_bill_time": "Usage bill time flag",
    "usage_organize_event": "Usage organize event flag",
    "public": "Public access flag",
    "percent": "Progress percentage",
    "planned_workload": "Planned workload",
    "progress": "Progress percentage",
    "product_id": "Product ID",
    "user_id": "User ID",
    "shipping_method_id": "Shipping method ID",
    "lieu": "Location",
    "fax": "Fax number",
    "accountancy_code": "Accounting code",
    "num_payment": "Payment number",
    "chqemetteur": "Check issuer",
    "chqbank": "Check bank",
    "closepaidinvoices": "Close paid invoices flag",
    "paymentid": "Payment type ID",
    "accountid": "Account ID",
    "author_user_id": "Author user ID",
    "userownerid": "Owner user ID",
    "location": "Location",
    "fulldayevent": "Full day event flag",
    "punctual": "Punctual event flag",
    "contactid": "Contact ID",
    "source": "Source",
    "notrigger": "Disable triggers flag",
    "close_code": "Close code",
    "close_note": "Close note",
    "discountid": "Discount ID",
    "force_number": "Force document number flag",
    "orderid": "Order ID",
    "proposalid": "Proposal ID",
    "amount_to": "Destination amount",
    "cheque_number": "Check number",
    "bankaccount_from_id": "Source bank account ID",
    "bankaccount_to_id": "Destination bank account ID",
    "amount": "Amount",
    "code_banque": "Bank code",
    "code_guichet": "Branch code",
    "cle_rib": "RIB key",
    "bic": "BIC code",
    "iban": "IBAN",
    "domiciliation": "Bank branch address",
    "state_id": "State/region ID",
    "opening_balance": "Opening balance",
    "min_balance": "Minimum balance",
    "proprio": "Owner",
    "accountancycode": "Accounting code",
    "num_releve": "Statement number",
    "cheque_writer": "Check writer",
    "line_id": "Line ID",
    "payment_mode_id": "Payment mode ID",
    "sourcetype": "Source object type",
    "targettype": "Target object type",
    "relationtype": "Relation type",
    "idwarehouse": "Warehouse ID",
    "secondlevel": "Second approval level flag",
    "closeopenorder": "Close open order flag",
    "type_contact": "Contact type",
    "object_id": "Object ID",
    "object_ref": "Object reference",
    "mail_template_id": "Mail template ID",
    "mail_subject": "Mail subject",
    "sujet": "Subject",
    "body": "Body",
    "email_from": "From email",
    "email_to": "To email",
    "email_cc": "CC email",
    "email_bcc": "BCC email",
    "lang": "Language code",
    "track_id": "Track ID",
    "severity_code": "Severity code",
    "category_code": "Category code",
    "origin": "Origin",
    "message": "Message",
    "ticket_id": "Ticket ID",
    "rate": "Exchange rate",
    "color": "Color",
    "details": "Details",
    "detail": "Detail",
    "detail_refuse": "Refusal detail",
    "include_childs": "Include child categories flag",
    "includepermissions": "Include permissions flag",
    "includetimespent": "Include time spent flag",
    "user_ids": "Comma-separated user IDs",
    "product_ids": "Comma-separated product IDs",
    "halfday": "Half day flag (0=full, 1=morning, 2=afternoon)",
    "poste": "Job position",
    "default_lang": "Default language code",
    "bom_id": "BOM ID",
    "priority": "Priority",
    "payment_terms": "Payment terms",
    "fk_account": "Bank account ID",
    "label_contrat": "Contract label",
    "description_contrat": "Contract description",
    "fk_contract": "Contract ID",
    "fk_bom": "BOM ID",
    "fk_mo": "Manufacturing order ID",
    "qty_produced": "Produced quantity",
    "qty_to_produce": "Quantity to produce",
    "bom_line_id": "BOM line ID",
    "mo_type": "Manufacturing order type",
    "fk_warehouse_source": "Source warehouse ID",
    "fk_warehouse_destination": "Destination warehouse ID",
    "fk_mission": "Mission ID",
    "fk_c_type_fees": "Fee type ID",
    "comments": "Comments",
    "fk_user_valid": "Validating user ID",
    "fk_site": "Site ID",
    "sessid": "Session ID",
    "fk_c_type_intervention": "Intervention type ID",
    "fk_c_type_fees": "Fee type ID",
    "fk_c_type_holiday": "Holiday type ID",
    "holiday_type": "Holiday type",
    "date_debut": "Start date",
    "date_fin": "End date",
    "date_start": "Start date",
    "date_end": "End date",
    "datep": "Start date/time",
    "datep2": "End date/time",
    "delivery_date": "Delivery date",
    "date_contrat": "Contract date",
    "date_planned": "Planned date",
    "datem": "Manufacturing date",
    "sellBy": "Sell-by date",
    "eatBy": "Eat-by date",
    "sellby": "Sell-by date",
    "eatby": "Eat-by date",
    "birthday": "Birthday",
    "datepaye": "Payment date",
    "datev": "Value date",
    "date_delivery": "Delivery date",
    "country": "Country",
    "region": "Region",
    "fk_c_country": "Country ID",
    "fk_departement": "Department ID",
    "canvas": "Canvas",
    "import_key": "Import key",
    "model_pdf": "PDF model",
    "model_mail": "Mail model",
    "note": "Note",
    "note_public": "Public note",
    "note_private": "Private note",
    "total": "Total amount",
    "revenuestamp": "Revenue stamp",
    "type": "Type",
    "status": "Status",
    "mode": "Mode",
}


def get_description(param_name, default_repr, is_required, is_datetime):
    if is_datetime:
        return "Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00)"
    if param_name in DESCS:
        return DESCS[param_name]
    return param_name.replace("_", " ").title()


def is_datetime_param(name):
    return name in DATETIME_PARAMS


def parse_params(sig):
    """Parse a Python function signature and return list of (name, type, default, is_required)."""
    # Find the opening paren
    paren_depth = 0
    start = -1
    for idx, ch in enumerate(sig):
        if ch == "(" and paren_depth == 0:
            start = idx + 1
            paren_depth = 1
        elif ch == "(":
            paren_depth += 1
        elif ch == ")":
            paren_depth -= 1
            if paren_depth == 0 and start != -1:
                end = idx
                break
    else:
        return []

    params_str = sig[start:end]

    # Split by commas respecting nesting
    parts = []
    depth = 0
    cur = []
    for ch in params_str:
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            cur.append(ch)
    rest = "".join(cur).strip()
    if rest:
        parts.append(rest)

    result = []
    for p in parts:
        if not p:
            continue
        # Split on first ':' that is not inside brackets
        colon_idx = -1
        depth = 0
        for idx, ch in enumerate(p):
            if ch == ":" and depth == 0:
                colon_idx = idx
                break
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
        if colon_idx == -1:
            continue

        name = p[:colon_idx].strip()
        rest_part = p[colon_idx + 1:].strip()

        if name == "ctx":
            continue

        # Find '=' for default value, respecting nesting
        eq_idx = -1
        depth = 0
        for idx, ch in enumerate(rest_part):
            if ch == "=" and depth == 0:
                eq_idx = idx
                break
            elif ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1

        if eq_idx != -1:
            ptype = rest_part[:eq_idx].strip()
            pdefault = rest_part[eq_idx + 1:].strip()
            if pdefault.endswith(","):
                pdefault = pdefault[:-1].strip()
            is_required = False
        else:
            ptype = rest_part
            pdefault = None
            is_required = True
            if ptype.endswith(","):
                ptype = ptype[:-1].strip()

        result.append((name, ptype, pdefault, is_required))

    return result


def generate_docstring(func_name, params):
    """Generate a proper docstring for a tool function per spec Section 3E."""
    required = []
    optional = []
    for pname, ptype, pdefault, is_required in params:
        desc = get_description(pname, pdefault, is_required, is_datetime_param(pname))
        if is_required:
            required.append(f"        {pname}: {desc} (required).")
        else:
            optional.append(f"        {pname}: {desc}")

    # Generate one-line description from function name
    desc_line = func_name.replace("_", " ").title() + "."
    lines = [f"    \"\"\"{desc_line}"]
    if required or optional:
        lines.append("")
        lines.append("    Args:")
        lines.extend(required)
        lines.extend(optional)
    lines.append('    """')
    return "\n".join(lines)


FUNC_DESC_OVERRIDES = {
    "status_get": "Check connectivity to the Dolibarr backend.",
    "documents_list": "List documents/attachments for a given element.",
    "thirdparties_list": "List all third parties (customers, suppliers, prospects).",
    "thirdparties_get": "Get a single third party by ID.",
    "thirdparties_create": "Create a new third party.",
    "thirdparties_update": "Update an existing third party.",
    "thirdparties_delete": "Delete a third party by ID.",
    "thirdparties_get_outstanding_proposals": "Get outstanding proposals for a third party.",
    "thirdparties_get_outstanding_orders": "Get outstanding orders for a third party.",
    "thirdparties_get_outstanding_invoices": "Get outstanding invoices for a third party.",
    "thirdparties_get_representatives": "Get representatives for a third party.",
    "thirdparties_get_categories": "Get categories for a third party.",
    "contacts_list": "List all contacts.",
    "contacts_get": "Get a single contact by ID.",
    "contacts_create": "Create a new contact.",
    "contacts_update": "Update an existing contact.",
    "contacts_delete": "Delete a contact by ID.",
    "contacts_get_categories": "Get categories for a contact.",
    "products_list": "List all products/services.",
    "products_get": "Get a single product by ID.",
    "products_create": "Create a new product or service.",
    "products_update": "Update an existing product.",
    "products_delete": "Delete a product by ID.",
    "products_get_subproducts": "Get sub-products for a product.",
    "products_get_categories": "Get categories for a product.",
    "products_get_stock": "Get stock information for a product.",
    "products_get_contacts": "Get contacts linked to a product.",
    "warehouses_list": "List all warehouses.",
    "warehouses_get": "Get a single warehouse by ID.",
    "warehouses_create": "Create a new warehouse.",
    "warehouses_update": "Update an existing warehouse.",
    "warehouses_delete": "Delete a warehouse by ID.",
    "warehouses_list_products": "List products in a warehouse.",
    "stockmovements_list": "List all stock movements.",
    "stockmovements_get": "Get a single stock movement by ID.",
    "stockmovements_create": "Create a new stock movement.",
    "stockmovements_update": "Update an existing stock movement.",
    "stockmovements_delete": "Delete a stock movement by ID.",
    "productlots_list": "List all product lots/batches.",
    "productlots_get": "Get a single product lot by ID.",
    "productlots_create": "Create a new product lot/batch.",
    "productlots_update": "Update an existing product lot.",
    "productlots_delete": "Delete a product lot by ID.",
    "proposals_list": "List all commercial proposals.",
    "proposals_get": "Get a single proposal by ID.",
    "proposals_create": "Create a new commercial proposal.",
    "proposals_update": "Update an existing proposal.",
    "proposals_delete": "Delete a proposal by ID.",
    "proposals_get_lines": "Get lines for a proposal.",
    "proposals_create_line": "Add a line to a proposal.",
    "proposals_update_line": "Update a line in a proposal.",
    "proposals_delete_line": "Delete a line from a proposal.",
    "proposals_settodraft": "Set a proposal to draft status.",
    "proposals_validate": "Validate a proposal.",
    "proposals_close": "Close a proposal.",
    "proposals_setinvoiced": "Set a proposal as invoiced.",
    "proposals_get_contacts": "Get contacts linked to a proposal.",
    "proposals_add_contact": "Add a contact to a proposal.",
    "orders_list": "List all customer orders.",
    "orders_get": "Get a single order by ID.",
    "orders_create": "Create a new customer order.",
    "orders_update": "Update an existing order.",
    "orders_delete": "Delete an order by ID.",
    "orders_get_lines": "Get lines for an order.",
    "orders_get_line": "Get a single line from an order.",
    "orders_create_line": "Add a line to an order.",
    "orders_update_line": "Update a line in an order.",
    "orders_delete_line": "Delete a line from an order.",
    "orders_settodraft": "Set an order to draft status.",
    "orders_validate": "Validate an order.",
    "orders_close": "Close an order.",
    "orders_reopen": "Reopen a closed order.",
    "orders_setinvoiced": "Set an order as invoiced.",
    "orders_create_from_proposal": "Create an order from a proposal.",
    "orders_get_shipments": "Get shipments for an order.",
    "orders_create_shipment": "Create a shipment from an order.",
    "orders_get_contacts": "Get contacts linked to an order.",
    "invoices_list": "List all customer invoices.",
    "invoices_get": "Get a single invoice by ID.",
    "invoices_create": "Create a new customer invoice.",
    "invoices_update": "Update an existing invoice.",
    "invoices_delete": "Delete an invoice by ID.",
    "invoices_get_lines": "Get lines for an invoice.",
    "invoices_create_line": "Add a line to an invoice.",
    "invoices_update_line": "Update a line in an invoice.",
    "invoices_delete_line": "Delete a line from an invoice.",
    "invoices_create_from_order": "Create an invoice from an order.",
    "invoices_settodraft": "Set an invoice to draft status.",
    "invoices_validate": "Validate an invoice.",
    "invoices_settopaid": "Set an invoice as paid.",
    "invoices_settounpaid": "Set an invoice as unpaid.",
    "invoices_get_payments": "Get payments for an invoice.",
    "invoices_add_payment": "Add a payment to an invoice.",
    "invoices_get_contacts": "Get contacts linked to an invoice.",
    "invoices_add_contact": "Add a contact to an invoice.",
    "invoices_delete_contact": "Delete a contact from an invoice.",
    "invoices_get_discount": "Get available discount for an invoice.",
    "invoices_use_discount": "Apply a discount to an invoice.",
    "payments_list": "List all customer payments.",
    "payments_get": "Get a single payment by ID.",
    "payments_create": "Create a new customer payment.",
    "payments_delete": "Delete a payment by ID.",
    "payments_get_lines": "Get lines for a payment.",
    "payments_create_line": "Add a line to a payment.",
    "payments_update_line": "Update a line in a payment.",
    "payments_delete_line": "Delete a line from a payment.",
    "bankaccounts_list": "List all bank accounts.",
    "bankaccounts_get": "Get a single bank account by ID.",
    "bankaccounts_create": "Create a new bank account.",
    "bankaccounts_update": "Update an existing bank account.",
    "bankaccounts_delete": "Delete a bank account by ID.",
    "bankaccounts_list_lines": "List lines for a bank account.",
    "bankaccounts_create_line": "Add a line to a bank account.",
    "bankaccounts_update_line": "Update a line in a bank account.",
    "bankaccounts_delete_line": "Delete a line from a bank account.",
    "bankaccounts_create_transfer": "Create a bank transfer between accounts.",
    "supplierorders_list": "List all supplier orders.",
    "supplierorders_get": "Get a single supplier order by ID.",
    "supplierorders_create": "Create a new supplier order.",
    "supplierorders_update": "Update an existing supplier order.",
    "supplierorders_delete": "Delete a supplier order by ID.",
    "supplierorders_get_lines": "Get lines for a supplier order.",
    "supplierorders_create_line": "Add a line to a supplier order.",
    "supplierorders_update_line": "Update a line in a supplier order.",
    "supplierorders_delete_line": "Delete a line from a supplier order.",
    "supplierorders_validate": "Validate a supplier order.",
    "supplierorders_approve": "Approve a supplier order.",
    "supplierorders_reopen": "Reopen a supplier order.",
    "supplierorders_settodraft": "Set a supplier order to draft status.",
    "supplierorders_get_contacts": "Get contacts linked to a supplier order.",
    "supplierinvoices_list": "List all supplier invoices.",
    "supplierinvoices_get": "Get a single supplier invoice by ID.",
    "supplierinvoices_create": "Create a new supplier invoice.",
    "supplierinvoices_update": "Update an existing supplier invoice.",
    "supplierinvoices_delete": "Delete a supplier invoice by ID.",
    "supplierinvoices_get_lines": "Get lines for a supplier invoice.",
    "supplierinvoices_create_line": "Add a line to a supplier invoice.",
    "supplierinvoices_update_line": "Update a line in a supplier invoice.",
    "supplierinvoices_delete_line": "Delete a line from a supplier invoice.",
    "supplierinvoices_settodraft": "Set a supplier invoice to draft status.",
    "supplierinvoices_validate": "Validate a supplier invoice.",
    "supplierinvoices_settopaid": "Set a supplier invoice as paid.",
    "supplierinvoices_settounpaid": "Set a supplier invoice as unpaid.",
    "supplierinvoices_get_payments": "Get payments for a supplier invoice.",
    "supplierinvoices_add_payment": "Add a payment to a supplier invoice.",
    "supplierinvoices_get_contacts": "Get contacts linked to a supplier invoice.",
    "supplierinvoices_add_contact": "Add a contact to a supplier invoice.",
    "supplierinvoices_delete_contact": "Delete a contact from a supplier invoice.",
    "supplierproposals_list": "List all supplier proposals.",
    "supplierproposals_get": "Get a single supplier proposal by ID.",
    "supplierproposals_create": "Create a new supplier proposal.",
    "supplierproposals_update": "Update an existing supplier proposal.",
    "supplierproposals_delete": "Delete a supplier proposal by ID.",
    "supplierproposals_get_lines": "Get lines for a supplier proposal.",
    "supplierproposals_create_line": "Add a line to a supplier proposal.",
    "supplierproposals_update_line": "Update a line in a supplier proposal.",
    "supplierproposals_delete_line": "Delete a line from a supplier proposal.",
    "supplierproposals_settodraft": "Set a supplier proposal to draft status.",
    "supplierproposals_validate": "Validate a supplier proposal.",
    "supplierproposals_setinvoiced": "Set a supplier proposal as invoiced.",
    "supplierproposals_get_contacts": "Get contacts linked to a supplier proposal.",
    "contracts_list": "List all contracts.",
    "contracts_get": "Get a single contract by ID.",
    "contracts_create": "Create a new contract.",
    "contracts_update": "Update an existing contract.",
    "contracts_delete": "Delete a contract by ID.",
    "contracts_get_lines": "Get lines for a contract.",
    "contracts_create_line": "Add a line to a contract.",
    "contracts_create_activate_line": "Activate a contract line.",
    "contracts_validate": "Validate a contract.",
    "contracts_settodraft": "Set a contract to draft status.",
    "contracts_get_contacts": "Get contacts linked to a contract.",
    "boms_list": "List all bills of materials.",
    "boms_get": "Get a single BOM by ID.",
    "boms_create": "Create a new bill of materials.",
    "boms_update": "Update an existing BOM.",
    "boms_delete": "Delete a BOM by ID.",
    "boms_get_lines": "Get lines for a BOM.",
    "boms_create_line": "Add a line to a BOM.",
    "boms_update_line": "Update a line in a BOM.",
    "boms_delete_line": "Delete a line from a BOM.",
    "boms_validate": "Validate a BOM.",
    "manufacturingorders_list": "List all manufacturing orders.",
    "manufacturingorders_get": "Get a single manufacturing order by ID.",
    "manufacturingorders_create": "Create a new manufacturing order.",
    "manufacturingorders_update": "Update an existing manufacturing order.",
    "manufacturingorders_delete": "Delete a manufacturing order by ID.",
    "manufacturingorders_get_lines": "Get lines for a manufacturing order.",
    "manufacturingorders_create_line": "Add a line to a manufacturing order.",
    "manufacturingorders_update_line": "Update a line in a manufacturing order.",
    "manufacturingorders_delete_line": "Delete a line from a manufacturing order.",
    "manufacturingorders_produce": "Record production for a manufacturing order.",
    "manufacturingorders_validate": "Validate a manufacturing order.",
    "projects_list": "List all projects.",
    "projects_get": "Get a single project by ID.",
    "projects_create": "Create a new project.",
    "projects_update": "Update an existing project.",
    "projects_delete": "Delete a project by ID.",
    "projects_get_tasks": "Get tasks for a project.",
    "projects_get_contacts": "Get contacts linked to a project.",
    "tasks_list": "List all project tasks.",
    "tasks_get": "Get a single task by ID.",
    "tasks_create": "Create a new project task.",
    "tasks_update": "Update an existing task.",
    "tasks_delete": "Delete a task by ID.",
    "tasks_add_timespent": "Add time spent to a task.",
    "tasks_get_timespent": "Get time spent entries for a task.",
    "tasks_get_contacts": "Get contacts linked to a task.",
    "shipments_list": "List all shipments.",
    "shipments_get": "Get a single shipment by ID.",
    "shipments_create": "Create a new shipment.",
    "shipments_update": "Update an existing shipment.",
    "shipments_delete": "Delete a shipment by ID.",
    "shipments_get_lines": "Get lines for a shipment.",
    "shipments_create_line": "Add a line to a shipment.",
    "shipments_update_line": "Update a line in a shipment.",
    "shipments_delete_line": "Delete a line from a shipment.",
    "shipments_validate": "Validate a shipment.",
    "shipments_close": "Close a shipment.",
    "shipments_get_contacts": "Get contacts linked to a shipment.",
    "receptions_list": "List all receptions.",
    "receptions_get": "Get a single reception by ID.",
    "receptions_create": "Create a new reception.",
    "receptions_update": "Update an existing reception.",
    "receptions_delete": "Delete a reception by ID.",
    "receptions_get_lines": "Get lines for a reception.",
    "receptions_create_line": "Add a line to a reception.",
    "receptions_update_line": "Update a line in a reception.",
    "receptions_delete_line": "Delete a line from a reception.",
    "receptions_validate": "Validate a reception.",
    "receptions_get_contacts": "Get contacts linked to a reception.",
    "interventions_list": "List all interventions.",
    "interventions_get": "Get a single intervention by ID.",
    "interventions_create": "Create a new intervention.",
    "interventions_update": "Update an existing intervention.",
    "interventions_delete": "Delete an intervention by ID.",
    "interventions_get_lines": "Get lines for an intervention.",
    "interventions_create_line": "Add a line to an intervention.",
    "interventions_update_line": "Update a line in an intervention.",
    "interventions_delete_line": "Delete a line from an intervention.",
    "interventions_settodraft": "Set an intervention to draft status.",
    "interventions_validate": "Validate an intervention.",
    "interventions_get_contacts": "Get contacts linked to an intervention.",
    "expensereports_list": "List all expense reports.",
    "expensereports_get": "Get a single expense report by ID.",
    "expensereports_create": "Create a new expense report.",
    "expensereports_update": "Update an existing expense report.",
    "expensereports_delete": "Delete an expense report by ID.",
    "expensereports_get_lines": "Get lines for an expense report.",
    "expensereports_create_line": "Add a line to an expense report.",
    "expensereports_update_line": "Update a line in an expense report.",
    "expensereports_delete_line": "Delete a line from an expense report.",
    "expensereports_validate": "Validate an expense report.",
    "expensereports_settopaid": "Set an expense report as paid.",
    "expensereports_get_contacts": "Get contacts linked to an expense report.",
    "holidays_list": "List all leave/holiday requests.",
    "holidays_get": "Get a single leave request by ID.",
    "holidays_create": "Create a new leave/holiday request.",
    "holidays_update": "Update an existing leave request.",
    "holidays_delete": "Delete a leave request by ID.",
    "holidays_validate": "Validate a leave request.",
    "holidays_approve": "Approve a leave request.",
    "holidays_reject": "Reject a leave request.",
    "agendaevents_list": "List all agenda events.",
    "agendaevents_get": "Get a single agenda event by ID.",
    "agendaevents_create": "Create a new agenda event.",
    "agendaevents_update": "Update an existing agenda event.",
    "agendaevents_delete": "Delete an agenda event by ID.",
    "agendaevents_get_contacts": "Get contacts linked to an agenda event.",
    "categories_list": "List all categories.",
    "categories_get": "Get a single category by ID.",
    "categories_create": "Create a new category.",
    "categories_update": "Update an existing category.",
    "categories_delete": "Delete a category by ID.",
    "categories_get_objects": "Get objects linked to a category.",
    "mailings_list": "List all mailings.",
    "mailings_get": "Get a single mailing by ID.",
    "mailings_create": "Create a new mailing.",
    "mailings_update": "Update an existing mailing.",
    "mailings_delete": "Delete a mailing by ID.",
    "mailings_send": "Send a mailing.",
    "multicurrencies_list": "List all multi-currency rates.",
    "multicurrencies_get": "Get a single multi-currency rate by ID.",
    "multicurrencies_create": "Create a new multi-currency rate.",
    "multicurrencies_update": "Update an existing multi-currency rate.",
    "multicurrencies_delete": "Delete a multi-currency rate by ID.",
    "tickets_list": "List all tickets.",
    "tickets_get": "Get a single ticket by ID.",
    "tickets_create": "Create a new ticket.",
    "tickets_update": "Update an existing ticket.",
    "tickets_delete": "Delete a ticket by ID.",
    "tickets_create_message": "Add a message to a ticket.",
    "tickets_get_contacts": "Get contacts linked to a ticket.",
    "workstations_list": "List all workstations.",
    "workstations_get": "Get a single workstation by ID.",
    "workstations_create": "Create a new workstation.",
    "workstations_update": "Update an existing workstation.",
    "workstations_delete": "Delete a workstation by ID.",
    "objectlinks_list": "List all object links.",
    "objectlinks_get": "Get a single object link by ID.",
    "objectlinks_create": "Create a new object link.",
    "objectlinks_delete": "Delete an object link by ID.",
    "users_list": "List all users.",
    "users_get": "Get a single user by ID.",
    "users_create": "Create a new user.",
    "users_update": "Update an existing user.",
    "users_delete": "Delete a user by ID.",
    "users_get_groups": "Get groups for a user.",
    "users_add_group": "Add a user to a group.",
    "users_remove_group": "Remove a user from a group.",
}

def generate_docstring_v2(func_name, params):
    """Generate a proper docstring for a tool function per spec Section 3E."""
    required = []
    optional = []
    for pname, ptype, pdefault, is_required in params:
        desc = get_description(pname, pdefault, is_required, is_datetime_param(pname)).rstrip(".")
        if is_required:
            required.append(f"        {pname}: {desc} (required).")
        else:
            optional.append(f"        {pname}: {desc}.")

    desc_line = FUNC_DESC_OVERRIDES.get(func_name, func_name.replace("_", " ").title() + ".")
    lines = [f"    \"\"\"{desc_line}"]
    if required or optional:
        lines.append("")
        lines.append("    Args:")
        lines.extend(required)
        lines.extend(optional)
    lines.append('    """')
    return "\n".join(lines)


# Process the file line by line
while i < len(lines):
    line = lines[i]

    if line.strip() == "@mcp.tool()":
        tool_count += 1
        output.append(line)
        i += 1

        # Skip blank/comment lines until async def
        while i < len(lines) and not lines[i].strip().startswith("async def "):
            output.append(lines[i])
            i += 1

        if i < len(lines):
            func_name_match = re.match(r"\s*async def (\w+)\(", lines[i])
            func_name = func_name_match.group(1) if func_name_match else "unknown"

            # Collect and output signature lines
            sig_lines = []
            while i < len(lines):
                sig_lines.append(lines[i])
                output.append(lines[i])
                i += 1
                if "-> dict[str, Any]:" in sig_lines[-1]:
                    break

            # i now points to line after return type — check for docstring
            if i < len(lines):
                stripped = lines[i].strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    doc_start = i
                    # Determine docstring end
                    if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                        doc_end = i  # one-liner
                    else:
                        doc_end = i
                        # Find closing quotes
                        quote_char = '"""' if '"""' in stripped else "'''"
                        doc_end += 1
                        while doc_end < len(lines):
                            if quote_char in lines[doc_end]:
                                break
                            doc_end += 1

                    # Generate new docstring
                    full_sig = "\n".join(sig_lines)
                    all_params = parse_params(full_sig)

                    if all_params:
                        new_docstring = generate_docstring_v2(func_name, all_params)
                        output.append(new_docstring)
                        fixed_count += 1
                    else:
                        # No non-ctx params — preserve original docstring
                        for j in range(doc_start, doc_end + 1):
                            output.append(lines[j])

                    # Move past old docstring
                    i = doc_end + 1
                    continue

        # If no async def found or no docstring after sig, continue from current i
        continue

    output.append(lines[i])
    i += 1

result = "\n".join(output)
with open(FILE, "w") as f:
    f.write(result)

print(f"Processed {tool_count} tools, fixed {fixed_count} docstrings")
