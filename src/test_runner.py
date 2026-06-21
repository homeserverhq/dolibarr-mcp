"""
End-to-end test harness for Dolibarr MCP Server.

Connects via Streamable HTTP (JSON-RPC POST), tests all tools,
and prints a Markdown report to stdout.
"""

import json
import os
import sys
import time
import uuid
from typing import Any, Optional

import httpx

MCP_SERVER_PORT = os.environ.get("MCP_SERVER_PORT", "6033")
API_KEY = os.environ.get("API_KEY", "")
MCP_URL = f"http://localhost:{MCP_SERVER_PORT}/mcp"

MCP_HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
} if API_KEY else {}

rid = uuid.uuid4().hex[:8]
NOW = time.strftime('%Y-%m-%dT12:00:00+00:00')

results: list[dict[str, Any]] = []
store: dict[str, Any] = {}
created: dict[str, str] = {}


class MCPSession:
    """MCP Streamable HTTP client using JSON-RPC over HTTP POST (session-based)."""

    def __init__(self, url: str, headers: dict[str, str]):
        self.url = url
        self.base_headers = {
            **headers,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        self.session_headers = dict(self.base_headers)
        self.client = httpx.AsyncClient(timeout=120.0)
        self._request_id = 0
        self._session_id: str | None = None

    async def __aenter__(self):
        await self._initialize()
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def _send_notification(self, method: str, params: dict | None = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method}
        if params:
            payload["params"] = params
        await self.client.post(self.url, headers=self.session_headers, json=payload)

    async def _send(self, method: str, params: dict | None = None) -> dict:
        self._request_id += 1
        payload = {"jsonrpc": "2.0", "id": self._request_id, "method": method}
        if params:
            payload["params"] = params
        response = await self.client.post(self.url, headers=self.session_headers, json=payload)
        response.raise_for_status()

        sid = response.headers.get("mcp-session-id")
        if sid:
            self._session_id = sid
            self.session_headers = {**self.base_headers, "mcp-session-id": sid}

        data = response.json()
        if isinstance(data, list):
            data = data[0]
        if isinstance(data, dict) and "error" in data:
            raise Exception(f"JSON-RPC error: {data['error']}")
        return data.get("result", {})

    async def _initialize(self) -> dict:
        result = await self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "dolibarr-mcp-test-runner",
                "version": "1.0",
            },
        })
        await self._send_notification("notifications/initialized")
        return result

    async def list_tools(self) -> list[dict]:
        result = await self._send("tools/list")
        return result.get("tools", result)

    async def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        params = {"name": name}
        if arguments:
            params["arguments"] = arguments
        return await self._send("tools/call", params)


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def is_error(result: dict[str, Any]) -> Optional[str]:
    if "error" in result:
        err = result["error"]
        return err.get("message", str(err))
    if result.get("isError"):
        content = result.get("content", [])
        for c in content:
            if c.get("type") == "text":
                txt = c["text"]
                if txt.startswith("Error calling tool"):
                    return txt.split(":", 1)[1].strip() if ":" in txt else txt
                try:
                    data = json.loads(txt)
                except json.JSONDecodeError:
                    return txt
                if isinstance(data, dict):
                    return data.get("error", txt)
    return None


def extract_content(result: dict[str, Any]) -> Any:
    if result.get("isError"):
        return {}
    content = result.get("content", [])
    for c in content:
        if c.get("type") == "text":
            try:
                return json.loads(c["text"])
            except json.JSONDecodeError:
                return c["text"]
    return result.get("_meta", {})


def resolve_value(v: Any) -> Any:
    if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
        key = v[1:-1]
        if "." in key:
            outer, inner = key.split(".", 1)
            val = store.get(outer)
            if isinstance(val, dict):
                return val.get(inner, val)
            return val
        if key in store:
            val = store[key]
            if isinstance(val, dict):
                return val.get("id", val)
            return val
    return v


def resolve_params(params: dict[str, Any] | None) -> dict[str, Any]:
    if params is None:
        return {}
    return {k: resolve_value(v) for k, v in params.items()}


async def run_test(
    session: MCPSession,
    label: str,
    tool: str,
    params: dict[str, Any] = None,
    prereq: Optional[str] = None,
) -> bool:
    if params is None:
        params = {}
    if prereq and prereq not in created:
        results.append({
            "label": label, "tool": tool, "status": "SKIPPED",
            "reason": f"Missing prerequisite: {prereq}"
        })
        log(f"  SKIP {label}: missing {prereq}")
        return False
    params = resolve_params(params)
    try:
        result = await session.call_tool(tool, params)
        err = is_error(result)
        if err:
            results.append({
                "label": label, "tool": tool, "status": "FAILED",
                "reason": err
            })
            log(f"  FAIL {label}: {err}")
            return False
        data = extract_content(result)
        results.append({
            "label": label, "tool": tool, "status": "PASSED", "data": data
        })
        log(f"  PASS {label}")
        return True
    except Exception as e:
        results.append({
            "label": label, "tool": tool, "status": "FAILED",
            "reason": str(e)
        })
        log(f"  FAIL {label}: {e}")
        return False


