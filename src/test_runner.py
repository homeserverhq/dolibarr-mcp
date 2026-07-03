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
from toon_mcp import toon_to_json

MCP_SERVER_PORT = os.environ.get("MCP_SERVER_PORT", "6033")
API_KEY = os.environ.get("API_KEY", "")
MCP_URL = f"http://localhost:{MCP_SERVER_PORT}/mcp"

MCP_HEADERS = {"Authorization": f"Bearer {API_KEY}"}

rid = uuid.uuid4().hex[:8]

def now() -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%S+00:00')

NOW = "__NOW__"

results: list[dict[str, Any]] = []
store: dict[str, Any] = {}
created: dict[str, str] = {}

# =============================================================================
# Field Filtering Verification — expected field sets (mirrors client.py)
# =============================================================================

EXPECTED_FIELDS: dict[str, set[str]] = {
    "TP_COMMON": {"id","ref","name","client","fournisseur","code_client","code_fournisseur","address","zip","town","country_id","country_code","phone","email","status","tva_intra"},
    "PROD_COMMON": {"id","ref","label","type","status","price_ttc","stock_reel","barcode","weight"},
    "INV_COMMON": {"id","ref","socid","total_ttc","status"},
    "CONTACT_COMMON": {"id","lastname","firstname","socid","socname","email","phone_pro","phone_mobile","status"},
    "TICKET_COMMON": {"id","ref","subject","type_label","status","track_id"},
    "LINE_COMMON": {"id","product_label","qty","subprice","total_ttc","desc"},
    "BOM_LINE_COMMON": {"id","ref","fk_product","qty"},
    "EXPENSE_LINE_COMMON": {"id","type_fees_libelle","qty","total_ttc","date","projet_title"},
    "BANK_LINE_COMMON": {"id","ref","label","amount","dateo","bank_account_label"},
    "PAYMENT_LINE_COMMON": {"id","amount","date","type_label","fk_paiement"},
    "USER_COMMON": {"id","ref","login","firstname","lastname","email","status","entity"},
    "GROUP_COMMON": {"id","name","nom","entity"},
    "CATEGORY_COMMON": {"id","ref","label","type","fk_parent"},
    "WAREHOUSE_COMMON": {"id","ref","label","status","lieu"},
    "STOCK_MOVEMENT_COMMON": {"id","ref","product_id","qty","datem","label"},
    "PRODUCT_LOT_COMMON": {"id","fk_product","batch","eatby","sellby"},
    "OUTSTANDING_COMMON": {"id","ref","total_ttc","status","date"},
    "BANK_ACCOUNT_COMMON": {"id","ref","label","type","courant","currency_code","number"},
    "MULTI_CURRENCY_COMMON": {"id","code","name","rate"},
    "EXPENSE_REPORT_COMMON": {"id","ref","total_ttc","status","date_create","fk_project"},
    "HOLIDAY_COMMON": {"id","ref","fk_user","date_debut","date_fin","status"},
    "PROJECT_COMMON": {"id","ref","title","status","socid","budget_amount"},
    "TASK_COMMON": {"id","ref","label","status","progress","planned_workload"},
    "SHIPMENT_COMMON": {"id","ref","socid","status","date_delivery"},
    "RECEPTION_COMMON": {"id","ref","socid","status","date_reception"},
    "INTERVENTION_COMMON": {"id","ref","socid","status","datec"},
    "AGENDA_EVENT_COMMON": {"id","ref","label","type","datep","status"},
    "MAILING_COMMON": {"id","title","status","nbemail","date_creation"},
    "BOM_COMMON": {"id","ref","label","status","fk_product"},
    "MO_COMMON": {"id","ref","label","status","fk_product","qty"},
    "WORKSTATION_COMMON": {"id","ref","label","status","type"},
    "DOC_COMMON": {"id","ref","label","module","type","date_c"},
}

