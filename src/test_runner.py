"""
Zero-branch test runner for Dolibarr MCP Server.
One flat list. One loop. Zero if/and/or/isinstance/ternary.
"""
import json, os, re, sys, time, uuid, httpx

MCP_URL = f"http://localhost:{os.environ.get('MCP_SERVER_PORT','6033')}/mcp"
HDR = {"Authorization": f"Bearer {os.environ.get('API_KEY','')}", "Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
rid = uuid.uuid4().hex[:8]
store = {}
results = []

def now():
    return time.strftime('%Y-%m-%dT%H:%M:%S+00:00')

# HARDCODED: System seed data IDs (guaranteed by base install)
# These are unavoidable hardcoded values — documented here to stand out.
store["payment_type_id.id"] = "1"
store["expense_type_id.id"] = "1"
store["holiday_type_id.id"] = "1"
# HARDCODED: Workstations — API rejects create/delete on seed data,
# so all read/update/list operations reference existing seed ID 1.
store["workstation.id"] = "1"
# Pre-computed truncated codes (Python expressions evaluated at module load)
_CODE_MC = rid[-3:]

# Pre-computed entity codes (Python expressions, not format placeholders)
_CODE_CLIENT = f"CU{time.strftime('%y%m')}-{rid[-4:]}"
_CODE_FOURN = f"SU{time.strftime('%y%m')}-{rid[-4:]}"

ALL_TESTS = [
    # ===== Phase 0-1: Status =====
    ("A1 status_get", "status_get", '{}', "last", ""),

    # ===== Phase 3.5: Reference Data Discovery (formally tested) =====
    ("B3 payment_types_list", "payment_types_list", '{}', "last", ""),
    ("B3 expense_types_list", "expense_types_list", '{}', "last", ""),
    ("B3 holiday_types_list", "holiday_types_list", '{}', "last", ""),

    # ===== Phase 3A: Creates (store populated with ALL response fields) =====
    ("C1 create_products", "products_create", '{"ref": "t{rid}-PROD", "label": "t{rid}-Product", "type": 0, "status": 1, "price": 10.0, "price_base_type": "HT"}', "product", ""),
    ("C1 create_thirdparty", "thirdparties_create", '{"name": "t{rid}-TP", "client": 1, "fournisseur": 1, "code_client": "' + _CODE_CLIENT + '", "code_fournisseur": "' + _CODE_FOURN + '"}', "thirdparty", ""),
    ("C1 create_contacts", "contacts_create", '{"lastname": "t{rid}-L", "socid": {thirdparty.id}, "firstname": "Test"}', "contact", ""),
    ("C1 create_warehouses", "warehouses_create", '{"ref": "t{rid}-WH", "label": "t{rid}-Warehouse", "status": 1}', "warehouse", ""),
    ("C1 create_bankaccounts", "bankaccounts_create", '{"ref": "t{rid}-BA", "label": "t{rid}-Bank", "type": 0, "currency_code": "EUR", "account_number": "FR7630001007941234567890185", "country_id": 1}', "bankaccount", ""),
    ("C1 create_stockmovements", "stockmovements_create", '{"product_id": {product.id}, "warehouse_id": {warehouse.id}, "qty": 10.0, "type": 0, "label": "t{rid}-Movement", "batch": "test-batch-001"}', "stockmovement", ""),
    ("C1 create_productlots", "productlots_create", '{"ref": "t{rid}-LOT", "fk_product": {product.id}, "batch": "BATCH-001"}', "productlot", ""),
    ("C1 create_proposals", "proposals_create", '{"socid": {thirdparty.id}, "date": "{now}"}', "proposal", ""),
    ("C1 create_orders", "orders_create", '{"socid": {thirdparty.id}, "date": "{now}"}', "order", ""),
    ("C1 create_invoices", "invoices_create", '{"socid": {thirdparty.id}, "date": "{now}", "type": 0}', "invoice", ""),
    ("C1 create_payments", "payments_create", '{"datepaye": "{now}", "paymentid": {payment_type_id.id}, "amount": 10.0, "accountid": {bankaccount.id}, "socid": {thirdparty.id}}', "payment", ""),
    ("C1 create_supplier_orders", "supplier_orders_create", '{"socid": {thirdparty.id}, "date": "{now}"}', "supplier_order", ""),
    ("C1 create_supplier_invoices", "supplier_invoices_create", '{"socid": {thirdparty.id}, "date": "{now}"}', "supplier_invoice", ""),
    ("C1 create_supplier_proposals", "supplier_proposals_create", '{"socid": {thirdparty.id}, "date": "{now}"}', "supplier_proposal", ""),
    ("C1 create_contracts", "contracts_create", '{"socid": {thirdparty.id}, "ref": "t{rid}-CT", "date_contrat": "{now}", "commercial_signature_id": {contact.id}, "commercial_suivi_id": {contact.id}}', "contract", ""),
    ("C1 create_boms", "boms_create", '{"ref": "t{rid}-BOM", "label": "t{rid}-BillOfMaterials", "fk_product": {product.id}, "qty": 1.0, "bomtype": 0, "status": 0}', "bom", ""),
    ("C1 create_mos", "mos_create", '{"ref": "t{rid}-MO", "label": "t{rid}-ManufOrder", "fk_product": {product.id}, "qty": 5.0, "fk_warehouse": {warehouse.id}, "mrptype": 0, "status": 0}', "mo", ""),
    ("C1 create_projects", "projects_create", '{"ref": "t{rid}-PRJ", "title": "t{rid}-Project"}', "project", ""),
    ("C1 create_tasks", "tasks_create", '{"ref": "t{rid}-TSK", "label": "t{rid}-Task", "fk_project": {project.id}}', "task", ""),
    ("C1 create_shipments", "shipments_create", '{"socid": {thirdparty.id}, "ref": "t{rid}-SHP", "origin_id": {order.id}, "origin_type": "commande"}', "shipment", ""),
    ("C1 create_receptions", "receptions_create", '{"socid": {thirdparty.id}, "ref": "t{rid}-REC", "origin_id": {supplier_order.id}, "origin_type": "commande_fournisseur"}', "reception", ""),
    ("C1 create_interventions", "interventions_create", '{"socid": {thirdparty.id}, "ref": "t{rid}-IN"}', "intervention", ""),
    ("C1 create_users", "users_create", '{"login": "t{rid}-user", "email": "t{rid}-u@test.com", "password": "test1234", "lastname": "t{rid}-Last", "firstname": "t{rid}-First"}', "user", ""),
    ("C1 create_expense_reports", "expense_reports_create", '{"fk_user": {user.id}, "date_debut": "2026-06-01T12:00:00+00:00", "date_fin": "2026-06-22T12:00:00+00:00", "fk_user_author": {user.id}}', "expense_report", ""),
    ("C1 create_holidays", "holidays_create", '{"fk_user": {user.id}, "date_debut": "2026-07-01T00:00:00+00:00", "date_fin": "2026-07-05T00:00:00+00:00", "halfday": 0, "fk_type": {holiday_type_id.id}, "note": "t{rid}-Holiday", "fk_validator": {user.id}}', "holiday", ""),
    ("C1 create_agenda_events", "agenda_events_create", '{"type_code": "AC_OTH", "datep": "{now}", "label": "t{rid}-Event"}', "agenda_event", ""),
    ("C1 create_categories", "categories_create", '{"ref": "t{rid}-CAT", "label": "t{rid}-Category", "type": "product"}', "category", ""),
    ("C1 create_mailings", "mailings_create", '{"title": "t{rid}-Mailing", "sujet": "Test Sujet", "body": "Test email body", "email_from": "test@example.com"}', "mailing", ""),
    ("C1 create_multi_currencies", "multi_currencies_create", '{"code": "' + _CODE_MC + '", "name": "t{rid}-Currency", "rate": 1.0}', "multi_currency", ""),
    ("C1 create_tickets", "tickets_create", '{"subject": "t{rid}-Ticket", "type_code": "COM", "severity_code": "MINOR", "category_code": "OTH"}', "ticket", ""),
    ("C1 create_groups", "groups_create", '{"name": "t{rid}-GRP"}', "group", ""),
    ("C1 create_workstations", "workstations_create", '{"label": "t{rid}-WS", "status": 1}', "workstation", ""),
    ("C1 create_objectlinks", "object_links_create", '{"fk_source": {proposal.id}, "sourcetype": "propal", "fk_target": {order.id}, "targettype": "commande", "relationtype": "link"}', "object_link", ""),

    # ===== Phase 3A.5: Fetches (GET overwrites store with verified data) =====
    ("C1b fetch_products", "products_get", '{"id": {product.id}}', "product", ""),
    ("C1b fetch_thirdparty", "thirdparties_get", '{"id": {thirdparty.id}}', "thirdparty", ""),
    ("C1b fetch_contacts", "contacts_get", '{"id": {contact.id}}', "contact", ""),
    ("C1b fetch_warehouses", "warehouses_get", '{"id": {warehouse.id}}', "warehouse", ""),
    ("C1b fetch_bankaccounts", "bankaccounts_get", '{"id": {bankaccount.id}}', "bankaccount", ""),
    ("C1b fetch_stockmovements", "stockmovements_get", '{"id": {stockmovement.id}}', "stockmovement", ""),
    ("C1b fetch_productlots", "productlots_get", '{"id": {productlot.id}}', "productlot", ""),
    ("C1b fetch_proposals", "proposals_get", '{"id": {proposal.id}}', "proposal", ""),
    ("C1b fetch_orders", "orders_get", '{"id": {order.id}}', "order", ""),
    ("C1b fetch_invoices", "invoices_get", '{"id": {invoice.id}}', "invoice", ""),
    ("C1b fetch_payments", "payments_get", '{"id": {payment.id}}', "payment", ""),
    ("C1b fetch_supplier_orders", "supplier_orders_get", '{"id": {supplier_order.id}}', "supplier_order", ""),
    ("C1b fetch_supplier_invoices", "supplier_invoices_get", '{"id": {supplier_invoice.id}}', "supplier_invoice", ""),
    ("C1b fetch_supplier_proposals", "supplier_proposals_get", '{"id": {supplier_proposal.id}}', "supplier_proposal", ""),
    ("C1b fetch_contracts", "contracts_get", '{"id": {contract.id}}', "contract", ""),
    ("C1b fetch_boms", "boms_get", '{"id": {bom.id}}', "bom", ""),
    ("C1b fetch_mos", "mos_get", '{"id": {mo.id}}', "mo", ""),
    ("C1b fetch_projects", "projects_get", '{"id": {project.id}}', "project", ""),
    ("C1b fetch_tasks", "tasks_get", '{"id": {task.id}}', "task", ""),
    ("C1b fetch_shipments", "shipments_get", '{"id": {shipment.id}}', "shipment", ""),
    ("C1b fetch_receptions", "receptions_get", '{"id": {reception.id}}', "reception", ""),
    ("C1b fetch_interventions", "interventions_get", '{"id": {intervention.id}}', "intervention", ""),
    ("C1b fetch_users", "users_get", '{"id": {user.id}}', "user", ""),
    ("C1b fetch_expense_reports", "expense_reports_get", '{"id": {expense_report.id}}', "expense_report", ""),
    ("C1b fetch_holidays", "holidays_get", '{"id": {holiday.id}}', "holiday", ""),
    ("C1b fetch_agenda_events", "agenda_events_get", '{"id": {agenda_event.id}}', "agenda_event", ""),
    ("C1b fetch_categories", "categories_get", '{"id": {category.id}}', "category", ""),
    ("C1b fetch_mailings", "mailings_get", '{"id": {mailing.id}}', "mailing", ""),
    ("C1b fetch_multi_currencies", "multi_currencies_get", '{"id": {multi_currency.id}}', "multi_currency", ""),
    ("C1b fetch_tickets", "tickets_get", '{"id": {ticket.id}}', "ticket", ""),
    ("C1b fetch_groups", "users_get_group", '{"id": {group.id}}', "group", ""),
    ("C1b fetch_workstations", "workstations_get", '{"id": {workstation.id}}', "workstation", ""),
    ("C1b fetch_objectlinks", "object_links_get_by_values", '{"fk_source": {proposal.id}, "sourcetype": "propal", "fk_target": {order.id}, "targettype": "commande"}', "object_link", ""),

    # ===== Phase 3B.0: Assign representatives to thirdparty =====
    ("C1c thirdparty_add_rep", "thirdparties_add_representative", '{"id": {thirdparty.id}, "fk_user": {user.id}}', "last", ""),

    # ===== Phase 3B.1: Gets (reversed), Updates (reversed), Sub-tests (reversed) =====
    # ObjectLinks
    ("C2 get_objectlinks_by_id", "object_links_get", '{"id": {object_link.id}}', "object_link", ""),
    ("C3s objectlinks_object_links_get_by_values", "object_links_get_by_values", '{"fk_source": {proposal.id}, "sourcetype": "propal", "fk_target": {order.id}, "targettype": "commande"}', "last", ""),
    # Workstations
    ("C2 get_workstations_by_id", "workstations_get", '{"id": {workstation.id}}', "workstation", ""),
    ("C3 update_workstations", "workstations_update", '{"id": {workstation.id}, "label": "Updated WS"}', "last", ""),
    # Groups (no update)
    ("C2 get_groups_by_id", "users_get_group", '{"id": {group.id}}', "group", ""),
    # Tickets
    ("C2 get_tickets_by_id", "tickets_get", '{"id": {ticket.id}}', "ticket", ""),
    ("C3 update_tickets", "tickets_update", '{"id": {ticket.id}, "subject": "Updated Ticket"}', "last", ""),
    # MultiCurrencies
    ("C2 get_multi_currencies_by_id", "multi_currencies_get", '{"id": {multi_currency.id}}', "multi_currency", ""),
    ("C3 update_multi_currencies", "multi_currencies_update", '{"id": {multi_currency.id}, "rate": 1.5}', "last", ""),
    ("C3s multi_currencies_multi_currencies_get_rates", "multi_currencies_get_rates", '{"id": {multi_currency.id}}', "last", ""),
    # Mailings
    ("C2 get_mailings_by_id", "mailings_get", '{"id": {mailing.id}}', "mailing", ""),
    ("C3 update_mailings", "mailings_update", '{"id": {mailing.id}, "title": "t{rid}-UpdatedMail"}', "last", ""),
    # Categories
    ("C2 get_categories_by_id", "categories_get", '{"id": {category.id}}', "category", ""),
    ("C3 update_categories", "categories_update", '{"id": {category.id}, "label": "t{rid}-UpdatedCat"}', "last", ""),
    ("C3s categories_categories_get_for_object", "categories_get_for_object", '{"type": "product", "id": {product.id}}', "last", ""),
    # AgendaEvents
    ("C2 get_agenda_events_by_id", "agenda_events_get", '{"id": {agenda_event.id}}', "agenda_event", ""),
    ("C3 update_agenda_events", "agenda_events_update", '{"id": {agenda_event.id}, "label": "Updated Event"}', "last", ""),
    # Holidays
    ("C2 get_holidays_by_id", "holidays_get", '{"id": {holiday.id}}', "holiday", ""),
    ("C3 update_holidays", "holidays_update", '{"id": {holiday.id}, "note": "Updated holiday"}', "last", ""),
    # ExpenseReports
    ("C2 get_expense_reports_by_id", "expense_reports_get", '{"id": {expense_report.id}}', "expense_report", ""),
    ("C3 update_expense_reports", "expense_reports_update", '{"id": {expense_report.id}, "note_public": "Updated"}', "last", ""),
    ("C3s expense_reports_expense_reports_get_lines", "expense_reports_get_lines", '{"id": {expense_report.id}}', "last", ""),
    # Users
    ("C2 get_users_by_id", "users_get", '{"id": {user.id}}', "user", ""),
    ("C3 update_users", "users_update", '{"id": {user.id}, "email": "updated@test.com"}', "last", ""),
    # Interventions
    ("C2 get_interventions_by_id", "interventions_get", '{"id": {intervention.id}}', "intervention", ""),
    ("C3 update_interventions", "interventions_update", '{"id": {intervention.id}, "note_public": "Updated"}', "last", ""),
    ("C3s interventions_interventions_get_contacts", "interventions_get_contacts", '{"id": {intervention.id}}', "last", ""),
    # Receptions
    ("C2 get_receptions_by_id", "receptions_get", '{"id": {reception.id}}', "reception", ""),
    ("C3 update_receptions", "receptions_update", '{"id": {reception.id}, "note_public": "Updated"}', "last", ""),
    # Shipments
    ("C2 get_shipments_by_id", "shipments_get", '{"id": {shipment.id}}', "shipment", ""),
    ("C3 update_shipments", "shipments_update", '{"id": {shipment.id}, "note_public": "Updated"}', "last", ""),
    # Tasks
    ("C2 get_tasks_by_id", "tasks_get", '{"id": {task.id}}', "task", ""),
    ("C3 update_tasks", "tasks_update", '{"id": {task.id}, "label": "Updated Task"}', "last", ""),
    ("C3s tasks_tasks_get_timespent", "tasks_get_timespent", '{"id": {task.id}}', "last", ""),
    ("C3s tasks_tasks_get_contacts", "tasks_get_contacts", '{"id": {task.id}}', "last", ""),
    # Projects
    ("C2 get_projects_by_id", "projects_get", '{"id": {project.id}}', "project", ""),
    ("C3 update_projects", "projects_update", '{"id": {project.id}, "title": "Updated Project"}', "last", ""),
    ("C3s projects_projects_get_tasks", "projects_get_tasks", '{"id": {project.id}}', "last", ""),
    ("C3s projects_projects_get_timespent", "projects_get_timespent", '{"id": {project.id}}', "last", ""),
    ("C3s projects_projects_get_contacts", "projects_get_contacts", '{"id": {project.id}}', "last", ""),
    # MOs
    ("C2 get_mos_by_id", "mos_get", '{"id": {mo.id}}', "mo", ""),
    ("C3 update_mos", "mos_update", '{"id": {mo.id}, "qty": 10.0}', "last", ""),
    # BOMs
    ("C2 get_boms_by_id", "boms_get", '{"id": {bom.id}}', "bom", ""),
    ("C3 update_boms", "boms_update", '{"id": {bom.id}, "qty": 2.0}', "last", ""),
    ("C3s boms_boms_get_lines", "boms_get_lines", '{"id": {bom.id}}', "last", ""),
    # Contracts
    ("C2 get_contracts_by_id", "contracts_get", '{"id": {contract.id}}', "contract", ""),
    ("C3 update_contracts", "contracts_update", '{"id": {contract.id}, "note_public": "Updated"}', "last", ""),
    ("C3s contracts_contracts_get_lines", "contracts_get_lines", '{"id": {contract.id}}', "last", ""),
    # SupplierProposals
    ("C2 get_supplier_proposals_by_id", "supplier_proposals_get", '{"id": {supplier_proposal.id}}', "supplier_proposal", ""),
    ("C3 update_supplier_proposals", "supplier_proposals_update", '{"id": {supplier_proposal.id}, "note_public": "Updated", "note_private": "Private note"}', "last", ""),
    # SupplierInvoices
    ("C2 get_supplier_invoices_by_id", "supplier_invoices_get", '{"id": {supplier_invoice.id}}', "supplier_invoice", ""),
    ("C3 update_supplier_invoices", "supplier_invoices_update", '{"id": {supplier_invoice.id}, "note_public": "Updated"}', "last", ""),
    ("C3s supplier_invoices_supplier_invoices_get_lines", "supplier_invoices_get_lines", '{"id": {supplier_invoice.id}}', "last", ""),
    ("C3s supplier_invoices_supplier_invoices_get_payments", "supplier_invoices_get_payments", '{"id": {supplier_invoice.id}}', "last", ""),
    # SupplierOrders
    ("C2 get_supplier_orders_by_id", "supplier_orders_get", '{"id": {supplier_order.id}}', "supplier_order", ""),
    ("C3 update_supplier_orders", "supplier_orders_update", '{"id": {supplier_order.id}, "note_public": "Updated"}', "last", ""),
    # Payments (no update, no sub-tests in entity def)
    ("C2 get_payments_by_id", "payments_get", '{"id": {payment.id}}', "payment", ""),
    # Invoices
    ("C2 get_invoices_by_id", "invoices_get", '{"id": {invoice.id}}', "invoice", ""),
    ("C3 update_invoices", "invoices_update", '{"id": {invoice.id}, "note_public": "Updated"}', "last", ""),
    ("C3s invoices_invoices_get_lines", "invoices_get_lines", '{"id": {invoice.id}}', "last", ""),
    ("C3s invoices_invoices_get_contacts", "invoices_get_contacts", '{"id": {invoice.id}}', "last", ""),
    ("C3s invoices_invoices_get_payments", "invoices_get_payments", '{"id": {invoice.id}}', "last", ""),
    # Orders
    ("C2 get_orders_by_id", "orders_get", '{"id": {order.id}}', "order", ""),
    ("C3 update_orders", "orders_update", '{"id": {order.id}, "note_public": "Updated"}', "last", ""),
    ("C3s orders_orders_get_lines", "orders_get_lines", '{"id": {order.id}}', "last", ""),
    ("C3s orders_orders_get_contacts", "orders_get_contacts", '{"id": {order.id}}', "last", ""),
    # Proposals
    ("C2 get_proposals_by_id", "proposals_get", '{"id": {proposal.id}}', "proposal", ""),
    ("C3 update_proposals", "proposals_update", '{"id": {proposal.id}, "note_public": "Updated"}', "last", ""),
    ("C3s proposals_proposals_get_lines", "proposals_get_lines", '{"id": {proposal.id}}', "last", ""),
    ("C3s proposals_proposals_get_contacts", "proposals_get_contacts", '{"id": {proposal.id}}', "last", ""),
    # ProductLots
    ("C2 get_productlots_by_id", "productlots_get", '{"id": {productlot.id}}', "productlot", ""),
    ("C3 update_productlots", "productlots_update", '{"id": {productlot.id}, "qty": 5.0}', "last", ""),
    # StockMovements
    ("C2 get_stockmovements_by_id", "stockmovements_get", '{"id": {stockmovement.id}}', "stockmovement", ""),
    # BankAccount
    ("C2 get_bankaccounts_by_id", "bankaccounts_get", '{"id": {bankaccount.id}}', "bankaccount", ""),
    ("C3 update_bankaccounts", "bankaccounts_update", '{"id": {bankaccount.id}, "label": "t{rid}-UpdBank"}', "last", ""),
    ("C3s bankaccounts_bankaccounts_get_lines", "bankaccounts_get_lines", '{"id": {bankaccount.id}}', "last", ""),
    ("C3s bankaccounts_bankaccounts_get_balance", "bankaccounts_get_balance", '{"id": {bankaccount.id}}', "last", ""),
    # Warehouses
    ("C2 get_warehouses_by_id", "warehouses_get", '{"id": {warehouse.id}}', "warehouse", ""),
    ("C3 update_warehouses", "warehouses_update", '{"id": {warehouse.id}, "label": "Updated Warehouse"}', "last", ""),
    ("C3s warehouses_warehouses_list_products", "warehouses_list_products", '{"id": {warehouse.id}}', "last", ""),
    # ThirdParty
    ("C2 get_thirdparty_by_id", "thirdparties_get", '{"id": {thirdparty.id}}', "thirdparty", ""),
    ("C3 update_thirdparty", "thirdparties_update", '{"id": {thirdparty.id}, "phone": "555-0000"}', "last", ""),
    ("C3s thirdparty_thirdparties_get_outstanding_proposals", "thirdparties_get_outstanding_proposals", '{"id": {thirdparty.id}}', "last", ""),
    ("C3s thirdparty_thirdparties_get_outstanding_orders", "thirdparties_get_outstanding_orders", '{"id": {thirdparty.id}}', "last", ""),
    ("C3s thirdparty_thirdparties_get_outstanding_invoices", "thirdparties_get_outstanding_invoices", '{"id": {thirdparty.id}}', "last", ""),
    ("C3s thirdparty_thirdparties_get_representatives", "thirdparties_get_representatives", '{"id": {thirdparty.id}}', "last", ""),
    ("C3s thirdparty_thirdparties_get_categories", "thirdparties_get_categories", '{"id": {thirdparty.id}}', "last", ""),
    # Contacts
    ("C2 get_contacts_by_id", "contacts_get", '{"id": {contact.id}}', "contact", ""),
    ("C3 update_contacts", "contacts_update", '{"id": {contact.id}, "firstname": "Updated"}', "last", ""),
    ("C3s contacts_contacts_get_categories", "contacts_get_categories", '{"id": {contact.id}}', "last", ""),
    # Products
    ("C2 get_products_by_id", "products_get", '{"id": {product.id}}', "product", ""),
    ("C3 update_products", "products_update", '{"id": {product.id}, "description": "Updated via test"}', "last", ""),
    ("C3s products_products_get_subproducts", "products_get_subproducts", '{"id": {product.id}}', "last", ""),
    ("C3s products_products_get_categories", "products_get_categories", '{"id": {product.id}}', "last", ""),
    ("C3s products_products_get_stock", "products_get_stock", '{"id": {product.id}}', "last", ""),
    ("C3s products_products_get_contacts", "products_get_contacts", '{"id": {product.id}}', "last", ""),

    # ===== Phase 2: Lists (data exists now, after creates/fetches) =====
    ("B2 list_products", "products_list", '{}', "last", ""),
    ("B2 list_thirdparty", "thirdparties_list", '{}', "last", ""),
    ("B2 list_contacts", "contacts_list", '{}', "last", ""),
    ("B2 list_warehouses", "warehouses_list", '{}', "last", ""),
    ("B2 list_bankaccounts", "bankaccounts_list", '{}', "last", ""),
    ("B2 list_stockmovements", "stockmovements_list", '{}', "last", ""),
    ("B2 list_productlots", "productlots_list", '{}', "last", ""),
    ("B2 list_proposals", "proposals_list", '{}', "last", ""),
    ("B2 list_orders", "orders_list", '{}', "last", ""),
    ("B2 list_invoices", "invoices_list", '{}', "last", ""),
    ("B2 list_payments", "payments_list", '{}', "last", ""),
    ("B2 list_supplier_orders", "supplier_orders_list", '{}', "last", ""),
    ("B2 list_supplier_invoices", "supplier_invoices_list", '{}', "last", ""),
    ("B2 list_supplier_proposals", "supplier_proposals_list", '{}', "last", ""),
    ("B2 list_contracts", "contracts_list", '{}', "last", ""),
    ("B2 list_boms", "boms_list", '{}', "last", ""),
    ("B2 list_mos", "mos_list", '{}', "last", ""),
    ("B2 list_projects", "projects_list", '{}', "last", ""),
    ("B2 list_tasks", "tasks_list", '{}', "last", ""),
    ("B2 list_shipments", "shipments_list", '{}', "last", ""),
    ("B2 list_receptions", "receptions_list", '{}', "last", ""),
    ("B2 list_interventions", "interventions_list", '{}', "last", ""),
    ("B2 list_expense_reports", "expense_reports_list", '{}', "last", ""),
    ("B2 list_holidays", "holidays_list", '{}', "last", ""),
    ("B2 list_agenda_events", "agenda_events_list", '{}', "last", ""),
    ("B2 list_categories", "categories_list", '{}', "last", ""),
    ("B2 list_mailings", "mailings_list", '{}', "last", ""),
    ("B2 list_multi_currencies", "multi_currencies_list", '{}', "last", ""),
    ("B2 list_tickets", "tickets_list", '{}', "last", ""),
    ("B2 list_groups", "users_list_groups", '{}', "last", ""),
    ("B2 list_workstations", "workstations_list", '{}', "last", ""),
    ("B2 list_objectlinks", "object_links_get_by_values", '{"fk_source": {proposal.id}, "sourcetype": "propal", "fk_target": {order.id}, "targettype": "commande"}', "last", ""),

    # ===== Phase 4: Domain-Specific Tools =====
    # ThirdParty
    ("P4_thirdparties_outstanding_proposals", "thirdparties_get_outstanding_proposals", '{"id": {thirdparty.id}}', "last", ""),
    ("P4_thirdparties_outstanding_orders", "thirdparties_get_outstanding_orders", '{"id": {thirdparty.id}}', "last", ""),
    ("P4_thirdparties_outstanding_invoices", "thirdparties_get_outstanding_invoices", '{"id": {thirdparty.id}}', "last", ""),
    ("P4_thirdparties_representatives", "thirdparties_get_representatives", '{"id": {thirdparty.id}}', "last", ""),
    ("P4_thirdparties_categories", "thirdparties_get_categories", '{"id": {thirdparty.id}}', "last", ""),
    # Contacts
    ("P4_contacts_categories", "contacts_get_categories", '{"id": {contact.id}}', "last", ""),
    # Products
    ("P4_products_subproducts", "products_get_subproducts", '{"id": {product.id}}', "last", ""),
    ("P4_products_categories", "products_get_categories", '{"id": {product.id}}', "last", ""),
    ("P4_products_stock", "products_get_stock", '{"id": {product.id}}', "last", ""),
    ("P4_products_contacts", "products_get_contacts", '{"id": {product.id}}', "last", ""),
    # Warehouses
    ("P4_warehouses_list_products", "warehouses_list_products", '{"id": {warehouse.id}}', "last", ""),
    # Proposals
    ("P4_proposals_get_lines", "proposals_get_lines", '{"id": {proposal.id}}', "last", ""),
    ("P4_proposals_create_line", "proposals_create_line", '{"id": {proposal.id}, "desc": "Test line", "qty": 1, "subprice": 10.0, "product_id": {product.id}}', "proposal_line", ""),
    ("P4_proposals_create_line_f3", "proposals_create_line", '{"id": {proposal.id}, "desc": "F3 test line", "qty": 1, "subprice": 10.0, "product_id": {product.id}}', "proposal_line_f3", ""),
    ("P4_proposals_get_contacts", "proposals_get_contacts", '{"id": {proposal.id}}', "last", ""),
    ("P4_proposals_add_contact", "proposals_add_contact", '{"id": {proposal.id}, "contactid": {contact.id}, "type": "CUSTOMER"}', "last", ""),
    ("P4_proposals_update_line", "proposals_update_line", '{"id": {proposal.id}, "lineid": {proposal_line.id}, "desc": "Updated line"}', "last", ""),
    ("P4_proposals_delete_line", "proposals_delete_line", '{"id": {proposal.id}, "lineid": {proposal_line.id}}', "last", ""),
    ("P4_proposals_settodraft", "proposals_settodraft", '{"id": {proposal.id}}', "last", ""),
    ("P4_proposals_validate", "proposals_validate", '{"id": {proposal.id}}', "last", ""),
    ("P4_proposals_close", "proposals_close", '{"id": {proposal.id}, "status": 2}', "last", ""),
    ("P4_proposals_setinvoiced", "proposals_setinvoiced", '{"id": {proposal.id}}', "last", ""),
    # Orders
    ("P4_orders_get_lines", "orders_get_lines", '{"id": {order.id}}', "last", ""),
    ("P4_orders_create_line", "orders_create_line", '{"id": {order.id}, "desc": "Test line", "qty": 1, "subprice": 10.0}', "order_line", ""),
    ("P4_orders_get_contacts", "orders_get_contacts", '{"id": {order.id}}', "last", ""),
    ("P4_orders_update_line", "orders_update_line", '{"id": {order.id}, "lineid": {order_line.id}, "desc": "Updated line"}', "last", ""),
    ("P4_orders_create_shipment", "orders_create_shipment", '{"id": {order.id}, "warehouse_id": {warehouse.id}}', "last", ""),
    ("P4_orders_get_shipments", "orders_get_shipments", '{"id": {order.id}}', "last", ""),
    ("P4_orders_validate", "orders_validate", '{"id": {order.id}}', "last", ""),
    ("P4_orders_close", "orders_close", '{"id": {order.id}}', "last", ""),
    ("P4_orders_reopen", "orders_reopen", '{"id": {order.id}}', "last", ""),
    ("P4_orders_setinvoiced", "orders_setinvoiced", '{"id": {order.id}}', "last", ""),
    ("P4_orders_create_from_proposal", "orders_create_from_proposal", '{"proposalid": {proposal.id}}', "last", ""),
    # Invoices
    ("P4_invoices_get_lines", "invoices_get_lines", '{"id": {invoice.id}}', "last", ""),
    ("P4_invoices_create_line", "invoices_create_line", '{"id": {invoice.id}, "desc": "Test line", "qty": 1, "subprice": 10.0, "tva_tx": 20.0, "price_base_type": "HT", "product_id": {product.id}}', "invoice_line", ""),
    ("P4_invoices_get_contacts", "invoices_get_contacts", '{"id": {invoice.id}}', "last", ""),
    ("P4_invoices_get_payments", "invoices_get_payments", '{"id": {invoice.id}}', "last", ""),
    ("P4_invoices_create_from_order", "invoices_create_from_order", '{"orderid": {order.id}}', "last", ""),
    ("P4_invoices_update_line", "invoices_update_line", '{"id": {invoice.id}, "lineid": {invoice_line.id}, "desc": "Updated line"}', "last", ""),
    ("P4_invoices_set_totals", "invoices_update", '{"id": {invoice.id}, "total_ht": 10.0, "total_tva": 2.0, "total_ttc": 12.0}', "last", ""),
    ("P4_invoices_validate", "invoices_validate", '{"id": {invoice.id}}', "last", ""),
    # Credit note flow: create a credit note to generate an available discount
    ("P4_invoices_create_credit_note", "invoices_create", '{"socid": {thirdparty.id}, "date": "{now}", "type": 2}', "credit_note", ""),
    ("P4_invoices_create_credit_note_line", "invoices_create_line", '{"id": {credit_note.id}, "desc": "Credit note line", "qty": 1, "subprice": 50.0}', "credit_note_line", ""),
    ("P4_invoices_validate_credit_note", "invoices_validate", '{"id": {credit_note.id}}', "last", ""),
    ("P4_invoices_mark_credit_available", "invoices_mark_as_credit_available", '{"id": {credit_note.id}}', "last", ""),
    ("P4_invoices_get_discount", "invoices_get_discount", '{"id": {credit_note.id}}', "discount", ""),
    ("P4_invoices_use_discount", "invoices_use_discount", '{"id": {invoice.id}, "discountid": {discount.id}}', "last", ""),
    ("P4_invoices_add_payment", "invoices_add_payment", '{"id": {invoice.id}, "datepaye": "{now}", "paymentid": {payment_type_id.id}, "accountid": {bankaccount.id}, "closepaidinvoices": "yes", "amount": 12.0}', "invoice_payment", ""),
    ("P4_invoices_settopaid", "invoices_settopaid", '{"id": {invoice.id}}', "last", ""),
    ("P4_invoices_settounpaid", "invoices_settounpaid", '{"id": {invoice.id}}', "last", ""),
    ("P4_invoices_settodraft", "invoices_settodraft", '{"id": {invoice.id}}', "last", ""),
    ("P4_invoices_add_contact", "invoices_add_contact", '{"id": {invoice.id}, "fk_socpeople": {contact.id}, "type_contact": "BILLING", "source": "external"}', "last", ""),
    ("P4_orders_settodraft", "orders_settodraft", '{"id": {order.id}}', "last", ""),
    # Payments
    ("P4_payments_update", "payments_update", '{"id": {payment.id}, "num_payment": "UPDATED-001"}', "last", ""),
    # Bank Accounts
    ("P4_bankaccounts_get_lines", "bankaccounts_get_lines", '{"id": {bankaccount.id}}', "last", ""),
    ("P4_bankaccounts_get_balance", "bankaccounts_get_balance", '{"id": {bankaccount.id}}', "last", ""),
    ("P4_bankaccounts_create_line", "bankaccounts_create_line", '{"id": {bankaccount.id}, "date": "{now}", "type": "VIR", "label": "Test wire transfer", "amount": 100.0}', "bank_line", ""),
    ("P4_bankaccounts_get_line", "bankaccounts_get_line", '{"line_id": {bank_line.id}}', "last", ""),
    ("P4_bankaccounts_update_line", "bankaccounts_update_line", '{"id": {bankaccount.id}, "line_id": {bank_line.id}, "label": "Updated bank line"}', "last", ""),
    ("P4_bankaccounts_create_second", "bankaccounts_create", '{"ref": "t{rid}-B2", "label": "t{rid}-B2", "type": 0, "currency_code": "EUR", "account_number": "FR7630001007941234567890185", "country_id": 1}', "bankaccount2", ""),
    ("P4_bankaccounts_transfer", "bankaccounts_transfer", '{"bankaccount_from_id": {bankaccount.id}, "bankaccount_to_id": {bankaccount2.id}, "date": "{now}", "description": "Test transfer", "amount": 10.0}', "last", ""),
    # Supplier Orders
    ("P4_supplier_orders_get_contacts", "supplier_orders_get_contacts", '{"id": {supplier_order.id}}', "last", ""),
    ("P4_supplier_orders_create_line", "supplier_orders_create_line", '{"id": {supplier_order.id}, "desc": "Test", "qty": 1, "subprice": 10.0}', "supplier_order_line", ""),
    ("P4_supplier_orders_add_contact", "supplier_orders_add_contact", '{"id": {supplier_order.id}, "contactid": {contact.id}, "type": "external", "source": "external"}', "last", ""),
    ("P4_supplier_orders_validate", "supplier_orders_validate", '{"id": {supplier_order.id}}', "last", ""),
    ("P4_supplier_orders_approve", "supplier_orders_approve", '{"id": {supplier_order.id}}', "last", ""),
    ("P4_supplier_orders_setsent", "supplier_orders_update", '{"id": {supplier_order.id}, "status": 3}', "last", ""),
    ("P4_supplier_orders_receive", "supplier_orders_receive", '{"id": {supplier_order.id}, "lines": "[{\\"id\\": {supplier_order_line.id}, \\"qty\\": 1, \\"warehouse\\": {warehouse.id}, \\"fk_product\\": {product.id}}]"}', "last", ""),
    # Supplier Invoices
    ("P4_supplier_invoices_get_lines", "supplier_invoices_get_lines", '{"id": {supplier_invoice.id}}', "last", ""),
    ("P4_supplier_invoices_create_line", "supplier_invoices_create_line", '{"id": {supplier_invoice.id}, "desc": "Test", "qty": 1, "subprice": 10.0}', "supplier_invoice_line", ""),
    ("P4_supplier_invoices_update_line", "supplier_invoices_update_line", '{"id": {supplier_invoice.id}, "lineid": {supplier_invoice_line.id}, "desc": "Updated line"}', "last", ""),
    ("P4_supplier_invoices_validate", "supplier_invoices_validate", '{"id": {supplier_invoice.id}}', "last", ""),
    ("P4_supplier_invoices_settopaid", "supplier_invoices_settopaid", '{"id": {supplier_invoice.id}}', "last", ""),
    ("P4_supplier_invoices_get_payments", "supplier_invoices_get_payments", '{"id": {supplier_invoice.id}}', "last", ""),
    ("P4_supplier_invoices_add_payment", "supplier_invoices_add_payment", '{"id": {supplier_invoice.id}, "datepaye": "{now}", "payment_mode_id": {payment_type_id.id}, "accountid": {bankaccount.id}, "amount": 100.0}', "last", ""),
    # Contracts
    ("P4_contracts_get_lines", "contracts_get_lines", '{"id": {contract.id}}', "last", ""),
    ("P4_contracts_create_line", "contracts_create_line", '{"id": {contract.id}, "desc": "Test contract line"}', "contract_line", ""),
    ("P4_contracts_update_line", "contracts_update_line", '{"id": {contract.id}, "lineid": {contract_line.id}, "desc": "Updated line"}', "last", ""),
    ("P4_contracts_activate_line", "contracts_activate_line", '{"id": {contract.id}, "lineid": {contract_line.id}, "datestart": "{now}"}', "last", ""),
    ("P4_contracts_validate", "contracts_validate", '{"id": {contract.id}}', "last", ""),
    ("P4_contracts_close", "contracts_close", '{"id": {contract.id}}', "last", ""),
    # BOMs
    ("P4_boms_get_lines", "boms_get_lines", '{"id": {bom.id}}', "last", ""),
    ("P4_boms_create_line", "boms_create_line", '{"id": {bom.id}, "fk_product": {product.id}, "qty": 1.0}', "bom_line", ""),
    # MOs
    ("P4_mos_update", "mos_update", '{"id": {mo.id}, "status": 1}', "last", ""),
    ("P4_mos_produce_and_consume", "mos_produce_and_consume", '{"id": {mo.id}, "inventorylabel": "Test produce", "inventorycode": "PROD-001", "arraytoconsume": [], "arraytoproduce": []}', "last", ""),
    # Projects
    ("P4_projects_get_tasks", "projects_get_tasks", '{"id": {project.id}}', "last", ""),
    ("P4_projects_get_timespent", "projects_get_timespent", '{"id": {project.id}}', "last", ""),
    ("P4_projects_validate", "projects_validate", '{"id": {project.id}}', "last", ""),
    ("P4_projects_get_contacts", "projects_get_contacts", '{"id": {project.id}}', "last", ""),
    # Tasks
    ("P4_tasks_get_timespent", "tasks_get_timespent", '{"id": {task.id}}', "last", ""),
    ("P4_tasks_add_timespent", "tasks_add_timespent", '{"id": {task.id}, "date": "{dtfmt}", "duration": 3600, "note": "Test entry", "user_id": {user.id}, "billable": 1}', "timespent", ""),
    ("P4_tasks_update_timespent", "tasks_update_timespent", '{"id": {task.id}, "timespent_id": {timespent.id}, "date": "{dtfmt}", "duration": 3600, "note": "Updated timespent"}', "last", ""),
    ("P4_tasks_delete_timespent", "tasks_delete_timespent", '{"id": {task.id}, "timespent_id": {timespent.id}}', "last", ""),
    ("P4_tasks_get_contacts", "tasks_get_contacts", '{"id": {task.id}}', "last", ""),
    # Shipments
    ("P4_shipments_close", "shipments_close", '{"id": {shipment.id}}', "last", ""),
    ("P4_shipments_validate", "shipments_validate", '{"id": {shipment.id}}', "last", ""),
    # Receptions
    ("P4_receptions_close", "receptions_close", '{"id": {reception.id}}', "last", ""),
    ("P4_receptions_validate", "receptions_validate", '{"id": {reception.id}}', "last", ""),
    # Interventions
    ("P4_interventions_create_line", "interventions_create_line", '{"id": {intervention.id}, "description": "Test intervention line", "duration": 60, "date": "{now}", "product_id": {product.id}, "qty": 1}', "intervention_line", ""),
    ("P4_interventions_get_lines", "interventions_get_lines", '{"id": {intervention.id}}', "last", ""),
    ("P4_interventions_update_line", "interventions_update_line", '{"id": {intervention.id}, "lineid": {intervention_line.id}, "desc": "Updated line"}', "last", ""),
    ("P4_interventions_delete_line", "interventions_delete_line", '{"id": {intervention.id}, "lineid": {intervention_line.id}}', "last", ""),
    ("P4_interventions_settodraft", "interventions_settodraft", '{"id": {intervention.id}}', "last", ""),
    ("P4_interventions_validate", "interventions_validate", '{"id": {intervention.id}}', "last", ""),
    ("P4_interventions_close", "interventions_close", '{"id": {intervention.id}}', "last", ""),
    # Expense Reports
    ("P4_expense_reports_get_lines", "expense_reports_get_lines", '{"id": {expense_report.id}}', "last", ""),
    ("P4_expense_reports_create_line", "expense_reports_create_line", '{"id": {expense_report.id}, "date": "{now}", "fk_c_type_fees": {expense_type_id.id}, "qty": 1, "value_unit": 10.0, "comment": "Test expense line"}', "expense_report_line", ""),
    ("P4_expense_reports_update_line", "expense_reports_update_line", '{"id": {expense_report.id}, "lineid": {expense_report_line.id}, "date": "{now}", "comment": "Updated line", "fk_c_type_fees": {expense_type_id.id}}', "last", ""),
    ("P4_expense_reports_delete_line", "expense_reports_delete_line", '{"id": {expense_report.id}, "lineid": {expense_report_line.id}}', "last", ""),
    ("P4_expense_reports_settodraft", "expense_reports_settodraft", '{"id": {expense_report.id}}', "last", ""),
    ("P4_expense_reports_validate", "expense_reports_validate", '{"id": {expense_report.id}}', "last", ""),
    ("P4_expense_reports_approve", "expense_reports_approve", '{"id": {expense_report.id}}', "last", ""),
    ("P4_expense_reports_deny", "expense_reports_deny", '{"id": {expense_report.id}, "details": "Test denial"}', "last", ""),
    ("P4_expense_reports_cancel", "expense_reports_cancel", '{"id": {expense_report.id}, "detail": "Test cancellation"}', "last", ""),
    # Holidays
    ("P4_holidays_validate", "holidays_validate", '{"id": {holiday.id}}', "last", ""),
    ("P4_holidays_approve", "holidays_approve", '{"id": {holiday.id}}', "last", ""),
    ("P4_holidays_cancel", "holidays_cancel", '{"id": {holiday.id}}', "last", ""),
    ("P4_holidays_refuse", "holidays_refuse", '{"id": {holiday.id}, "detail_refuse": "Test refusal"}', "last", ""),
    # Categories
    ("P4_categories_link_thirdparty", "categories_link_object_by_id", '{"id": {category.id}, "type": "customer", "object_id": {thirdparty.id}}', "last", ""),
    ("P4_categories_link_contact", "categories_link_object_by_id", '{"id": {category.id}, "type": "contact", "object_id": {contact.id}}', "last", ""),
    ("P4_categories_get_for_object", "categories_get_for_object", '{"type": "product", "id": {product.id}}', "last", ""),
    ("P4_categories_link_object_by_id", "categories_link_object_by_id", '{"id": {category.id}, "type": "product", "object_id": {product.id}}', "last", ""),
    ("P4_categories_link_object_by_ref", "categories_link_object_by_ref", '{"id": {category.id}, "type": "product", "object_ref": "{product.ref}"}', "last", ""),
    ("P4_categories_unlink_object", "categories_unlink_object", '{"id": {category.id}, "type": "product", "object_id": {product.id}}', "last", ""),
    # Mailings
    ("P4_mailings_validate", "mailings_validate", '{"id": {mailing.id}}', "last", ""),
    # Multi Currencies
    ("P4_multi_currencies_get_rates", "multi_currencies_get_rates", '{"id": {multi_currency.id}}', "last", ""),
    # Object Links
    ("P4_object_links_get_by_values", "object_links_get_by_values", '{"fk_source": {proposal.id}, "sourcetype": "propal", "fk_target": {order.id}, "targettype": "commande"}', "last", ""),
    # Discovery
    ("P4_documents_list_types", "documents_list_types", '{}', "last", ""),
    ("P4_categories_get_types", "categories_get_types", '{}', "last", ""),
    # Tickets
    ("P4_tickets_refetch", "tickets_get", '{"id": {ticket.id}, "include_all_fields": true}', "ticket", ""),
    ("P4_tickets_create_message", "tickets_create_message", '{"track_id": "{ticket.track_id}", "message": "Test ticket message"}', "last", ""),
    # Users
    ("P4_users_get", "users_get", '{"id": {user.id}, "include_all_fields": true}', "user", ""),
    ("P4_users_get_by_login", "users_get_by_login", '{"login": "{user.login}"}', "last", ""),
    ("P4_users_get_by_email", "users_get_by_email", '{"email": "{user.email}"}', "last", ""),
    ("P4_users_get_info", "users_get_info", '{}', "last", ""),
    ("P4_users_list_groups", "users_list_groups", '{}', "last", ""),
    ("P4_users_get_group", "users_get_group", '{"id": {group.id}}', "last", ""),
    ("P4_users_get_user_groups", "users_get_user_groups", '{"id": {user.id}}', "last", ""),

    # ===== Phase 5: Field Filtering (F1, F2, F3) =====
    # F1: Single-entity GET checks
    ("F1 thirdparties_get", "thirdparties_get", '{"id": {thirdparty.id}}', "last", ""),
    ("F1 products_get", "products_get", '{"id": {product.id}}', "last", ""),
    ("F1 contacts_get", "contacts_get", '{"id": {contact.id}}', "last", ""),
    ("F1 invoices_get", "invoices_get", '{"id": {invoice.id}}', "last", ""),
    ("F1 orders_get", "orders_get", '{"id": {order.id}}', "last", ""),
    ("F1 proposals_get", "proposals_get", '{"id": {proposal.id}}', "last", ""),
    ("F1 supplier_invoices_get", "supplier_invoices_get", '{"id": {supplier_invoice.id}}', "last", ""),
    ("F1 supplier_orders_get", "supplier_orders_get", '{"id": {supplier_order.id}}', "last", ""),
    ("F1 supplier_proposals_get", "supplier_proposals_get", '{"id": {supplier_proposal.id}}', "last", ""),
    ("F1 contracts_get", "contracts_get", '{"id": {contract.id}}', "last", ""),
    ("F1 shipments_get", "shipments_get", '{"id": {shipment.id}}', "last", ""),
    ("F1 receptions_get", "receptions_get", '{"id": {reception.id}}', "last", ""),
    ("F1 interventions_get", "interventions_get", '{"id": {intervention.id}}', "last", ""),
    ("F1 expense_reports_get", "expense_reports_get", '{"id": {expense_report.id}}', "last", ""),
    ("F1 holidays_get", "holidays_get", '{"id": {holiday.id}}', "last", ""),
    ("F1 agenda_events_get", "agenda_events_get", '{"id": {agenda_event.id}}', "last", ""),
    ("F1 categories_get", "categories_get", '{"id": {category.id}}', "last", ""),
    ("F1 mailings_get", "mailings_get", '{"id": {mailing.id}}', "last", ""),
    ("F1 multi_currencies_get", "multi_currencies_get", '{"id": {multi_currency.id}}', "last", ""),
    ("F1 tickets_get", "tickets_get", '{"id": {ticket.id}}', "last", ""),
    ("F1 warehouses_get", "warehouses_get", '{"id": {warehouse.id}}', "last", ""),
    ("F1 stockmovements_get", "stockmovements_get", '{"id": {stockmovement.id}}', "last", ""),
    ("F1 productlots_get", "productlots_get", '{"id": {productlot.id}}', "last", ""),
    ("F1 boms_get", "boms_get", '{"id": {bom.id}}', "last", ""),
    ("F1 mos_get", "mos_get", '{"id": {mo.id}}', "last", ""),
    ("F1 projects_get", "projects_get", '{"id": {project.id}}', "last", ""),
    ("F1 tasks_get", "tasks_get", '{"id": {task.id}}', "last", ""),
    ("F1 users_get", "users_get", '{"id": {user.id}}', "last", ""),
    ("F1 users_get_by_login", "users_get_by_login", '{"login": "{user.login}"}', "last", ""),
    ("F1 users_get_by_email", "users_get_by_email", '{"email": "{user.email}"}', "last", ""),
    ("F1 users_get_group", "users_get_group", '{"id": {group.id}}', "last", ""),
    ("F1 workstations_get", "workstations_get", '{"id": {workstation.id}}', "last", ""),
    ("F1 payments_get", "payments_get", '{"id": {payment.id}}', "last", ""),
    ("F1 orders_get_line", "orders_get_line", '{"id": {order.id}, "lineid": {order_line.id}}', "last", ""),
    ("F1 products_get_stock", "products_get_stock", '{"id": {product.id}}', "last", ""),
    ("F1 bankaccounts_get", "bankaccounts_get", '{"id": {bankaccount.id}}', "last", ""),
    # F2: List GET checks
    ("F2 thirdparties_list", "thirdparties_list", '{}', "last", ""),
    ("F2 products_list", "products_list", '{}', "last", ""),
    ("F2 contacts_list", "contacts_list", '{}', "last", ""),
    ("F2 invoices_list", "invoices_list", '{}', "last", ""),
    ("F2 orders_list", "orders_list", '{}', "last", ""),
    ("F2 proposals_list", "proposals_list", '{}', "last", ""),
    ("F2 supplier_invoices_list", "supplier_invoices_list", '{}', "last", ""),
    ("F2 supplier_orders_list", "supplier_orders_list", '{}', "last", ""),
    ("F2 supplier_proposals_list", "supplier_proposals_list", '{}', "last", ""),
    ("F2 contracts_list", "contracts_list", '{}', "last", ""),
    ("F2 shipments_list", "shipments_list", '{}', "last", ""),
    ("F2 receptions_list", "receptions_list", '{}', "last", ""),
    ("F2 interventions_list", "interventions_list", '{}', "last", ""),
    ("F2 expense_reports_list", "expense_reports_list", '{}', "last", ""),
    ("F2 holidays_list", "holidays_list", '{}', "last", ""),
    ("F2 agenda_events_list", "agenda_events_list", '{}', "last", ""),
    ("F2 categories_list", "categories_list", '{}', "last", ""),
    ("F2 mailings_list", "mailings_list", '{}', "last", ""),
    ("F2 multi_currencies_list", "multi_currencies_list", '{}', "last", ""),
    ("F2 tickets_list", "tickets_list", '{}', "last", ""),
    ("F2 warehouses_list", "warehouses_list", '{}', "last", ""),
    ("F2 stockmovements_list", "stockmovements_list", '{}', "last", ""),
    ("F2 productlots_list", "productlots_list", '{}', "last", ""),
    ("F2 boms_list", "boms_list", '{}', "last", ""),
    ("F2 mos_list", "mos_list", '{}', "last", ""),
    ("F2 projects_list", "projects_list", '{}', "last", ""),
    ("F2 tasks_list", "tasks_list", '{}', "last", ""),
    ("F2 users_list_groups", "users_list_groups", '{}', "last", ""),
    ("F2 documents_list", "documents_list", '{"modulepart": "propal", "id": {proposal.id}}', "last", ""),
    # F3: Sub-resource GET checks
    ("F3 proposals_get_lines", "proposals_get_lines", '{"id": {proposal.id}}', "last", ""),
    ("F3 proposals_get_contacts", "proposals_get_contacts", '{"id": {proposal.id}}', "last", ""),
    ("F3 orders_get_lines", "orders_get_lines", '{"id": {order.id}}', "last", ""),
    ("F3 orders_get_contacts", "orders_get_contacts", '{"id": {order.id}}', "last", ""),
    ("F3 invoices_get_lines", "invoices_get_lines", '{"id": {invoice.id}}', "last", ""),
    ("F3 invoices_get_contacts", "invoices_get_contacts", '{"id": {invoice.id}}', "last", ""),
    ("F3 invoices_get_payments", "invoices_get_payments", '{"id": {invoice.id}}', "last", ""),
    ("F3 supplier_invoices_get_lines", "supplier_invoices_get_lines", '{"id": {supplier_invoice.id}}', "last", ""),
    ("F3 supplier_invoices_get_payments", "supplier_invoices_get_payments", '{"id": {supplier_invoice.id}}', "last", ""),
    ("F3 supplier_orders_get_contacts", "supplier_orders_get_contacts", '{"id": {supplier_order.id}}', "last", ""),
    ("F3 contracts_get_lines", "contracts_get_lines", '{"id": {contract.id}}', "last", ""),
    ("F3 boms_get_lines", "boms_get_lines", '{"id": {bom.id}}', "last", ""),
    ("F3 expense_reports_get_lines", "expense_reports_get_lines", '{"id": {expense_report.id}}', "last", ""),
    ("F3 interventions_get_contacts", "interventions_get_contacts", '{"id": {intervention.id}}', "last", ""),
    ("F3 tasks_get_contacts", "tasks_get_contacts", '{"id": {task.id}}', "last", ""),
    ("F3 projects_get_tasks", "projects_get_tasks", '{"id": {project.id}}', "last", ""),
    ("F3 projects_get_contacts", "projects_get_contacts", '{"id": {project.id}}', "last", ""),
    ("F3 thirdparties_get_outstanding_proposals", "thirdparties_get_outstanding_proposals", '{"id": {thirdparty.id}}', "last", ""),
    ("F3 thirdparties_get_outstanding_orders", "thirdparties_get_outstanding_orders", '{"id": {thirdparty.id}}', "last", ""),
    ("F3 thirdparties_get_outstanding_invoices", "thirdparties_get_outstanding_invoices", '{"id": {thirdparty.id}}', "last", ""),
    ("F3 thirdparties_get_categories", "thirdparties_get_categories", '{"id": {thirdparty.id}}', "last", ""),
    ("F3 contacts_get_categories", "contacts_get_categories", '{"id": {contact.id}}', "last", ""),
    ("F3 products_get_categories", "products_get_categories", '{"id": {product.id}}', "last", ""),
    ("F3 products_get_subproducts", "products_get_subproducts", '{"id": {product.id}}', "last", ""),
    ("F3 products_get_contacts", "products_get_contacts", '{"id": {product.id}}', "last", ""),
    ("F3 multi_currencies_get_rates", "multi_currencies_get_rates", '{"id": {multi_currency.id}}', "last", ""),
    ("F3 thirdparties_get_representatives", "thirdparties_get_representatives", '{"id": {thirdparty.id}}', "last", ""),
    ("F3 users_get_user_groups", "users_get_user_groups", '{"id": {user.id}}', "last", ""),
    ("F3 warehouses_list_products", "warehouses_list_products", '{"id": {warehouse.id}}', "last", ""),

    # ===== Phase 5.5: Line Cleanup =====
    ("P4_orders_delete_line", "orders_delete_line", '{"id": {order.id}, "lineid": {order_line.id}}', "last", ""),
    ("P4_invoices_delete_line", "invoices_delete_line", '{"id": {invoice.id}, "lineid": {invoice_line.id}}', "last", ""),
    ("P4_bankaccounts_delete_line", "bankaccounts_delete_line", '{"id": {bankaccount.id}, "line_id": {bank_line.id}}', "last", ""),
    ("P4_supplier_invoices_delete_line", "supplier_invoices_delete_line", '{"id": {supplier_invoice.id}, "lineid": {supplier_invoice_line.id}}', "last", ""),
    ("P4_contracts_delete_line", "contracts_delete_line", '{"id": {contract.id}, "lineid": {contract_line.id}}', "last", ""),
    ("P4_boms_delete_line", "boms_delete_line", '{"id": {bom.id}, "lineid": {bom_line.id}}', "last", ""),
    # Invoice financial cleanup (remove payment before invoice delete)
    ("P4_invoices_delete_payment", "payments_delete", '{"id": {invoice_payment.id}}', "last", ""),

    # ===== Phase 3B.2: Deletes + Verify Deletes (reversed order) =====
    ("C4 delete_objectlinks", "object_links_delete", '{"id": {object_link.id}}', "last", ""),
    ("C5 verify_delete_objectlinks", "object_links_get", '{"id": {object_link.id}}', "last", "error"),
    ("C4 delete_workstations", "workstations_delete", '{"id": {workstation.id}}', "last", ""),
    ("C5 verify_delete_workstations", "workstations_get", '{"id": {workstation.id}}', "last", "error"),
    ("C4 delete_groups", "groups_delete", '{"id": {group.id}}', "last", ""),
    ("C5 verify_delete_groups", "users_get_group", '{"id": {group.id}}', "last", "error"),
    ("C4 delete_tickets", "tickets_delete", '{"id": {ticket.id}}', "last", ""),
    ("C5 verify_delete_tickets", "tickets_get", '{"id": {ticket.id}}', "last", "error"),
    ("C4 delete_multi_currencies", "multi_currencies_delete", '{"id": {multi_currency.id}}', "last", ""),
    ("C5 verify_delete_multi_currencies", "multi_currencies_get", '{"id": {multi_currency.id}}', "last", "error"),
    ("C4 delete_mailings", "mailings_delete", '{"id": {mailing.id}}', "last", ""),
    ("C5 verify_delete_mailings", "mailings_get", '{"id": {mailing.id}}', "last", "error"),
    ("C4 delete_categories", "categories_delete", '{"id": {category.id}}', "last", ""),
    ("C5 verify_delete_categories", "categories_get", '{"id": {category.id}}', "last", "error"),
    ("C4 delete_agenda_events", "agenda_events_delete", '{"id": {agenda_event.id}}', "last", ""),
    ("C5 verify_delete_agenda_events", "agenda_events_get", '{"id": {agenda_event.id}}', "last", "error"),
    ("C4 delete_holidays", "holidays_delete", '{"id": {holiday.id}}', "last", ""),
    ("C5 verify_delete_holidays", "holidays_get", '{"id": {holiday.id}}', "last", "error"),
    ("C4 delete_expense_reports", "expense_reports_delete", '{"id": {expense_report.id}}', "last", ""),
    ("C5 verify_delete_expense_reports", "expense_reports_get", '{"id": {expense_report.id}}', "last", "error"),
    ("C4 delete_users", "users_delete", '{"id": {user.id}}', "last", ""),
    ("C5 verify_delete_users", "users_get", '{"id": {user.id}}', "last", "error"),
    ("C4 delete_interventions", "interventions_delete", '{"id": {intervention.id}}', "last", ""),
    ("C5 verify_delete_interventions", "interventions_get", '{"id": {intervention.id}}', "last", "error"),
    ("C4 delete_receptions", "receptions_delete", '{"id": {reception.id}}', "last", ""),
    ("C5 verify_delete_receptions", "receptions_get", '{"id": {reception.id}}', "last", "error"),
    ("C4 delete_shipments", "shipments_delete", '{"id": {shipment.id}}', "last", ""),
    ("C5 verify_delete_shipments", "shipments_get", '{"id": {shipment.id}}', "last", "error"),
    ("C4 delete_tasks", "tasks_delete", '{"id": {task.id}}', "last", ""),
    ("C5 verify_delete_tasks", "tasks_get", '{"id": {task.id}}', "last", "error"),
    ("C4 delete_projects", "projects_delete", '{"id": {project.id}}', "last", ""),
    ("C5 verify_delete_projects", "projects_get", '{"id": {project.id}}', "last", "error"),
    ("C4 delete_mos", "mos_delete", '{"id": {mo.id}}', "last", ""),
    ("C5 verify_delete_mos", "mos_get", '{"id": {mo.id}}', "last", "error"),
    ("C4 delete_boms", "boms_delete", '{"id": {bom.id}}', "last", ""),
    ("C5 verify_delete_boms", "boms_get", '{"id": {bom.id}}', "last", "error"),
    ("C4 delete_contracts", "contracts_delete", '{"id": {contract.id}}', "last", ""),
    ("C5 verify_delete_contracts", "contracts_get", '{"id": {contract.id}}', "last", "error"),
    ("C4 delete_supplier_proposals", "supplier_proposals_delete", '{"id": {supplier_proposal.id}}', "last", ""),
    ("C5 verify_delete_supplier_proposals", "supplier_proposals_get", '{"id": {supplier_proposal.id}}', "last", "error"),
    ("C4 delete_supplier_invoices", "supplier_invoices_delete", '{"id": {supplier_invoice.id}}', "last", ""),
    ("C5 verify_delete_supplier_invoices", "supplier_invoices_get", '{"id": {supplier_invoice.id}}', "last", "error"),
    ("C4 delete_supplier_orders", "supplier_orders_delete", '{"id": {supplier_order.id}}', "last", ""),
    ("C5 verify_delete_supplier_orders", "supplier_orders_get", '{"id": {supplier_order.id}}', "last", "error"),
    ("C4 delete_payments", "payments_delete", '{"id": {payment.id}}', "last", ""),
    ("C5 verify_delete_payments", "payments_get", '{"id": {payment.id}}', "last", "error"),
    ("C4 delete_invoices", "invoices_delete", '{"id": {invoice.id}}', "last", ""),
    ("C4 delete_credit_note", "invoices_delete", '{"id": {credit_note.id}}', "last", ""),
    ("C5 verify_delete_credit_note", "invoices_get", '{"id": {credit_note.id}}', "last", "error"),
    ("C5 verify_delete_invoices", "invoices_get", '{"id": {invoice.id}}', "last", "error"),
    ("C4 delete_orders", "orders_delete", '{"id": {order.id}}', "last", ""),
    ("C5 verify_delete_orders", "orders_get", '{"id": {order.id}}', "last", "error"),
    ("C4 delete_proposals", "proposals_delete", '{"id": {proposal.id}}', "last", ""),
    ("C5 verify_delete_proposals", "proposals_get", '{"id": {proposal.id}}', "last", "error"),
    ("C4 delete_productlots", "productlots_delete", '{"id": {productlot.id}}', "last", ""),
    ("C5 verify_delete_productlots", "productlots_get", '{"id": {productlot.id}}', "last", "error"),
    ("C4 delete_stockmovements", "stockmovements_delete", '{"id": {stockmovement.id}}', "last", ""),
    ("C5 verify_delete_stockmovements", "stockmovements_get", '{"id": {stockmovement.id}}', "last", "error"),
    ("C4 delete_bankaccounts", "bankaccounts_delete", '{"id": {bankaccount.id}}', "last", ""),
    ("C5 verify_delete_bankaccounts", "bankaccounts_get", '{"id": {bankaccount.id}}', "last", "error"),
    ("C4 delete_warehouses", "warehouses_delete", '{"id": {warehouse.id}}', "last", ""),
    ("C5 verify_delete_warehouses", "warehouses_get", '{"id": {warehouse.id}}', "last", "error"),
    ("C4 delete_contacts", "contacts_delete", '{"id": {contact.id}}', "last", ""),
    ("C5 verify_delete_contacts", "contacts_get", '{"id": {contact.id}}', "last", "error"),
    ("C4 delete_thirdparty", "thirdparties_delete", '{"id": {thirdparty.id}}', "last", ""),
    ("C5 verify_delete_thirdparty", "thirdparties_get", '{"id": {thirdparty.id}}', "last", "error"),
    ("C4 delete_products", "products_delete", '{"id": {product.id}}', "last", ""),
    ("C5 verify_delete_products", "products_get", '{"id": {product.id}}', "last", "error"),

    # ===== Phase 6: Negative Tests (expect_err = "error") =====
    ("C6 invalid_tool", "nonexistent_tool", '{}', "last", "error"),
    ("C6 invalid_user_id", "users_get", '{"id": 99999999}', "last", "error"),
    ("C6 invalid_thirdparty_id", "thirdparties_get", '{"id": 99999999}', "last", "error"),
    ("C6 invalid_product_id", "products_get", '{"id": 99999999}', "last", "error"),
    ("C6 invalid_invoice_id", "invoices_get", '{"id": 99999999}', "last", "error"),
    ("C6 invalid_delete", "products_delete", '{"id": 99999999}', "last", "error"),
    ("C6 delete_nonexistent_warehouse", "warehouses_delete", '{"id": 99999999}', "last", "error"),
    ("C6 missing_params_products_create", "products_create", '{}', "last", "error"),
]

async def main():
    print(f"# Test Report — Dolibarr MCP Server\n**Run ID**: {rid}\n")
    async with httpx.AsyncClient(timeout=120.0) as client:
        _init = await client.post(MCP_URL, headers=HDR, json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "dolibarr-mcp-test-runner", "version": "1.0"}}})
        _init.raise_for_status()
        _sid = _init.headers.get("mcp-session-id")
        _hdr = dict(HDR)
        _hdr["mcp-session-id"] = _sid
        await client.post(MCP_URL, headers=_hdr, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
        for label, tool, params_json, prefix, expect_err in ALL_TESTS:
            params_str = params_json
            combined = {"rid": rid, "now": now(), "dtfmt": __import__("time").strftime('%Y-%m-%d %H:%M:%S')}
            combined.update(store)
            for k, v in combined.items():
                params_str = params_str.replace("{" + k + "}", str(v))
            params_str = re.sub(r'\{[a-zA-Z_][a-zA-Z0-9_.]*\}', 'null', params_str)
            params = json.loads(params_str)
            payload = {"jsonrpc": "2.0", "id": 0, "method": "tools/call", "params": {"name": tool, "arguments": params}}
            resp = await client.post(MCP_URL, headers=_hdr, json=payload)
            resp.raise_for_status()
            data = resp.json()["result"]
            text = data["content"][0]["text"]
            is_err = bool(data.get("isError"))
            parsed = [json.loads, lambda t: {"_raw": t}][is_err](text)
            is_pass = (expect_err == "error") == is_err
            results.append({"label": label, "tool": tool, "status": ("FAILED", "PASSED")[is_pass], "text": text})
            print(f"  {('FAIL', 'PASS')[is_pass]} {label}", file=sys.stderr)
            for k, v in parsed.items():
                store[prefix + "." + k] = str(v)
        passed = sum(r["status"] == "PASSED" for r in results)
        print(f"\n**Total:** {len(results)} | **PASSED:** {passed} | **FAILED:** {len(results)-passed}")

__import__("asyncio").run(main())