async def run_test_with_store(
    session: MCPSession,
    label: str,
    tool: str,
    params: dict[str, Any] = None,
    store_key: str = None,
    prereq: Optional[str] = None,
) -> bool:
    ok = await run_test(session, label, tool, params, prereq)
    if ok and store_key:
        for r in results:
            if r["label"] == label and r["status"] == "PASSED":
                store[store_key] = r.get("data")
                break
    return ok


def pick_id(key: str) -> Optional[str]:
    entry = store.get(key, {})
    if isinstance(entry, dict):
        return entry.get("id")
    return None


def make_name(base: str) -> str:
    return f"t{rid}-{base}"


async def run_verify_delete(
    session: MCPSession,
    label: str,
    get_tool: str,
    params: dict[str, Any] = None,
) -> bool:
    if params is None:
        params = {}
    params = resolve_params(params)
    try:
        result = await session.call_tool(get_tool, params)
        err = is_error(result)
        if err:
            if "not found" in err.lower():
                results.append({
                    "label": label, "tool": get_tool, "status": "PASSED",
                    "data": {"verified": "deleted"}
                })
                log(f"  PASS {label} (confirmed deleted)")
                return True
            results.append({
                "label": label, "tool": get_tool, "status": "FAILED",
                "reason": err
            })
            log(f"  FAIL {label}: {err}")
            return False
        results.append({
            "label": label, "tool": get_tool, "status": "FAILED",
            "reason": "Record still exists after delete"
        })
        log(f"  FAIL {label}: record still exists")
        return False
    except Exception as e:
        results.append({
            "label": label, "tool": get_tool, "status": "FAILED",
            "reason": str(e)
        })
        log(f"  FAIL {label}: {e}")
        return False


# =============================================================================
# Test Data Configuration
# =============================================================================