# Map every GET tool to its expected field set
TOOL_FIELD_MAP: dict[str, set[str]] = {
    # -- Single-GET (uses _filter_fields) --
    "thirdparties_get": EXPECTED_FIELDS["TP_COMMON"],
    "contacts_get": EXPECTED_FIELDS["CONTACT_COMMON"],
    "products_get": EXPECTED_FIELDS["PROD_COMMON"],
    "warehouses_get": EXPECTED_FIELDS["WAREHOUSE_COMMON"],
    "bankaccounts_get": EXPECTED_FIELDS["BANK_ACCOUNT_COMMON"],
    "stockmovements_get": EXPECTED_FIELDS["STOCK_MOVEMENT_COMMON"],
    "productlots_get": EXPECTED_FIELDS["PRODUCT_LOT_COMMON"],
    "proposals_get": EXPECTED_FIELDS["INV_COMMON"],
    "orders_get": EXPECTED_FIELDS["INV_COMMON"],
    "orders_get_line": EXPECTED_FIELDS["LINE_COMMON"],
    "invoices_get": EXPECTED_FIELDS["INV_COMMON"],
    "payments_get": EXPECTED_FIELDS["PAYMENT_LINE_COMMON"],
    "supplier_orders_get": EXPECTED_FIELDS["INV_COMMON"],
    "supplier_invoices_get": EXPECTED_FIELDS["INV_COMMON"],
    "supplier_proposals_get": EXPECTED_FIELDS["INV_COMMON"],
    "contracts_get": EXPECTED_FIELDS["INV_COMMON"],
    "boms_get": EXPECTED_FIELDS["BOM_COMMON"],
    "mos_get": EXPECTED_FIELDS["MO_COMMON"],
    "projects_get": EXPECTED_FIELDS["PROJECT_COMMON"],
    "tasks_get": EXPECTED_FIELDS["TASK_COMMON"],
    "shipments_get": EXPECTED_FIELDS["SHIPMENT_COMMON"],
    "receptions_get": EXPECTED_FIELDS["RECEPTION_COMMON"],
    "interventions_get": EXPECTED_FIELDS["INTERVENTION_COMMON"],
    "expense_reports_get": EXPECTED_FIELDS["EXPENSE_REPORT_COMMON"],
    "holidays_get": EXPECTED_FIELDS["HOLIDAY_COMMON"],
    "agenda_events_get": EXPECTED_FIELDS["AGENDA_EVENT_COMMON"],
    "categories_get": EXPECTED_FIELDS["CATEGORY_COMMON"],
    "mailings_get": EXPECTED_FIELDS["MAILING_COMMON"],
    "multi_currencies_get": EXPECTED_FIELDS["MULTI_CURRENCY_COMMON"],
    "tickets_get": EXPECTED_FIELDS["TICKET_COMMON"],
    "users_get": EXPECTED_FIELDS["USER_COMMON"],
    "users_get_by_login": EXPECTED_FIELDS["USER_COMMON"],
    "users_get_by_email": EXPECTED_FIELDS["USER_COMMON"],
    "users_get_group": EXPECTED_FIELDS["GROUP_COMMON"],
    "workstations_get": EXPECTED_FIELDS["WORKSTATION_COMMON"],
    # -- List-GET (uses properties param) --
    "thirdparties_list": EXPECTED_FIELDS["TP_COMMON"],
    "contacts_list": EXPECTED_FIELDS["CONTACT_COMMON"],
    "products_list": EXPECTED_FIELDS["PROD_COMMON"],
    "warehouses_list": EXPECTED_FIELDS["WAREHOUSE_COMMON"],
    "bankaccounts_list": EXPECTED_FIELDS["BANK_ACCOUNT_COMMON"],
    "stockmovements_list": EXPECTED_FIELDS["STOCK_MOVEMENT_COMMON"],
    "productlots_list": EXPECTED_FIELDS["PRODUCT_LOT_COMMON"],
    "proposals_list": EXPECTED_FIELDS["INV_COMMON"],
    "orders_list": EXPECTED_FIELDS["INV_COMMON"],
    "invoices_list": EXPECTED_FIELDS["INV_COMMON"],
    "payments_list": EXPECTED_FIELDS["PAYMENT_LINE_COMMON"],
    "supplier_orders_list": EXPECTED_FIELDS["INV_COMMON"],
    "supplier_invoices_list": EXPECTED_FIELDS["INV_COMMON"],
    "supplier_proposals_list": EXPECTED_FIELDS["INV_COMMON"],
    "contracts_list": EXPECTED_FIELDS["INV_COMMON"],
    "boms_list": EXPECTED_FIELDS["BOM_COMMON"],
    "mos_list": EXPECTED_FIELDS["MO_COMMON"],
    "projects_list": EXPECTED_FIELDS["PROJECT_COMMON"],
    "tasks_list": EXPECTED_FIELDS["TASK_COMMON"],
    "shipments_list": EXPECTED_FIELDS["SHIPMENT_COMMON"],
    "receptions_list": EXPECTED_FIELDS["RECEPTION_COMMON"],
    "interventions_list": EXPECTED_FIELDS["INTERVENTION_COMMON"],
    "expense_reports_list": EXPECTED_FIELDS["EXPENSE_REPORT_COMMON"],
    "holidays_list": EXPECTED_FIELDS["HOLIDAY_COMMON"],
    "agenda_events_list": EXPECTED_FIELDS["AGENDA_EVENT_COMMON"],
    "categories_list": EXPECTED_FIELDS["CATEGORY_COMMON"],
    "mailings_list": EXPECTED_FIELDS["MAILING_COMMON"],
    "multi_currencies_list": EXPECTED_FIELDS["MULTI_CURRENCY_COMMON"],
    "tickets_list": EXPECTED_FIELDS["TICKET_COMMON"],
    "documents_list": EXPECTED_FIELDS["DOC_COMMON"],
    "users_list": EXPECTED_FIELDS["USER_COMMON"],
    "users_list_groups": EXPECTED_FIELDS["GROUP_COMMON"],
    "workstations_list": EXPECTED_FIELDS["WORKSTATION_COMMON"],
    # -- Sub-resource GET (uses properties param) --
    "proposals_get_lines": EXPECTED_FIELDS["LINE_COMMON"],
    "orders_get_lines": EXPECTED_FIELDS["LINE_COMMON"],
    "invoices_get_lines": EXPECTED_FIELDS["LINE_COMMON"],
    "supplier_invoices_get_lines": EXPECTED_FIELDS["LINE_COMMON"],
    "boms_get_lines": EXPECTED_FIELDS["BOM_LINE_COMMON"],
    "expense_reports_get_lines": EXPECTED_FIELDS["EXPENSE_LINE_COMMON"],
    "bankaccounts_get_lines": EXPECTED_FIELDS["BANK_LINE_COMMON"],
    "invoices_get_payments": EXPECTED_FIELDS["PAYMENT_LINE_COMMON"],
    "supplier_invoices_get_payments": EXPECTED_FIELDS["PAYMENT_LINE_COMMON"],
    "multi_currencies_get_rates": {"id", "rate"},
    "thirdparties_get_outstanding_proposals": {"opened", "refs"},
    "thirdparties_get_outstanding_orders": {"opened", "refs"},
    "thirdparties_get_outstanding_invoices": {"opened", "refs", "refsopened"},
    "thirdparties_get_categories": EXPECTED_FIELDS["CATEGORY_COMMON"],
    "contacts_get_categories": EXPECTED_FIELDS["CATEGORY_COMMON"],
    "products_get_categories": EXPECTED_FIELDS["CATEGORY_COMMON"],
    "products_get_subproducts": EXPECTED_FIELDS["PROD_COMMON"],
    "products_get_stock": {"stock_reel", "stock_theorique", "stock_warehouses"},
    "proposals_get_contacts": {"address", "civility", "code", "country", "country_id", "email", "firstname", "fk_c_type_contact", "gender", "id", "lastname", "libelle", "login", "nom", "parentId", "photo", "rowid", "socid", "source", "status", "statuscontact", "town", "zip"},
    "orders_get_contacts": {"email", "firstname", "id", "lastname", "socid", "status"},
    "invoices_get_contacts": {"email", "firstname", "id", "lastname", "socid", "status"},
    "supplier_orders_get_contacts": {"email", "firstname", "id", "lastname", "socid", "status"},
    "interventions_get_contacts": {"email", "firstname", "id", "lastname", "socid", "status"},
    "tasks_get_contacts": {"email", "firstname", "id", "lastname", "socid", "status"},
    "projects_get_contacts": {"email", "firstname", "id", "lastname", "socid", "status"},
    "products_get_contacts": {"email", "firstname", "id", "lastname", "socid", "status"},
    "thirdparties_get_representatives": EXPECTED_FIELDS["CONTACT_COMMON"],
    "users_get_user_groups": EXPECTED_FIELDS["GROUP_COMMON"],
    "contracts_get_lines": EXPECTED_FIELDS["LINE_COMMON"],
    "warehouses_list_products": EXPECTED_FIELDS["PROD_COMMON"],
}


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
        params and payload.update({"params": params})
        await self.client.post(self.url, headers=self.session_headers, json=payload)

    async def _send(self, method: str, params: dict | None = None) -> dict:
        self._request_id += 1
        payload = {"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params or {}}
        response = await self.client.post(self.url, headers=self.session_headers, json=payload)
        response.raise_for_status()
        sid = response.headers.get("mcp-session-id")
        sid and (setattr(self, '_session_id', sid) or 1) and (setattr(self, 'session_headers', {**self.base_headers, "mcp-session-id": sid}) or 1)
        data = response.json()
        isinstance(data, list) and isinstance(data[0], dict) and data.__setitem__(0, data[0]) or None
        data = isinstance(data, list) and data[0] or data
        data = isinstance(data, dict) and "error" in data and {"error": str(data["error"])} or data
        return data.get("result", data)

    async def _initialize(self) -> dict:
        result = await self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "dolibarr-mcp-test-runner", "version": "1.0"},
        })
        await self._send_notification("notifications/initialized")
        return result

    async def list_tools(self) -> list[dict]:
        result = await self._send("tools/list")
        return result.get("tools", result)

    async def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        params = {"name": name}
        arguments and params.update({"arguments": arguments})
        return await self._send("tools/call", params)


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def is_error(result: dict[str, Any]) -> Optional[str]:
    err = result.get("error")
    txt = err and (isinstance(err, dict) and err.get("message") or str(err))
    content = result.get("content", [])
    has_error = result.get("isError") or bool(err)
    for c in content:
        is_err_text = has_error and c.get("type") == "text" and c["text"]
        txt = txt or is_err_text
    return txt or None


def extract_content(result: dict[str, Any]) -> Any:
    content = result.get("content", [])
    for c in content:
        txt = c.get("type") == "text" and c.get("text") or ""
        is_json = txt and (txt.startswith("{") or txt.startswith("[")) and json.loads(txt) or txt
        return is_json or txt
    return {}


def resolve_value(v: Any) -> Any:
    key = isinstance(v, str) and v.startswith("{") and v.endswith("}") and v[1:-1]
    key = key or ""
    outer, inner = (key.split(".", 1) + ["", ""])[:2]
    outer = outer or ""
    val = store.get(outer)
    resolved = val and isinstance(val, dict) and (inner and val.get(inner, val) or val.get("id", val)) or val
    now_val = isinstance(v, str) and v == "__NOW__" and now()
    return now_val or resolved or v


import re as _re

def _resolve_json_str(s: str) -> str:
    def _replace(m):
        key = m.group(1)
        outer, inner = (key.split(".", 1) + ["", ""])[:2]
        val = store.get(outer)
        resolved = val and isinstance(val, dict) and (inner and val.get(inner, val) or val.get("id", val)) or val
        resolved = resolved if resolved is not None else key
        return str(resolved)
    result = _re.sub(r'\{(\w+(?:\.\w+)*)\}', _replace, s)
    try:
        parsed = json.loads(result)
        result = json.dumps(parsed)
    except json.JSONDecodeError:
        pass
    return result

def resolve_params(params: dict[str, Any] | None) -> dict[str, Any]:
    resolved = {}
    for k, v in (params or {}).items():
        v = resolve_value(v)
        if isinstance(v, str) and "{" in v and v != "__NOW__":
            v = _resolve_json_str(v)
        resolved[k] = v
    return resolved


async def run_test(
    session: MCPSession,
    label: str,
    tool: str,
    params: dict[str, Any] = None,
    prereq: Optional[str] = None,
) -> bool:
    params = resolve_params(params or {})
    result = await session.call_tool(tool, params)
    err = is_error(result)
    data = extract_content(result)
    is_pass = not err and data is not None and (not isinstance(data, dict) or len(data) > 0)
    statuses = {True: "PASSED", False: "FAILED"}
    results.append({
        "label": label, "tool": tool, "status": statuses[is_pass],
        "reason": is_pass or err or "null or empty response",
        "data": is_pass and data or None
    })
    labels = {True: "PASS", False: "FAIL"}
    log(f"  {labels[is_pass]} {label}: {is_pass or err or 'null/empty'}")
    return is_pass


async def run_test_with_store(
    session: MCPSession,
    label: str,
    tool: str,
    params: dict[str, Any] = None,
    store_key: str = None,
    prereq: Optional[str] = None,
) -> bool:
    ok = await run_test(session, label, tool, params, prereq)
    for r in results:
        store_key and r["label"] == label and r["status"] == "PASSED" and store.update({store_key: r.get("data")})
    return ok


def pick_id(key: str) -> Optional[str]:
    entry = store.get(key, {})
    return isinstance(entry, dict) and entry.get("id") or entry


def make_name(base: str) -> str:
    return f"t{rid}-{base}"


async def run_verify_delete(
    session: MCPSession,
    label: str,
    get_tool: str,
    params: dict[str, Any] = None,
) -> bool:
    params = resolve_params(params or {})
    result = await session.call_tool(get_tool, params)
    err = is_error(result)
    confirmed = bool(err and "not found" in err.lower())
    statuses = {True: "PASSED", False: "FAILED"}
    reasons = {True: "confirmed deleted", False: err and str(err) or "Record still exists after delete"}
    results.append({
        "label": label, "tool": get_tool, "status": statuses[confirmed],
        "data": confirmed and {"verified": "deleted"} or None,
        "reason": reasons[confirmed]
    })
    labels = {True: "PASS", False: "FAIL"}
    log(f"  {labels[confirmed]} {label} ({reasons[confirmed]})")
    return confirmed


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
        "create": ("contacts_create", {"lastname": make_name("L"), "socid": "{thirdparty}", "firstname": "Test"}),
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
        "update": ("bankaccounts_update", {"label": make_name("UpdBank")}),
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
        "update": ("stockmovements_update", {"qty": 5.0}),
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
        "create": ("proposals_create", {"socid": "{thirdparty}", "date": NOW}),
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
        "create": ("orders_create", {"socid": "{thirdparty}", "date": NOW}),
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
        "create": ("invoices_create", {"socid": "{thirdparty}", "date": NOW, "type": 0}),
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
        "create": ("payments_create", {"datepaye": NOW, "paymentid": "{payment_type_id}", "amount": 10.0, "accountid": "{bankaccount}", "socid": "{thirdparty}"}),
        "get": "payments_get",
        "delete": "payments_delete",
        "store_key": "payment",
        "sub_tests": [],
    },
    {
        "label": "SupplierOrders",
        "list": "supplier_orders_list",
        "create": ("supplier_orders_create", {"socid": "{thirdparty}", "date": NOW}),
        "get": "supplier_orders_get",
        "update": ("supplier_orders_update", {"note_public": "Updated"}),
        "delete": "supplier_orders_delete",
        "store_key": "supplier_order",
        "sub_tests": [],
    },
    {
        "label": "SupplierInvoices",
        "list": "supplier_invoices_list",
        "create": ("supplier_invoices_create", {"socid": "{thirdparty}", "date": NOW}),
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
        "create": ("supplier_proposals_create", {"socid": "{thirdparty}", "date": NOW}),
        "get": "supplier_proposals_get",
        "update": ("supplier_proposals_update", {"note_public": "Updated", "note_private": "Private note"}),
        "delete": "supplier_proposals_delete",
        "store_key": "supplier_proposal",
        "sub_tests": [],
    },
    {
        "label": "Contracts",
        "list": "contracts_list",
        "create": ("contracts_create", {"socid": "{thirdparty}", "ref": make_name("CT"), "date_contrat": NOW, "commercial_signature_id": "{contact}", "commercial_suivi_id": "{contact}"}),
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
        "create": ("shipments_create", {"socid": "{thirdparty}", "ref": make_name("SHP"), "origin_id": "{order}", "origin_type": "commande"}),
        "get": "shipments_get",
        "update": ("shipments_update", {"note_public": "Updated"}),
        "delete": "shipments_delete",
        "store_key": "shipment",
        "sub_tests": [],
    },
    {
        "label": "Receptions",
        "list": "receptions_list",
        "create": ("receptions_create", {"socid": "{thirdparty}", "ref": make_name("REC"), "origin_id": "{supplier_order}", "origin_type": "commande_fournisseur"}),
        "get": "receptions_get",
        "update": ("receptions_update", {"note_public": "Updated"}),
        "delete": "receptions_delete",
        "store_key": "reception",
        "sub_tests": [],
    },
    {
        "label": "Interventions",
        "list": "interventions_list",
        "create": ("interventions_create", {"socid": "{thirdparty}", "ref": make_name("IN")}),
        "get": "interventions_get",
        "update": ("interventions_update", {"note_public": "Updated"}),
        "delete": "interventions_delete",
        "store_key": "intervention",
        "sub_tests": [
            ("interventions_get_contacts", {}),
        ],
    },
    {
        "label": "Users",
        "list": "users_list",
        "create": ("users_create", {"login": make_name("user"), "email": f"{make_name('u')}@test.com", "password": "test1234", "lastname": make_name("Last"), "firstname": make_name("First")}),
        "get": "users_get",
        "update": ("users_update", {"email": "updated@test.com"}),
        "delete": "users_delete",
        "store_key": "user",
        "sub_tests": [],
    },
    {
        "label": "ExpenseReports",
        "list": "expense_reports_list",
        "create": ("expense_reports_create", {"fk_user": "{user}", "date_debut": "2026-06-01T12:00:00+00:00", "date_fin": "2026-06-22T12:00:00+00:00", "fk_user_author": "{user}"}),
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
        "create": ("holidays_create", {"fk_user": "{user}", "date_debut": "2026-07-01T00:00:00+00:00", "date_fin": "2026-07-05T00:00:00+00:00", "halfday": 0, "fk_type": "{holiday_type_id}", "note": make_name("Holiday"), "fk_validator": "{user}"}),
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
        "update": ("categories_update", {"label": make_name("UpdatedCat")}),
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
        "update": ("mailings_update", {"title": make_name("UpdatedMail")}),
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
        "label": "Groups",
        "list": "users_list_groups",
        "create": ("groups_create", {"name": make_name("GRP")}),
        "get": "users_get_group",
        "delete": "groups_delete",
        "store_key": "group",
        "sub_tests": [],
    },
    {
        "label": "Workstations",
        "list": "workstations_list",
        "create": ("workstations_create", {"label": make_name("WS"), "status": 1}),
        "get": "workstations_get",
        "update": ("workstations_update", {"label": "Updated WS"}),
        "delete": "workstations_delete",
        "store_key": "workstation",
        "sub_tests": [],
    },
    {
        "label": "ObjectLinks",
        "list": ("object_links_get_by_values", {"fk_source": 1, "sourcetype": "thirdparty", "fk_target": 1, "targettype": "contact"}),
        "create": ("object_links_create", {"fk_source": "{thirdparty}", "sourcetype": "thirdparty", "fk_target": "{contact}", "targettype": "contact", "relationtype": "link"}),
        "get": "object_links_get",
        "delete": "object_links_delete",
        "store_key": "object_link",
        "sub_tests": [
            ("object_links_get_by_values", {"_auto_inject_id": True, "fk_source": "{thirdparty}", "sourcetype": "thirdparty", "fk_target": "{contact}", "targettype": "contact"}),
        ],
    },
]