RESOURCE_TESTS = [
    {
        "label": "Products",
        "list": "products_list",
        "create": ("products_create", {"ref": make_name("PROD"), "label": make_name("Product"), "type": 0, "status": 1, "price": 10.0, "price_base_type": "HT"}),
        "get": "products_get",
        "update": ("products_update", {"description": "Updated via test"}),
        "delete": "products_delete",
        "store_key": "product",
        "sub_tests": [
            ("products_get_subproducts", {}),
            ("products_get_categories", {}),
            ("products_get_stock", {}),
            ("products_get_contacts", {}),
        ],
    },
    {
        "label": "ThirdParty",
        "list": "thirdparties_list",
        "create": ("thirdparties_create", {"name": make_name("TP"), "client": 1, "fournisseur": 1, "code_client": f"CU{time.strftime('%y%m')}-{rid[-4:]}", "code_fournisseur": f"SU{time.strftime('%y%m')}-{rid[-4:]}"}),
        "get": "thirdparties_get",
        "update": ("thirdparties_update", {"phone": "555-0000"}),
        "delete": "thirdparties_delete",
        "store_key": "thirdparty",
        "sub_tests": [
            ("thirdparties_get_outstanding_proposals", {"id": "{thirdparty}"}),
            ("thirdparties_get_outstanding_orders", {"id": "{thirdparty}"}),
            ("thirdparties_get_outstanding_invoices", {"id": "{thirdparty}"}),
            ("thirdparties_get_representatives", {"id": "{thirdparty}"}),
            ("thirdparties_get_categories", {"id": "{thirdparty}"}),
        ],
    },
    {
        "label": "Contacts",
        "list": "contacts_list",
        "create": ("contacts_create", {"lastname": make_name("L"), "socid": 1, "firstname": "Test"}),
        "get": "contacts_get",
        "update": ("contacts_update", {"firstname": "Updated"}),
        "delete": "contacts_delete",
        "store_key": "contact",
        "sub_tests": [
            ("contacts_get_categories", {}),
        ],
    },
    {
        "label": "Warehouses",
        "list": "warehouses_list",
        "create": ("warehouses_create", {"ref": make_name("WH"), "label": make_name("Warehouse"), "status": 1}),
        "get": "warehouses_get",
        "update": ("warehouses_update", {"label": "Updated Warehouse"}),
        "delete": "warehouses_delete",
        "store_key": "warehouse",
        "sub_tests": [
            ("warehouses_list_products", {}),
        ],
    },
    {
        "label": "BankAccount",
        "list": "bankaccounts_list",
        "create": ("bankaccounts_create", {"ref": make_name("BA"), "label": make_name("Bank"), "type": 0, "currency_code": "EUR", "account_number": "FR7630001007941234567890185", "country_id": 1}),
        "get": "bankaccounts_get",
        "update": ("bankaccounts_update", {"label": "Updated Bank"}),
        "delete": "bankaccounts_delete",
        "store_key": "bankaccount",
        "sub_tests": [
            ("bankaccounts_get_lines", {}),
            ("bankaccounts_get_balance", {}),
        ],
    },
    {
        "label": "StockMovements",
        "list": "stockmovements_list",
        "create": ("stockmovements_create", {"product_id": "{product}", "warehouse_id": "{warehouse}", "qty": 10.0, "type": 0, "label": make_name("Movement"), "batch": "test-batch-001"}),
        "get": "stockmovements_get",
        "update": ("stockmovements_update", {"qty": 15.0}),
        "delete": "stockmovements_delete",
        "store_key": "stockmovement",
        "sub_tests": [],
    },
    {
        "label": "ProductLots",
        "list": "productlots_list",
        "create": ("productlots_create", {"ref": make_name("LOT"), "fk_product": "{product}", "batch": "BATCH-001"}),
        "get": "productlots_get",
        "update": ("productlots_update", {"qty": 5.0}),
        "delete": "productlots_delete",
        "store_key": "productlot",
        "sub_tests": [],
    },
    {
        "label": "Proposals",
        "list": "proposals_list",
        "create": ("proposals_create", {"socid": 1, "date": NOW}),
        "get": "proposals_get",
        "update": ("proposals_update", {"note_public": "Updated"}),
        "delete": "proposals_delete",
        "store_key": "proposal",
        "sub_tests": [
            ("proposals_get_lines", {}),
            ("proposals_get_contacts", {}),
        ],
    },
    {
        "label": "Orders",
        "list": "orders_list",
        "create": ("orders_create", {"socid": 1, "date": NOW}),
        "get": "orders_get",
        "update": ("orders_update", {"note_public": "Updated"}),
        "delete": "orders_delete",
        "store_key": "order",
        "sub_tests": [
            ("orders_get_lines", {}),
            ("orders_get_contacts", {}),
        ],
    },
    {
        "label": "Invoices",
        "list": "invoices_list",
        "create": ("invoices_create", {"socid": 1, "date": NOW, "type": 0}),
        "get": "invoices_get",
        "update": ("invoices_update", {"note_public": "Updated"}),
        "delete": "invoices_delete",
        "store_key": "invoice",
        "sub_tests": [
            ("invoices_get_lines", {}),
            ("invoices_get_contacts", {}),
            ("invoices_get_payments", {}),
        ],
    },
    {
        "label": "Payments",
        "list": "payments_list",
        "get": "payments_get",
        "update": ("payments_update", {}),
        "delete": "payments_delete",
        "store_key": "payment",
        "sub_tests": [],
    },
    {
        "label": "SupplierOrders",
        "list": "supplier_orders_list",
        "create": ("supplier_orders_create", {"socid": 1, "date": NOW}),
        "get": "supplier_orders_get",
        "update": ("supplier_orders_update", {"note_public": "Updated"}),
        "delete": "supplier_orders_delete",
        "store_key": "supplier_order",
        "sub_tests": [],
    },
    {
        "label": "SupplierInvoices",
        "list": "supplier_invoices_list",
        "create": ("supplier_invoices_create", {"socid": 1, "date": NOW}),
        "get": "supplier_invoices_get",
        "update": ("supplier_invoices_update", {"note_public": "Updated"}),
        "delete": "supplier_invoices_delete",
        "store_key": "supplier_invoice",
        "sub_tests": [
            ("supplier_invoices_get_lines", {}),
            ("supplier_invoices_get_payments", {}),
        ],
    },
    {
        "label": "SupplierProposals",
        "list": "supplier_proposals_list",
        "create": ("supplier_proposals_create", {"socid": 1, "date": NOW}),
        "get": "supplier_proposals_get",
        "update": ("supplier_proposals_update", {"note_public": "Updated"}),
        "delete": "supplier_proposals_delete",
        "store_key": "supplier_proposal",
        "sub_tests": [],
    },
    {
        "label": "Contracts",
        "list": "contracts_list",
        "create": ("contracts_create", {"socid": 1, "ref": make_name("CT"), "date_contrat": NOW, "commercial_signature_id": 1, "commercial_suivi_id": 1}),
        "get": "contracts_get",
        "update": ("contracts_update", {"note_public": "Updated"}),
        "delete": "contracts_delete",
        "store_key": "contract",
        "sub_tests": [
            ("contracts_get_lines", {}),
        ],
    },
    {
        "label": "BOMs",
        "list": "boms_list",
        "create": ("boms_create", {"ref": make_name("BOM"), "label": make_name("BillOfMaterials"), "fk_product": "{product}", "qty": 1.0, "bomtype": 0, "status": 0}),
        "get": "boms_get",
        "update": ("boms_update", {"qty": 2.0}),
        "delete": "boms_delete",
        "store_key": "bom",
        "sub_tests": [
            ("boms_get_lines", {}),
        ],
    },
    {
        "label": "MOs",
        "list": "mos_list",
        "create": ("mos_create", {"ref": make_name("MO"), "label": make_name("ManufOrder"), "fk_product": "{product}", "qty": 5.0, "fk_warehouse": "{warehouse}", "mrptype": 0, "status": 0}),
        "get": "mos_get",
        "update": ("mos_update", {"qty": 10.0}),
        "delete": "mos_delete",
        "store_key": "mo",
        "sub_tests": [],
    },
    {
        "label": "Projects",
        "list": "projects_list",
        "create": ("projects_create", {"ref": make_name("PRJ"), "title": make_name("Project")}),
        "get": "projects_get",
        "update": ("projects_update", {"title": "Updated Project"}),
        "delete": "projects_delete",
        "store_key": "project",
        "sub_tests": [
            ("projects_get_tasks", {}),
            ("projects_get_timespent", {}),
            ("projects_get_contacts", {}),
        ],
    },
    {
        "label": "Tasks",
        "list": "tasks_list",
        "create": ("tasks_create", {"ref": make_name("TSK"), "label": make_name("Task"), "fk_project": "{project}"}),
        "get": "tasks_get",
        "update": ("tasks_update", {"label": "Updated Task"}),
        "delete": "tasks_delete",
        "store_key": "task",
        "sub_tests": [
            ("tasks_get_timespent", {}),
            ("tasks_get_contacts", {}),
        ],
    },
    {
        "label": "Shipments",
        "list": "shipments_list",
        "create": ("shipments_create", {"socid": 1, "ref": make_name("SHP"), "origin_id": "{order}", "origin_type": "commande"}),
        "get": "shipments_get",
        "update": ("shipments_update", {"note_public": "Updated"}),
        "delete": "shipments_delete",
        "store_key": "shipment",
        "sub_tests": [],
    },
    {
        "label": "Receptions",
        "list": "receptions_list",
        "create": ("receptions_create", {"socid": 1, "ref": make_name("REC"), "origin_id": "{supplier_order}", "origin_type": "commande_fournisseur"}),
        "get": "receptions_get",
        "update": ("receptions_update", {"note_public": "Updated"}),
        "delete": "receptions_delete",
        "store_key": "reception",
        "sub_tests": [],
    },
    {
        "label": "Interventions",
        "list": "interventions_list",
        "create": ("interventions_create", {"socid": 1, "ref": make_name("IN")}),
        "get": "interventions_get",
        "update": ("interventions_update", {"note_public": "Updated"}),
        "delete": "interventions_delete",
        "store_key": "intervention",
        "sub_tests": [
            ("interventions_get_contacts", {}),
        ],
    },
    {
        "label": "ExpenseReports",
        "list": "expense_reports_list",
        "create": ("expense_reports_create", {"fk_user": 1, "date_debut": "2026-06-01T12:00:00+00:00", "date_fin": "2026-06-22T12:00:00+00:00", "fk_user_author": 1}),
        "get": "expense_reports_get",
        "update": ("expense_reports_update", {"note_public": "Updated"}),
        "delete": "expense_reports_delete",
        "store_key": "expense_report",
        "sub_tests": [
            ("expense_reports_get_lines", {}),
        ],
    },
    {
        "label": "Holidays",
        "list": "holidays_list",
        "create": ("holidays_create", {"fk_user": 1, "date_debut": "2026-07-01T00:00:00+00:00", "date_fin": "2026-07-05T00:00:00+00:00", "halfday": 0, "fk_type": 1, "note": make_name("Holiday"), "fk_validator": 1}),
        "get": "holidays_get",
        "update": ("holidays_update", {"note": "Updated holiday"}),
        "delete": "holidays_delete",
        "store_key": "holiday",
        "sub_tests": [],
    },
    {
        "label": "AgendaEvents",
        "list": "agenda_events_list",
        "create": ("agenda_events_create", {"type_code": "AC_OTH", "datep": NOW, "label": make_name("Event")}),
        "get": "agenda_events_get",
        "update": ("agenda_events_update", {"label": "Updated Event"}),
        "delete": "agenda_events_delete",
        "store_key": "agenda_event",
        "sub_tests": [],
    },
    {
        "label": "Categories",
        "list": "categories_list",
        "create": ("categories_create", {"ref": make_name("CAT"), "label": make_name("Category"), "type": "product"}),
        "get": "categories_get",
        "update": ("categories_update", {"label": "Updated Category"}),
        "delete": "categories_delete",
        "store_key": "category",
        "sub_tests": [
            ("categories_get_for_object", {"type": "product", "id": "{product}"}),
        ],
    },
    {
        "label": "Mailings",
        "list": "mailings_list",
        "create": ("mailings_create", {"title": make_name("Mailing"), "sujet": "Test Sujet", "body": "Test email body", "email_from": "test@example.com"}),
        "get": "mailings_get",
        "update": ("mailings_update", {"title": "Updated Mailing"}),
        "delete": "mailings_delete",
        "store_key": "mailing",
        "sub_tests": [],
    },
    {
        "label": "MultiCurrencies",
        "list": "multi_currencies_list",
        "create": ("multi_currencies_create", {"code": make_name("MC")[:3], "name": make_name("Currency"), "rate": 1.0}),
        "get": "multi_currencies_get",
        "update": ("multi_currencies_update", {"rate": 1.5}),
        "delete": "multi_currencies_delete",
        "store_key": "multi_currency",
        "sub_tests": [
            ("multi_currencies_get_rates", {}),
        ],
    },
    {
        "label": "Tickets",
        "list": "tickets_list",
        "create": ("tickets_create", {"subject": make_name("Ticket"), "type_code": "COM", "severity_code": "MINOR", "category_code": "OTH"}),
        "get": "tickets_get",
        "update": ("tickets_update", {"subject": "Updated Ticket"}),
        "delete": "tickets_delete",
        "store_key": "ticket",
        "sub_tests": [],
    },
    {
        "label": "ObjectLinks",
        "list": "object_links_get_by_values",
        "create": ("object_links_create", {"fk_source": 1, "sourcetype": "thirdparty", "fk_target": 1, "targettype": "contact", "relationtype": "link"}),
        "get": "object_links_get",
        "delete": "object_links_delete",
        "store_key": "object_link",
        "sub_tests": [
            ("object_links_get_by_values", {"fk_source": 1, "sourcetype": "thirdparty", "fk_target": 1, "targettype": "contact"}),
        ],
    },
]