LIST_ONLY_TESTS: list = []


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
    ("P4_proposals_create_line", "proposals_create_line", {"id": "{proposal}", "desc": "Test line", "qty": 1, "subprice": 10.0, "product_id": "{product}"}, "proposal_line"),
    ("P4_proposals_create_line", "proposals_create_line", {"id": "{proposal}", "desc": "F3 test line", "qty": 1, "subprice": 10.0, "product_id": "{product}"}, "proposal_line_f3"),
    ("P4_proposals_get_contacts", "proposals_get_contacts", {"id": "{proposal}"}),
    ("P4_proposals_add_contact", "proposals_add_contact", {"id": "{proposal}", "contactid": "{contact}", "type": "CUSTOMER"}),
    ("P4_proposals_update_line", "proposals_update_line", {"id": "{proposal}", "lineid": "{proposal_line.id}", "desc": "Updated line"}),
    ("P4_proposals_delete_line", "proposals_delete_line", {"id": "{proposal}", "lineid": "{proposal_line.id}"}),
    ("P4_proposals_settodraft", "proposals_settodraft", {"id": "{proposal}"}),
    ("P4_proposals_validate", "proposals_validate", {"id": "{proposal}"}),
    ("P4_proposals_close", "proposals_close", {"id": "{proposal}", "status": 2}),
    ("P4_proposals_setinvoiced", "proposals_setinvoiced", {"id": "{proposal}"}),

    # ===== Orders (state transitions + sub-resources) =====
    ("P4_orders_get_lines", "orders_get_lines", {"id": "{order}"}),
    ("P4_orders_create_line", "orders_create_line", {"id": "{order}", "desc": "Test line", "qty": 1, "subprice": 10.0}, "order_line"),
    ("P4_orders_get_contacts", "orders_get_contacts", {"id": "{order}"}),
    ("P4_orders_update_line", "orders_update_line", {"id": "{order}", "lineid": "{order_line.id}", "desc": "Updated line"}),
    ("P4_orders_create_shipment", "orders_create_shipment", {"id": "{order}", "warehouse_id": "{warehouse}"}),
    ("P4_orders_get_shipments", "orders_get_shipments", {"id": "{order}"}),
    ("P4_orders_validate", "orders_validate", {"id": "{order}"}),
    ("P4_orders_close", "orders_close", {"id": "{order}"}),
    ("P4_orders_reopen", "orders_reopen", {"id": "{order}"}),
    ("P4_orders_setinvoiced", "orders_setinvoiced", {"id": "{order}"}),
    ("P4_orders_create_from_proposal", "orders_create_from_proposal", {"proposalid": "{proposal}"}),

    # ===== Invoices (state transitions + sub-resources) =====
    ("P4_invoices_get_lines", "invoices_get_lines", {"id": "{invoice}"}),
    ("P4_invoices_create_line", "invoices_create_line", {"id": "{invoice}", "desc": "Test line", "qty": 1, "subprice": 10.0, "tva_tx": 20.0, "price_base_type": "HT", "product_id": "{product}"}, "invoice_line"),
    ("P4_invoices_get_contacts", "invoices_get_contacts", {"id": "{invoice}"}),
    ("P4_invoices_get_payments", "invoices_get_payments", {"id": "{invoice}"}),
    ("P4_invoices_create_from_order", "invoices_create_from_order", {"orderid": "{order}"}),
    ("P4_invoices_update_line", "invoices_update_line", {"id": "{invoice}", "lineid": "{invoice_line.id}", "desc": "Updated line"}),
    ("P4_invoices_get_discount", "invoices_get_discount", {"id": "{invoice}"}),
    ("P4_invoices_use_discount", "invoices_use_discount", {"id": "{invoice}", "discountid": 0}),
    ("P4_invoices_settodraft", "invoices_settodraft", {"id": "{invoice}"}),
    ("P4_invoices_validate", "invoices_validate", {"id": "{invoice}"}),
    ("P4_invoices_add_payment", "invoices_add_payment", {"id": "{invoice}", "datepaye": NOW, "paymentid": "{payment_type_id}", "accountid": "{bankaccount}", "closepaidinvoices": "yes", "amount": 100.0}, "invoice_payment"),
    ("P4_invoices_settopaid", "invoices_settopaid", {"id": "{invoice}"}),
    ("P4_invoices_settounpaid", "invoices_settounpaid", {"id": "{invoice}"}),
    ("P4_invoices_add_contact", "invoices_add_contact", {"id": "{invoice}", "fk_socpeople": "{contact}", "type_contact": "BILLING", "source": "external"}),
    ("P4_orders_settodraft", "orders_settodraft", {"id": "{order}"}),

    # ===== Payments =====
    ("P4_payments_update", "payments_update", {"id": "{payment}", "num_payment": "UPDATED-001"}),

    # ===== Bank Accounts =====
    ("P4_bankaccounts_get_lines", "bankaccounts_get_lines", {"id": "{bankaccount}"}),
    ("P4_bankaccounts_get_balance", "bankaccounts_get_balance", {"id": "{bankaccount}"}),
    ("P4_bankaccounts_create_line", "bankaccounts_create_line", {"id": "{bankaccount}", "date": NOW, "type": "VIR", "label": "Test wire transfer", "amount": 100.0}, "bank_line"),
    ("P4_bankaccounts_get_line", "bankaccounts_get_line", {"line_id": "{bank_line.id}"}),
    ("P4_bankaccounts_update_line", "bankaccounts_update_line", {"id": "{bankaccount}", "line_id": "{bank_line.id}", "label": "Updated bank line"}),
    ("P4_bankaccounts_create_second", "bankaccounts_create", {"ref": make_name("B2"), "label": make_name("B2"), "type": 0, "currency_code": "EUR", "account_number": "FR7630001007941234567890185", "country_id": 1}, "bankaccount2"),
    ("P4_bankaccounts_transfer", "bankaccounts_transfer", {"bankaccount_from_id": "{bankaccount}", "bankaccount_to_id": "{bankaccount2}", "date": NOW, "description": "Test transfer", "amount": 10.0}),

    # ===== Supplier Orders =====
    ("P4_supplier_orders_get_contacts", "supplier_orders_get_contacts", {"id": "{supplier_order}"}),
    ("P4_supplier_orders_create_line", "supplier_orders_create_line", {"id": "{supplier_order}", "desc": "Test", "qty": 1, "subprice": 10.0}, "supplier_order_line"),
    ("P4_supplier_orders_add_contact", "supplier_orders_add_contact", {"id": "{supplier_order}", "contactid": "{contact}", "type": "external", "source": "external"}),
    ("P4_supplier_orders_validate", "supplier_orders_validate", {"id": "{supplier_order}"}),
    ("P4_supplier_orders_approve", "supplier_orders_approve", {"id": "{supplier_order}"}),
    ("P4_supplier_orders_setsent", "supplier_orders_update", {"id": "{supplier_order}", "status": 3}),
    ("P4_supplier_orders_receive", "supplier_orders_receive", {"id": "{supplier_order}", "lines": '[{"id": "{supplier_order_line.id}", "qty": 1, "warehouse": "{warehouse}", "fk_product": "{product}"}]'}),

    # ===== Supplier Invoices =====
    ("P4_supplier_invoices_get_lines", "supplier_invoices_get_lines", {"id": "{supplier_invoice}"}),
    ("P4_supplier_invoices_create_line", "supplier_invoices_create_line", {"id": "{supplier_invoice}", "desc": "Test", "qty": 1, "subprice": 10.0}, "supplier_invoice_line"),
    ("P4_supplier_invoices_update_line", "supplier_invoices_update_line", {"id": "{supplier_invoice}", "lineid": "{supplier_invoice_line.id}", "desc": "Updated line"}),
    ("P4_supplier_invoices_validate", "supplier_invoices_validate", {"id": "{supplier_invoice}"}),
    ("P4_supplier_invoices_settopaid", "supplier_invoices_settopaid", {"id": "{supplier_invoice}"}),
    ("P4_supplier_invoices_get_payments", "supplier_invoices_get_payments", {"id": "{supplier_invoice}"}),
    ("P4_supplier_invoices_add_payment", "supplier_invoices_add_payment", {"id": "{supplier_invoice}", "datepaye": NOW, "payment_mode_id": "{payment_type_id}", "accountid": "{bankaccount}", "amount": 100.0}),

    # ===== Contracts =====
    ("P4_contracts_get_lines", "contracts_get_lines", {"id": "{contract}"}),
    ("P4_contracts_create_line", "contracts_create_line", {"id": "{contract}", "desc": "Test contract line"}, "contract_line"),
    ("P4_contracts_update_line", "contracts_update_line", {"id": "{contract}", "lineid": "{contract_line.id}", "desc": "Updated line"}),
    ("P4_contracts_activate_line", "contracts_activate_line", {"id": "{contract}", "lineid": "{contract_line.id}", "datestart": NOW}),
    ("P4_contracts_validate", "contracts_validate", {"id": "{contract}"}),
    ("P4_contracts_close", "contracts_close", {"id": "{contract}"}),

    # ===== BOMs =====
    ("P4_boms_get_lines", "boms_get_lines", {"id": "{bom}"}),
    ("P4_boms_create_line", "boms_create_line", {"id": "{bom}", "fk_product": "{product}", "qty": 1.0}, "bom_line"),

    # ===== MOs =====
    ("P4_mos_update", "mos_update", {"id": "{mo}", "status": 1}),
    ("P4_mos_produce_and_consume", "mos_produce_and_consume", {"id": "{mo}", "inventorylabel": "Test produce", "inventorycode": "PROD-001", "arraytoconsume": [], "arraytoproduce": []}),

    # ===== Projects =====
    ("P4_projects_get_tasks", "projects_get_tasks", {"id": "{project}"}),
    ("P4_projects_get_timespent", "projects_get_timespent", {"id": "{project}"}),
    ("P4_projects_validate", "projects_validate", {"id": "{project}"}),
    ("P4_projects_get_contacts", "projects_get_contacts", {"id": "{project}"}),

    # ===== Tasks =====
    ("P4_tasks_get_timespent", "tasks_get_timespent", {"id": "{task}"}),
    ("P4_tasks_add_timespent", "tasks_add_timespent", {"id": "{task}", "date": NOW, "duration": 3600, "note": "Test entry"}, "timespent"),
    ("P4_tasks_update_timespent", "tasks_update_timespent", {"id": "{task}", "timespent_id": "{timespent.id}", "duration": 30}),
    ("P4_tasks_delete_timespent", "tasks_delete_timespent", {"id": "{task}", "timespent_id": "{timespent.id}"}),
    ("P4_tasks_get_contacts", "tasks_get_contacts", {"id": "{task}"}),

    # ===== Shipments =====
    ("P4_shipments_close", "shipments_close", {"id": "{shipment}"}),
    ("P4_shipments_validate", "shipments_validate", {"id": "{shipment}"}),

    # ===== Receptions =====
    ("P4_receptions_close", "receptions_close", {"id": "{reception}"}),
    ("P4_receptions_validate", "receptions_validate", {"id": "{reception}"}),

    # ===== Interventions =====
    ("P4_interventions_get_lines", "interventions_get_lines", {"id": "{intervention}"}),
    ("P4_interventions_create_line", "interventions_create_line", {"id": "{intervention}", "description": "Test intervention line", "duration": 60, "date": NOW, "product_id": "{product}", "qty": 1}, "intervention_line"),
    ("P4_interventions_update_line", "interventions_update_line", {"id": "{intervention}", "lineid": "{intervention_line.id}", "desc": "Updated line"}),
    ("P4_interventions_delete_line", "interventions_delete_line", {"id": "{intervention}", "lineid": "{intervention_line.id}"}),
    ("P4_interventions_settodraft", "interventions_settodraft", {"id": "{intervention}"}),
    ("P4_interventions_validate", "interventions_validate", {"id": "{intervention}"}),
    ("P4_interventions_close", "interventions_close", {"id": "{intervention}"}),

    # ===== Expense Reports =====
    ("P4_expense_reports_get_lines", "expense_reports_get_lines", {"id": "{expense_report}"}),
    ("P4_expense_reports_create_line", "expense_reports_create_line", {"id": "{expense_report}", "date": NOW, "fk_c_type_fees": "{expense_type_id}", "qty": 1, "value_unit": 10.0, "comment": "Test expense line"}, "expense_report_line"),
    ("P4_expense_reports_update_line", "expense_reports_update_line", {"id": "{expense_report}", "lineid": "{expense_report_line.id}", "date": NOW, "comment": "Updated line", "fk_c_type_fees": "{expense_type_id}"}),
    ("P4_expense_reports_delete_line", "expense_reports_delete_line", {"id": "{expense_report}", "lineid": "{expense_report_line.id}"}),
    ("P4_expense_reports_settodraft", "expense_reports_settodraft", {"id": "{expense_report}"}),
    ("P4_expense_reports_validate", "expense_reports_validate", {"id": "{expense_report}"}),
    ("P4_expense_reports_approve", "expense_reports_approve", {"id": "{expense_report}"}),
    ("P4_expense_reports_deny", "expense_reports_deny", {"id": "{expense_report}", "details": "Test denial"}),
    ("P4_expense_reports_cancel", "expense_reports_cancel", {"id": "{expense_report}", "detail": "Test cancellation"}),

    # ===== Holidays =====
    ("P4_holidays_validate", "holidays_validate", {"id": "{holiday}"}),
    ("P4_holidays_approve", "holidays_approve", {"id": "{holiday}"}),
    ("P4_holidays_cancel", "holidays_cancel", {"id": "{holiday}"}),
    ("P4_holidays_refuse", "holidays_refuse", {"id": "{holiday}", "detail_refuse": "Test refusal"}),

    # ===== Categories =====
    ("P4_categories_link_thirdparty", "categories_link_object_by_id", {"id": "{category}", "type": "customer", "object_id": "{thirdparty}"}),
    ("P4_categories_link_contact", "categories_link_object_by_id", {"id": "{category}", "type": "contact", "object_id": "{contact}"}),
    ("P4_categories_get_for_object", "categories_get_for_object", {"type": "product", "id": "{product}"}),
    ("P4_categories_link_object_by_id", "categories_link_object_by_id", {"id": "{category}", "type": "product", "object_id": "{product}"}),
    ("P4_categories_link_object_by_ref", "categories_link_object_by_ref", {"id": "{category}", "type": "product", "object_ref": "{product.ref}"}),
    ("P4_categories_unlink_object", "categories_unlink_object", {"id": "{category}", "type": "product", "object_id": "{product}"}),

    # ===== Mailings =====
    ("P4_mailings_validate", "mailings_validate", {"id": "{mailing}"}),

    # ===== Multi Currencies =====
    ("P4_multi_currencies_get_rates", "multi_currencies_get_rates", {"id": "{multi_currency}"}),

    # ===== Object Links =====
    ("P4_object_links_get_by_values", "object_links_get_by_values", {"fk_source": "{thirdparty}", "sourcetype": "thirdparty", "fk_target": "{contact}", "targettype": "contact"}),

    # ===== Discovery =====
    ("P4_documents_list_types", "documents_list_types", {}),
    ("P4_categories_get_types", "categories_get_types", {}),

    # ===== Tickets =====
    ("P4_tickets_refetch", "tickets_get", {"id": "{ticket}", "include_all_fields": True}, "ticket"),
    ("P4_tickets_create_message", "tickets_create_message", {"track_id": "{ticket.track_id}", "message": "Test ticket message"}),

    # ===== Users =====
    ("P4_users_get", "users_get", {"id": "{user}", "include_all_fields": True}),
    ("P4_users_get_by_login", "users_get_by_login", {"login": "{user.login}"}),
    ("P4_users_get_by_email", "users_get_by_email", {"email": "{user.email}"}),
    ("P4_users_get_info", "users_get_info", {}),
    ("P4_users_list_groups", "users_list_groups", {}),
    ("P4_users_get_group", "users_get_group", {"id": "{group}"}),
    ("P4_users_get_user_groups", "users_get_user_groups", {"id": "{user}"}),
]

# =============================================================================
# Filtering Checks — verify API responses contain only expected fields
# =============================================================================

async def run_filtering_check(
    session: MCPSession,
    label: str,
    tool: str,
    params: dict[str, Any],
) -> bool:
    expected = TOOL_FIELD_MAP.get(tool) or set()
    params = resolve_params(params)
    result = await session.call_tool(tool, params)
    err = is_error(result)
    data = extract_content(result)
    raw = isinstance(data, dict) and isinstance(data.get("items"), str) and toon_to_json(data["items"]) or data
    data = isinstance(raw, dict) and "items" in raw and raw["items"] or raw
    items = isinstance(data, list) and data or isinstance(data, dict) and [data] or []
    empty_list = isinstance(items, list) and len(items) == 0
    items = empty_list and [] or (isinstance(items, list) and items or [items])
    item = isinstance(items, list) and len(items) > 0 and items[0] or {}
    extra = isinstance(item, dict) and sorted(k for k in item if k not in expected) or []
    missing = isinstance(item, dict) and sorted(k for k in expected if k not in item) or []
    problems = []
    extra and problems.append(f"unexpected: {extra}")
    missing and problems.append(f"missing: {missing}")
    has_problems = len(problems) > 0
    is_pass = not err and not empty_list and not has_problems and len(expected) > 0
    statuses = {True: "PASSED", False: "FAILED"}
    fails = []
    err and fails.append(str(err))
    empty_list and fails.append("empty list")
    has_problems and fails.append('; '.join(problems))
    results.append({
        "label": label, "tool": tool, "status": statuses[is_pass],
        "reason": is_pass or '; '.join(fails) or "unknown failure",
        "data": is_pass and {"note": f"{len(items)} items checked, all fields in allowed set ({len(expected)} fields)"} or None
    })
    labels = {True: "PASS", False: "FAIL"}
    log(f"  {labels[is_pass]} {label}: {is_pass or '; '.join(fails)}")
    return is_pass