LIST_ONLY_TESTS = [
    ("Documents", "documents_list", {"modulepart": "propal", "id": 1}),
    ("Users", "users_list", {}),
    ("Workstations", "workstations_list", {}),
]


PHASE4_TESTS = [
    # ===== ThirdParty =====
    ("P4_thirdparties_outstanding_proposals", "thirdparties_get_outstanding_proposals", {"id": "{thirdparty}"}),
    ("P4_thirdparties_outstanding_orders", "thirdparties_get_outstanding_orders", {"id": "{thirdparty}"}),
    ("P4_thirdparties_outstanding_invoices", "thirdparties_get_outstanding_invoices", {"id": "{thirdparty}"}),
    ("P4_thirdparties_representatives", "thirdparties_get_representatives", {"id": "{thirdparty}"}),
    ("P4_thirdparties_categories", "thirdparties_get_categories", {"id": "{thirdparty}"}),

    # ===== Contacts =====
    ("P4_contacts_categories", "contacts_get_categories", {"id": "{contact}"}),

    # ===== Products =====
    ("P4_products_subproducts", "products_get_subproducts", {"id": "{product}"}),
    ("P4_products_categories", "products_get_categories", {"id": "{product}"}),
    ("P4_products_stock", "products_get_stock", {"id": "{product}"}),
    ("P4_products_contacts", "products_get_contacts", {"id": "{product}"}),

    # ===== Warehouses =====
    ("P4_warehouses_list_products", "warehouses_list_products", {"id": "{warehouse}"}),

    # ===== Proposals (state transitions + sub-resources) =====
    ("P4_proposals_get_lines", "proposals_get_lines", {"id": "{proposal}"}),
    ("P4_proposals_create_line", "proposals_create_line", {"id": "{proposal}", "desc": "Test line", "qty": 1, "subprice": 10.0, "product_id": "{product}"}),
    ("P4_proposals_get_contacts", "proposals_get_contacts", {"id": "{proposal}"}),
    ("P4_proposals_add_contact", "proposals_add_contact", {"id": "{proposal}", "contactid": "{contact}", "type": "CUSTOMER"}),
    ("P4_proposals_validate", "proposals_validate", {"id": "{proposal}"}),
    ("P4_proposals_close", "proposals_close", {"id": "{proposal}", "status": 2}),
    ("P4_proposals_setinvoiced", "proposals_setinvoiced", {"id": "{proposal}"}),

    # ===== Orders (state transitions + sub-resources) =====
    ("P4_orders_get_lines", "orders_get_lines", {"id": "{order}"}),
    ("P4_orders_create_line", "orders_create_line", {"id": "{order}", "desc": "Test line", "qty": 1, "subprice": 10.0}),
    ("P4_orders_get_contacts", "orders_get_contacts", {"id": "{order}"}),
    ("P4_orders_validate", "orders_validate", {"id": "{order}"}),
    ("P4_orders_close", "orders_close", {"id": "{order}"}),
    ("P4_orders_reopen", "orders_reopen", {"id": "{order}"}),
    ("P4_orders_setinvoiced", "orders_setinvoiced", {"id": "{order}"}),
    ("P4_orders_create_from_proposal", "orders_create_from_proposal", {"proposalid": "{proposal}"}),

    # ===== Invoices (state transitions + sub-resources) =====
    ("P4_invoices_get_lines", "invoices_get_lines", {"id": "{invoice}"}),
    ("P4_invoices_create_line", "invoices_create_line", {"id": "{invoice}", "desc": "Test line", "qty": 1, "subprice": 10.0}),
    ("P4_invoices_get_contacts", "invoices_get_contacts", {"id": "{invoice}"}),
    ("P4_invoices_get_payments", "invoices_get_payments", {"id": "{invoice}"}),
    ("P4_invoices_create_from_order", "invoices_create_from_order", {"orderid": "{order}"}),
    ("P4_invoices_validate", "invoices_validate", {"id": "{invoice}"}),
    ("P4_invoices_settopaid", "invoices_settopaid", {"id": "{invoice}"}),
    ("P4_invoices_settounpaid", "invoices_settounpaid", {"id": "{invoice}"}),
    ("P4_invoices_add_contact", "invoices_add_contact", {"id": "{invoice}", "fk_socpeople": "{contact}", "type_contact": "external"}),
    ("P4_invoices_delete_contact", "invoices_delete_contact", {"id": "{invoice}", "contactid": "{contact}", "type": "external"}),
    ("P4_orders_settodraft", "orders_settodraft", {"id": "{order}"}),

    # ===== Bank Accounts =====
    ("P4_bankaccounts_get_lines", "bankaccounts_get_lines", {"id": "{bankaccount}"}),
    ("P4_bankaccounts_get_balance", "bankaccounts_get_balance", {"id": "{bankaccount}"}),
    ("P4_bankaccounts_create_line", "bankaccounts_create_line", {"id": "{bankaccount}", "date": NOW, "type": "VIR", "label": "Test wire transfer", "amount": 100.0}),

    # ===== Supplier Orders =====
    ("P4_supplier_orders_create_line", "supplier_orders_create_line", {"id": "{supplier_order}", "desc": "Test", "qty": 1, "subprice": 10.0}),
    ("P4_supplier_orders_validate", "supplier_orders_validate", {"id": "{supplier_order}"}),
    ("P4_supplier_orders_approve", "supplier_orders_approve", {"id": "{supplier_order}"}),

    # ===== Supplier Invoices =====
    ("P4_supplier_invoices_get_lines", "supplier_invoices_get_lines", {"id": "{supplier_invoice}"}),
    ("P4_supplier_invoices_create_line", "supplier_invoices_create_line", {"id": "{supplier_invoice}", "desc": "Test", "qty": 1, "subprice": 10.0}),
    ("P4_supplier_invoices_validate", "supplier_invoices_validate", {"id": "{supplier_invoice}"}),
    ("P4_supplier_invoices_settopaid", "supplier_invoices_settopaid", {"id": "{supplier_invoice}"}),
    ("P4_supplier_invoices_get_payments", "supplier_invoices_get_payments", {"id": "{supplier_invoice}"}),

    # ===== Contracts =====
    ("P4_contracts_get_lines", "contracts_get_lines", {"id": "{contract}"}),
    ("P4_contracts_create_line", "contracts_create_line", {"id": "{contract}", "desc": "Test contract line"}),
    ("P4_contracts_validate", "contracts_validate", {"id": "{contract}"}),
    ("P4_contracts_close", "contracts_close", {"id": "{contract}"}),

    # ===== BOMs =====
    ("P4_boms_get_lines", "boms_get_lines", {"id": "{bom}"}),
    ("P4_boms_create_line", "boms_create_line", {"id": "{bom}", "fk_product": "{product}", "qty": 1.0}),

    # ===== MOs =====
    ("P4_mos_produce_and_consume", "mos_produce_and_consume", {"id": "{mo}"}),
    # ===== Projects =====
    ("P4_projects_get_tasks", "projects_get_tasks", {"id": "{project}"}),
    ("P4_projects_get_timespent", "projects_get_timespent", {"id": "{project}"}),
    ("P4_projects_validate", "projects_validate", {"id": "{project}"}),
    ("P4_projects_get_contacts", "projects_get_contacts", {"id": "{project}"}),

    # ===== Tasks =====
    ("P4_tasks_get_timespent", "tasks_get_timespent", {"id": "{task}"}),
    ("P4_tasks_add_timespent", "tasks_add_timespent", {"id": "{task}", "date": NOW, "duration": 60}),
    ("P4_tasks_get_contacts", "tasks_get_contacts", {"id": "{task}"}),

    # ===== Shipments =====
    ("P4_shipments_validate", "shipments_validate", {"id": "{shipment}"}),
    ("P4_shipments_close", "shipments_close", {"id": "{shipment}"}),

    # ===== Receptions =====
    ("P4_receptions_validate", "receptions_validate", {"id": "{reception}"}),
    ("P4_receptions_close", "receptions_close", {"id": "{reception}"}),

    # ===== Interventions (state transitions) =====
    ("P4_interventions_create_line", "interventions_create_line", {"id": "{intervention}", "description": "Test intervention line", "duration": 60, "date": NOW, "product_id": "{product}", "qty": 1}),
    ("P4_interventions_get_contacts", "interventions_get_contacts", {"id": "{intervention}"}),
    ("P4_interventions_validate", "interventions_validate", {"id": "{intervention}"}),
    ("P4_interventions_close", "interventions_close", {"id": "{intervention}"}),

    # ===== Expense Reports (state transitions) =====
    ("P4_expense_reports_get_lines", "expense_reports_get_lines", {"id": "{expense_report}"}),
    ("P4_expense_reports_create_line", "expense_reports_create_line", {"id": "{expense_report}", "date": NOW, "fk_c_type_fees": 1, "qty": 1, "value_unit": 10.0, "comment": "Test expense line"}),
    ("P4_expense_reports_settodraft", "expense_reports_settodraft", {"id": "{expense_report}"}),
    ("P4_expense_reports_validate", "expense_reports_validate", {"id": "{expense_report}"}),
    ("P4_expense_reports_approve", "expense_reports_approve", {"id": "{expense_report}"}),
    ("P4_expense_reports_deny", "expense_reports_deny", {"id": "{expense_report}", "details": "Test denial"}),
    ("P4_expense_reports_cancel", "expense_reports_cancel", {"id": "{expense_report}", "detail": "Test cancellation"}),

    # ===== Holidays (state transitions) =====
    ("P4_holidays_validate", "holidays_validate", {"id": "{holiday}"}),
    ("P4_holidays_approve", "holidays_approve", {"id": "{holiday}"}),
    ("P4_holidays_cancel", "holidays_cancel", {"id": "{holiday}"}),
    ("P4_holidays_refuse", "holidays_refuse", {"id": "{holiday}", "detail_refuse": "Test refusal"}),

    # ===== Categories =====
    ("P4_categories_get_for_object", "categories_get_for_object", {"type": "product", "id": "{product}"}),
    ("P4_categories_link_object_by_id", "categories_link_object_by_id", {"id": "{category}", "type": "product", "object_id": "{product}"}),
    ("P4_categories_link_object_by_ref", "categories_link_object_by_ref", {"id": "{category}", "type": "product", "object_ref": "{product.ref}"}),
    ("P4_categories_unlink_object", "categories_unlink_object", {"id": "{category}", "type": "product", "object_id": "{product}"}),

    # ===== Mailings =====
    ("P4_mailings_validate", "mailings_validate", {"id": "{mailing}"}),

    # ===== Multi Currencies =====
    ("P4_multi_currencies_get_rates", "multi_currencies_get_rates", {"id": "{multi_currency}"}),

    # ===== Object Links =====
    ("P4_object_links_get_by_values", "object_links_get_by_values", {"fk_source": 1, "sourcetype": "thirdparty", "fk_target": 1, "targettype": "contact"}),

    # ===== Users =====
    ("P4_users_get", "users_get", {"id": 1}),
    ("P4_users_get_by_login", "users_get_by_login", {"login": "admin"}),
    ("P4_users_get_by_email", "users_get_by_email", {"email": "admin@example.com"}),
    ("P4_users_get_info", "users_get_info", {}),
    ("P4_users_list_groups", "users_list_groups", {}),
    ("P4_users_get_group", "users_get_group", {"group": 1}),
    ("P4_users_get_user_groups", "users_get_user_groups", {"id": 1}),
]