FILTERING_CHECKS = [
    # F1: Single-entity GET checks
    ("F1 thirdparties_get", "thirdparties_get", {"id": "{thirdparty}"}),
    ("F1 products_get", "products_get", {"id": "{product}"}),
    ("F1 contacts_get", "contacts_get", {"id": "{contact}"}),
    ("F1 invoices_get", "invoices_get", {"id": "{invoice}"}),
    ("F1 orders_get", "orders_get", {"id": "{order}"}),
    ("F1 proposals_get", "proposals_get", {"id": "{proposal}"}),
    ("F1 supplier_invoices_get", "supplier_invoices_get", {"id": "{supplier_invoice}"}),
    ("F1 supplier_orders_get", "supplier_orders_get", {"id": "{supplier_order}"}),
    ("F1 supplier_proposals_get", "supplier_proposals_get", {"id": "{supplier_proposal}"}),
    ("F1 contracts_get", "contracts_get", {"id": "{contract}"}),
    ("F1 shipments_get", "shipments_get", {"id": "{shipment}"}),
    ("F1 receptions_get", "receptions_get", {"id": "{reception}"}),
    ("F1 interventions_get", "interventions_get", {"id": "{intervention}"}),
    ("F1 expense_reports_get", "expense_reports_get", {"id": "{expense_report}"}),
    ("F1 holidays_get", "holidays_get", {"id": "{holiday}"}),
    ("F1 agenda_events_get", "agenda_events_get", {"id": "{agenda_event}"}),
    ("F1 categories_get", "categories_get", {"id": "{category}"}),
    ("F1 mailings_get", "mailings_get", {"id": "{mailing}"}),
    ("F1 multi_currencies_get", "multi_currencies_get", {"id": "{multi_currency}"}),
    ("F1 tickets_get", "tickets_get", {"id": "{ticket}"}),
    ("F1 warehouses_get", "warehouses_get", {"id": "{warehouse}"}),
    ("F1 stockmovements_get", "stockmovements_get", {"id": "{stockmovement}"}),
    ("F1 productlots_get", "productlots_get", {"id": "{productlot}"}),
    ("F1 boms_get", "boms_get", {"id": "{bom}"}),
    ("F1 mos_get", "mos_get", {"id": "{mo}"}),
    ("F1 projects_get", "projects_get", {"id": "{project}"}),
    ("F1 tasks_get", "tasks_get", {"id": "{task}"}),
    ("F1 users_get", "users_get", {"id": "{user}"}),
    ("F1 users_get_by_login", "users_get_by_login", {"login": "{user.login}"}),
    ("F1 users_get_by_email", "users_get_by_email", {"email": "{user.email}"}),
    ("F1 users_get_group", "users_get_group", {"id": "{group}"}),
    ("F1 workstations_get", "workstations_get", {"id": "{workstation}"}),
    ("F1 payments_get", "payments_get", {"id": "{payment}"}),
    ("F1 orders_get_line", "orders_get_line", {"id": "{order}", "lineid": "{order_line.id}"}),
    ("F1 products_get_stock", "products_get_stock", {"id": "{product}"}),
    ("F1 bankaccounts_get", "bankaccounts_get", {"id": "{bankaccount}"}),
    # F2: List GET checks
    ("F2 thirdparties_list", "thirdparties_list", {}),
    ("F2 products_list", "products_list", {}),
    ("F2 contacts_list", "contacts_list", {}),
    ("F2 invoices_list", "invoices_list", {}),
    ("F2 orders_list", "orders_list", {}),
    ("F2 proposals_list", "proposals_list", {}),
    ("F2 supplier_invoices_list", "supplier_invoices_list", {}),
    ("F2 supplier_orders_list", "supplier_orders_list", {}),
    ("F2 supplier_proposals_list", "supplier_proposals_list", {}),
    ("F2 contracts_list", "contracts_list", {}),
    ("F2 shipments_list", "shipments_list", {}),
    ("F2 receptions_list", "receptions_list", {}),
    ("F2 interventions_list", "interventions_list", {}),
    ("F2 expense_reports_list", "expense_reports_list", {}),
    ("F2 holidays_list", "holidays_list", {}),
    ("F2 agenda_events_list", "agenda_events_list", {}),
    ("F2 categories_list", "categories_list", {}),
    ("F2 mailings_list", "mailings_list", {}),
    ("F2 multi_currencies_list", "multi_currencies_list", {}),
    ("F2 tickets_list", "tickets_list", {}),
    ("F2 warehouses_list", "warehouses_list", {}),
    ("F2 stockmovements_list", "stockmovements_list", {}),
    ("F2 productlots_list", "productlots_list", {}),
    ("F2 boms_list", "boms_list", {}),
    ("F2 mos_list", "mos_list", {}),
    ("F2 projects_list", "projects_list", {}),
    ("F2 tasks_list", "tasks_list", {}),
    ("F2 users_list_groups", "users_list_groups", {}),
    ("F2 documents_list", "documents_list", {"modulepart": "propal", "id": 1}),
    # F3: Sub-resource GET checks
    ("F3 proposals_get_lines", "proposals_get_lines", {"id": "{proposal}"}),
    ("F3 proposals_get_contacts", "proposals_get_contacts", {"id": "{proposal}"}),
    ("F3 orders_get_lines", "orders_get_lines", {"id": "{order}"}),
    ("F3 orders_get_contacts", "orders_get_contacts", {"id": "{order}"}),
    ("F3 invoices_get_lines", "invoices_get_lines", {"id": "{invoice}"}),
    ("F3 invoices_get_contacts", "invoices_get_contacts", {"id": "{invoice}"}),
    ("F3 invoices_get_payments", "invoices_get_payments", {"id": "{invoice}"}),
    ("F3 supplier_invoices_get_lines", "supplier_invoices_get_lines", {"id": "{supplier_invoice}"}),
    ("F3 supplier_invoices_get_payments", "supplier_invoices_get_payments", {"id": "{supplier_invoice}"}),
    ("F3 supplier_orders_get_contacts", "supplier_orders_get_contacts", {"id": "{supplier_order}"}),
    ("F3 contracts_get_lines", "contracts_get_lines", {"id": "{contract}"}),
    ("F3 boms_get_lines", "boms_get_lines", {"id": "{bom}"}),
    ("F3 expense_reports_get_lines", "expense_reports_get_lines", {"id": "{expense_report}"}),
    ("F3 interventions_get_contacts", "interventions_get_contacts", {"id": "{intervention}"}),
    ("F3 tasks_get_contacts", "tasks_get_contacts", {"id": "{task}"}),
    ("F3 projects_get_tasks", "projects_get_tasks", {"id": "{project}"}),
    ("F3 projects_get_contacts", "projects_get_contacts", {"id": "{project}"}),
    ("F3 thirdparties_get_outstanding_proposals", "thirdparties_get_outstanding_proposals", {"id": "{thirdparty}"}),
    ("F3 thirdparties_get_outstanding_orders", "thirdparties_get_outstanding_orders", {"id": "{thirdparty}"}),
    ("F3 thirdparties_get_outstanding_invoices", "thirdparties_get_outstanding_invoices", {"id": "{thirdparty}"}),
    ("F3 thirdparties_get_categories", "thirdparties_get_categories", {"id": "{thirdparty}"}),
    ("F3 contacts_get_categories", "contacts_get_categories", {"id": "{contact}"}),
    ("F3 products_get_categories", "products_get_categories", {"id": "{product}"}),
    ("F3 products_get_subproducts", "products_get_subproducts", {"id": "{product}"}),
    ("F3 products_get_contacts", "products_get_contacts", {"id": "{product}"}),
    ("F3 multi_currencies_get_rates", "multi_currencies_get_rates", {"id": "{multi_currency}"}),
    ("F3 thirdparties_get_representatives", "thirdparties_get_representatives", {"id": "{thirdparty}"}),
    ("F3 users_get_user_groups", "users_get_user_groups", {"id": "{user}"}),
    ("F3 contracts_get_lines", "contracts_get_lines", {"id": "{contract}"}),
    ("F3 warehouses_list_products", "warehouses_list_products", {"id": "{warehouse}"}),
]

async def main():
    print(f"# Test Report — Dolibarr MCP Server")
    print(f"\n**Date**: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    print(f"**Server**: {MCP_URL}")
    print(f"**Run ID**: {rid}")
    print()

    async with MCPSession(MCP_URL, MCP_HEADERS) as session:
        # Phase 0: Tool Discovery
        log("\n=== Phase 0: Tool Discovery ===")
        tools_list = await session.list_tools()
        tool_names = [t["name"] for t in tools_list]
        total_discovered = len(tool_names)
        print(f"**Discovered**: {total_discovered} tools")
        log(f"Tools: {', '.join(sorted(tool_names))}")

        # Coverage check
        tested_tools = set()
        for entry in RESOURCE_TESTS:
            for k in ("list", "get", "create", "update", "delete"):
                v = entry.get(k)
                isinstance(v, str) and tested_tools.add(v) or isinstance(v, tuple) and tested_tools.add(v[0]) or None
            for st, _ in entry.get("sub_tests", []): tested_tools.add(st)
        for _, t, _ in LIST_ONLY_TESTS: tested_tools.add(t)
        for e in PHASE4_TESTS: tested_tools.add(e[1])
        for _, t, _ in FILTERING_CHECKS: tested_tools.add(t)
        tested_tools.add("status_get")
        tested_tools.update(["payment_types_list", "expense_types_list", "holiday_types_list"])
        untested = sorted(t for t in tool_names if t not in tested_tools)
        log(untested and f"FAIL Untested tools: {', '.join(untested)}" or f"PASS all {total_discovered} tools covered")

        # Phase 1: Status check
        log("\n=== Phase 1: Status ===")
        await run_test(session, "A1 status_get", "status_get")

        # Phase 2: List Tools
        log("\n=== Phase 2: List Tools ===")
        for entry in RESOURCE_TESTS:
            label, key = entry["label"], entry["label"].lower()
            list_info = entry.get("list") or ""
            list_tool = isinstance(list_info, tuple) and list_info[0] or list_info
            list_params = isinstance(list_info, tuple) and list_info[1] or {}
            await run_test(session, f"B2 list_{label.lower()}", list_tool, list_params)
        for label, tool, params in LIST_ONLY_TESTS:
            await run_test(session, f"B2 list_{label.lower()}", tool, params)

        # Phase 3.5: Reference Data Discovery
        log("\n=== Phase 3.5: Reference Data Discovery ===")
        for discovery_tool, discovery_key in [("payment_types_list", "payment_type_id"), ("expense_types_list", "expense_type_id"), ("holiday_types_list", "holiday_type_id")]:
            result = await session.call_tool(discovery_tool, {})
            err = is_error(result)
            err or (lambda: None)()
            raw = extract_content(result)
            raw = isinstance(raw, dict) and "items" in raw and raw["items"] or raw
            raw = isinstance(raw, str) and toon_to_json(raw) or raw
            first_id = isinstance(raw, list) and len(raw) > 0 and (raw[0].get("id") or raw[0].get("rowid")) or None
            first_id and store.update({discovery_key: {"id": first_id}}) and log(f"  FOUND {discovery_key} = {first_id}") or None

        # Phase 3A: Create Resources
        log("\n=== Phase 3A: Create Resources ===")
        for entry in RESOURCE_TESTS:
            label, key = entry["label"], entry["label"].lower()
            store_key = entry.get("store_key", key)
            create_info = entry.get("create")
            store.pop(store_key, None)
            created.pop(f"create_{key}", None)
            create_tool, create_params = create_info or (None, {})
            ok = await run_test_with_store(session, f"C1 create_{key}", create_tool or "", create_params, store_key=store_key)
            v = store.get(store_key)
            store_key and store.update({store_key: isinstance(v, dict) and v or {"id": v}})

        # Phase 3A.5: Fetch records
        log("\n=== Phase 3A.5: Fetch Records ===")
        for entry in RESOURCE_TESTS:
            label, key = entry["label"], entry["label"].lower()
            store_key = entry.get("store_key", key)
            get_tool = entry.get("get") or ""
            cid = pick_id(store_key) or 0
            await run_test_with_store(session, f"C1b fetch_{key}", get_tool, {"id": cid}, store_key=store_key)

        # Phase 3B.1: Get/Update/Sub-tests
        log("\n=== Phase 3B.1: Get/Update/Sub-tests ===")
        for entry in reversed(RESOURCE_TESTS):
            label, key = entry["label"], entry["label"].lower()
            store_key = entry.get("store_key", key)
            get_tool = entry.get("get") or ""
            update_info = entry.get("update")
            sub_tests = entry.get("sub_tests", [])
            cid = pick_id(store_key) or 0
            update_tool = update_info and update_info[0] or ""
            await run_test_with_store(session, f"C2 get_{key}_by_id", get_tool, {"id": cid}, store_key=f"get_{key}")
            update_tool and await run_test_with_store(session, f"C3 update_{key}", update_tool, dict(update_info[1], id=cid), store_key=store_key)
            for sub_tool, sub_params in sub_tests:
                sp = dict(sub_params)
                auto_inject = sp.pop("_auto_inject_id", False)
                isinstance(True, bool) and not auto_inject and sp.update({"id": cid})
                await run_test(session, f"C3s {key}_{sub_tool}", sub_tool, sp)

        # Phase 4: Domain-Specific Tools
        log("\n=== Phase 4: Domain-Specific Tools ===")
        for entry in PHASE4_TESTS:
            label, tool, params = entry[0], entry[1], entry[2]
            store_key = len(entry) == 4 and entry[3] or None
            ok = await run_test_with_store(session, label, tool, params, store_key=store_key)
            for v in ok and store_key and [store.get(store_key)] or []:
                store[store_key] = isinstance(v, dict) and v or {"id": v}

        # Phase 5: Field Filtering
        log("\n=== Phase 5: Field Filtering ===")
        for label, tool, params in FILTERING_CHECKS:
            await run_filtering_check(session, label, tool, params)

        # Phase 5.5: Line Cleanup
        log("\n=== Phase 5.5: Line Cleanup ===")
        for label, tool, params in [
            ("P4_orders_delete_line", "orders_delete_line", {"id": "{order}", "lineid": "{order_line.id}"}),
            ("P4_invoices_delete_line", "invoices_delete_line", {"id": "{invoice}", "lineid": "{invoice_line.id}"}),
            ("P4_bankaccounts_delete_line", "bankaccounts_delete_line", {"id": "{bankaccount}", "line_id": "{bank_line.id}"}),
            ("P4_supplier_invoices_delete_line", "supplier_invoices_delete_line", {"id": "{supplier_invoice}", "lineid": "{supplier_invoice_line.id}"}),
            ("P4_contracts_delete_line", "contracts_delete_line", {"id": "{contract}", "lineid": "{contract_line.id}"}),
            ("P4_boms_delete_line", "boms_delete_line", {"id": "{bom}", "lineid": "{bom_line.id}"}),
        ]:
            await run_test(session, label, tool, params)

        # Phase 3B.2: Delete + Verify
        log("\n=== Phase 3B.2: Delete/Verify ===")
        for entry in reversed(RESOURCE_TESTS):
            label, key = entry["label"], entry["label"].lower()
            store_key = entry.get("store_key", key)
            get_tool = entry.get("get") or ""
            delete_tool = entry.get("delete") or ""
            cid = pick_id(store_key) or 0
            await run_test(session, f"C4 delete_{key}", delete_tool, {"id": cid})
            await run_verify_delete(session, f"C5 verify_delete_{key}", get_tool, {"id": cid})

        # Phase 6: Negative Tests
        log("\n=== Phase 6: Negative Tests ===")
        for label, tool, params, _ in [
            ("C6 invalid_tool", "nonexistent_tool", {}, "Unknown tool"),
            ("C6 invalid_user_id", "users_get", {"id": 99999999}, "not found"),
            ("C6 invalid_thirdparty_id", "thirdparties_get", {"id": 99999999}, "not found"),
            ("C6 invalid_product_id", "products_get", {"id": 99999999}, "not found"),
            ("C6 invalid_invoice_id", "invoices_get", {"id": 99999999}, "not found"),
            ("C6 invalid_delete", "products_delete", {"id": 99999999}, "not found"),
            ("C6 delete_nonexistent_warehouse", "warehouses_delete", {"id": 99999999}, "not found"),
            ("C6 missing_params_products_create", "products_create", {}, "required"),
        ]:
            rp = resolve_params(params)
            result = await session.call_tool(tool, rp)
            err = is_error(result)
            statuses = {True: "PASSED", False: "FAILED"}
            results.append({
                "label": label, "tool": tool, "status": statuses[bool(err)],
                "reason": err and f"Got expected error: {err[:80]}" or "Expected error but got success"
            })
            labels = {True: "PASS", False: "FAIL"}
            log(f"  {labels[bool(err)]} {label}: {err and 'got error as expected' or 'expected error, got success'}")

        # Report Summary
        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        total = len(results)
        print(f"\n## Summary\n")
        print(f"| Status | Count |")
        print(f"|--------|-------|")
        print(f"| PASSED | {passed} |")
        print(f"| FAILED | {failed} |")
        print(f"\n## PASSED ({passed})\n")
        for r in results:
            r["status"] == "PASSED" and print(f"- `{r['tool']}` — {r['label']}")
        print(f"\n## FAILED ({failed})\n")
        for r in results:
            r["status"] == "FAILED" and print(f"### {r['label']}") or None
            r["status"] == "FAILED" and print(f"- **Error**: {r['reason']}") or None
            r["status"] == "FAILED" and print() or None
        print(f"\n---")
        print(f"**Total tests:** {total} | **PASSED:** {passed} | **FAILED:** {failed}")
        print(failed == 0 and "\n**ALL TESTS PASS**" or "\n**TESTS FAILING** — see above for details")

__name__ == "__main__" and (lambda: (__import__('asyncio').run(main())))() or None