# =============================================================================
# Main Test Runner
# =============================================================================

async def main():
    print(f"# Test Report — Dolibarr MCP Server")
    print(f"\n**Date**: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    print(f"**Server**: {MCP_URL}")
    print(f"**Run ID**: {rid}")
    print()

    async with MCPSession(MCP_URL, MCP_HEADERS) as session:
        # ------------------------------------------------------------------
        # Phase 0: Session Init & Tool Discovery
        # ------------------------------------------------------------------
        log("\n=== Phase 0: Session Init & Tool Discovery ===")
        tools_list = await session.list_tools()
        tool_names = [t["name"] for t in tools_list]
        total_discovered = len(tool_names)
        print(f"**Discovered**: {total_discovered} tools")
        log(f"Tools: {', '.join(sorted(tool_names))}")

        # ------------------------------------------------------------------
        # Phase 1: Status / Health Checks (read-only)
        # ------------------------------------------------------------------
        log("\n=== Phase 1: Status & Health ===")
        await run_test(session, "A1 status_get", "status_get")

        # ------------------------------------------------------------------
        # Phase 2: List Tools (get_all for each resource)
        # ------------------------------------------------------------------
        log("\n=== Phase 2: List Tools ===")
        for entry in RESOURCE_TESTS:
            label = entry["label"]
            list_tool = entry["list"]
            list_params = entry.get("list_params", {})
            await run_test(session, f"B2 list_{label.lower()}", list_tool, list_params)
        for label, list_tool, list_params in LIST_ONLY_TESTS:
            await run_test(session, f"B2 list_{label.lower()}", list_tool, list_params)

        # ------------------------------------------------------------------
        # Phase 3A: Create All Resources (store IDs, no deletes)
        # ------------------------------------------------------------------
        log("\n=== Phase 3A: Create All Resources ===")
        for entry in RESOURCE_TESTS:
            label = entry["label"]
            key = label.lower()
            store_key = entry.get("store_key", key)
            create_info = entry.get("create")

            if not create_info:
                continue

            create_tool, create_params = create_info
            ok = await run_test_with_store(
                session, f"C1 create_{key}", create_tool, create_params,
                store_key=store_key
            )
            cid = pick_id(store_key) if ok else None
            if cid:
                created[f"create_{key}"] = cid

        # ------------------------------------------------------------------
        # Phase 3A.5: Fetch full records (overwrite create-only store entries)
        # ------------------------------------------------------------------
        log("\n=== Phase 3A.5: Fetch Full Records ===")
        for entry in RESOURCE_TESTS:
            label = entry["label"]
            key = label.lower()
            store_key = entry.get("store_key", key)
            get_tool = entry.get("get")
            if get_tool and store_key in store:
                stored = store[store_key]
                if isinstance(stored, dict) and len(stored) == 1 and "id" in stored:
                    cid = stored["id"]
                    await run_test_with_store(
                        session, f"C1b fetch_{key}", get_tool, {"id": cid},
                        store_key=store_key
                    )

        # ------------------------------------------------------------------
        # Phase 4: Extended Tool Tests (all domain-specific tools)
        # ------------------------------------------------------------------
        log("\n=== Phase 4: Domain-Specific Tools ===")
        for label, tool, params in PHASE4_TESTS:
            await run_test(session, label, tool, params)

        # ------------------------------------------------------------------
        # Phase 3B: Get by ID + Update + Sub-tests + Delete + Verify
        # ------------------------------------------------------------------
        log("\n=== Phase 3B: Get/Update/Delete Cycle ===")
        for entry in reversed(RESOURCE_TESTS):
            label = entry["label"]
            key = label.lower()
            store_key = entry.get("store_key", key)
            create_info = entry.get("create")
            get_tool = entry.get("get")
            update_info = entry.get("update")
            delete_tool = entry.get("delete")
            sub_tests = entry.get("sub_tests", [])

            cid = pick_id(store_key)

            if cid and get_tool:
                # -- Get by ID --
                await run_test_with_store(
                    session, f"C2 get_{key}_by_id", get_tool,
                    {"id": cid}, store_key=f"get_{key}"
                )

                # -- Update --
                if update_info:
                    update_tool, update_params = update_info
                    upd = dict(update_params)
                    upd["id"] = cid
                    await run_test(
                        session, f"C3 update_{key}", update_tool, upd
                    )

                # -- Sub-tests (run before delete) --
                for sub_tool, sub_params in sub_tests:
                    sp = dict(sub_params)
                    no_auto = sp.pop("_no_auto_id", False)
                    if "id" not in sp and not no_auto:
                        sp["id"] = cid
                    await run_test(
                        session, f"C3s {key}_{sub_tool}", sub_tool, sp
                    )

                # -- Delete --
                if delete_tool:
                    await run_test(
                        session, f"C4 delete_{key}", delete_tool,
                        {"id": cid}
                    )

                    # -- Verify Delete --
                    if get_tool:
                        await run_verify_delete(
                            session, f"C5 verify_delete_{key}", get_tool,
                            {"id": cid}
                        )
            elif entry.get("create") is None and get_tool:
                await run_test_with_store(
                    session, f"C2 get_{key}_by_id", get_tool,
                    {"id": 1}, store_key=f"get_{key}"
                )
            else:
                for phase in ("C2", "C3", "C4", "C5"):
                    ph = f"C1 create_{key}" if phase == "C2" else f"{phase}_{key}"
                    results.append({
                        "label": ph, "tool": get_tool or "",
                        "status": "SKIPPED",
                        "reason": "No ID from create — prerequisite failed"
                    })

        # ------------------------------------------------------------------
        # Report Summary
        # ------------------------------------------------------------------
        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        skipped = sum(1 for r in results if r["status"] == "SKIPPED")

        print(f"\n## Summary\n")
        print(f"| Status | Count |")
        print(f"|--------|-------|")
        print(f"| PASSED | {passed} |")
        print(f"| FAILED | {failed} |")
        print(f"| SKIPPED | {skipped} |")

        if passed:
            print(f"\n## PASSED ({passed})\n")
            for r in results:
                if r["status"] == "PASSED":
                    print(f"- `{r['tool']}` — {r['label']}")

        if failed:
            print(f"\n## FAILED ({failed})\n")
            for r in results:
                if r["status"] == "FAILED":
                    print(f"### {r['label']}")
                    print(f"- **Error**: {r['reason']}")
                    print()

        if skipped:
            print(f"\n## SKIPPED ({skipped})\n")
            for r in results:
                if r["status"] == "SKIPPED":
                    print(f"- `{r['tool']}` — {r['reason']}")

        print(f"\n## Iteration History\n")
        print(f"| Iteration | Passed | Failed | Skipped | Fixes Applied |")
        print(f"|-----------|--------|--------|---------|---------------|")
        print(f"| 1 | {passed} | {failed} | {skipped} | Initial run |")

        total = len(results)
        print(f"\n---")
        print(f"**Total tests:** {total} | **PASSED:** {passed} | "
              f"**FAILED:** {failed} | **SKIPPED:** {skipped}")

        if failed == 0 and skipped == 0:
            print(f"\n**ALL TESTS PASS**")
        else:
            print(f"\n**TESTS FAILING** — see above for details")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
