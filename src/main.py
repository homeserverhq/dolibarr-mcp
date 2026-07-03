import os
import sys
from contextvars import ContextVar
from typing import Any, Optional

from fastmcp import FastMCP, Context
from pydantic import BaseModel
from toon_mcp import json_to_toon

from.client import DolibarrClient, _normalize_datetime, _to_timestamp

ALLOW_ALL_AGGREGATE = os.getenv("ALLOW_ALL_AGGREGATE", "false").lower() in ("true", "1", "yes")

_current_user_token: ContextVar[Optional[str]] = ContextVar(
    "current_user_token", default=None
)


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                _current_user_token.set(token)
        await self.app(scope, receive, send)


mcp = FastMCP("dolibarr-mcp-server")

_client: Optional[DolibarrClient] = None


def get_client() -> DolibarrClient:
    global _client
    if _client is None:
        _client = DolibarrClient()
    return _client


def get_user_token() -> Optional[str]:
    return _current_user_token.get()


# ============================================================
# Pydantic Contract Models
# ============================================================

class CreateThirdPartyParam(BaseModel):
    name: str
    client: int
    fournisseur: int
    address: str = ""
    zip: str = ""
    town: str = ""
    country_id: int = 0
    country_code: str = ""
    phone: str = ""
    email: str = ""
    url: str = ""
    code_client: str = ""
    code_fournisseur: str = ""
    capital: int = 0
    siren: str = ""
    siret: str = ""
    ape: str = ""
    tva_intra: str = ""
    status: int = 1
    note_public: str = ""
    note_private: str = ""
    parent: int = 0
    price_level: int = 0
    outstanding_limit: float = 0.0
    multicurrency_code: str = ""


class UpdateThirdPartyParam(BaseModel):
    name: Optional[str] = None
    client: Optional[int] = None
    fournisseur: Optional[int] = None
    address: Optional[str] = None
    zip: Optional[str] = None
    town: Optional[str] = None
    country_id: Optional[int] = None
    country_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    url: Optional[str] = None
    code_client: Optional[str] = None
    code_fournisseur: Optional[str] = None
    capital: Optional[int] = None
    siren: Optional[str] = None
    siret: Optional[str] = None
    ape: Optional[str] = None
    tva_intra: Optional[str] = None
    status: Optional[int] = None
    note_public: Optional[str] = None
    note_private: Optional[str] = None
    parent: Optional[int] = None
    price_level: Optional[int] = None
    outstanding_limit: Optional[float] = None
    multicurrency_code: Optional[str] = None


class CreateContactParam(BaseModel):
    lastname: str
    socid: int
    firstname: str = ""
    address: str = ""
    zip: str = ""
    town: str = ""
    country_id: int = 0
    phone: str = ""
    phone_mobile: str = ""
    email: str = ""
    skype: str = ""
    note_public: str = ""
    note_private: str = ""
    status: int = 1
    birthday: str = ""
    poste: str = ""
    default_lang: str = ""


class CreateProductParam(BaseModel):
    ref: str
    label: str
    type: int
    status: int
    price: float
    price_base_type: str
    description: str = ""
    note_public: str = ""
    note_private: str = ""
    duration_value: float = 0.0
    duration_unit: str = ""
    barcode: str = ""
    tva_tx: float = 0.0
    stock: float = 0.0
    pmp: float = 0.0
    weight: float = 0.0
    weight_units: int = 0
    length: float = 0.0
    width: float = 0.0
    height: float = 0.0
    surface: float = 0.0
    volume: float = 0.0
    country_id: int = 0
    seuil_stock_alerte: float = 0.0
    desiredstock: float = 0.0
    accountancy_code_sell: str = ""
    accountancy_code_buy: str = ""
    customcode: str = ""
    multicurrency_code: str = ""
    multicurrency_price: float = 0.0


class CreateWarehouseParam(BaseModel):
    ref: str
    label: str
    status: int
    description: str = ""
    lieu: str = ""
    address: str = ""
    zip: str = ""
    town: str = ""
    country_id: int = 0
    phone: str = ""
    fax: str = ""
    accountancy_code: str = ""


class CreateStockMovementParam(BaseModel):
    product_id: int
    warehouse_id: int
    qty: float
    type: int
    batch: str = ""
    movementcode: str = ""
    label: str = ""
    price: float = 0.0
    datem: str = ""
    sellBy: str = ""
    eatBy: str = ""
    origin_type: str = ""
    origin_id: int = 0


class CreateProductLotParam(BaseModel):
    ref: str
    fk_product: int
    batch: str
    qty: float = 0.0
    warehouse_id: int = 0
    price: float = 0.0
    datem: str = ""
    eatby: str = ""
    sellby: str = ""
    note_public: str = ""
    note_private: str = ""


class CreateProposalParam(BaseModel):
    socid: int
    date: str
    ref: str = ""
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    total_ht: float = 0.0
    total_tva: float = 0.0
    total_ttc: float = 0.0
    multicurrency_code: str = ""
    payment_terms: int = 0
    delivery_date: str = ""


class CreateProposalLineParam(BaseModel):
    desc: str
    qty: float
    subprice: float
    product_id: int = 0
    tva_tx: float = 0.0
    remise_percent: float = 0.0
    remise: float = 0.0
    price_base_type: str = "HT"
    date_start: str = ""
    date_end: str = ""
    product_type: int = 0
    rang: int = 0


class CreateOrderParam(BaseModel):
    socid: int
    date: str
    ref: str = ""
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    total_ht: float = 0.0
    total_tva: float = 0.0
    total_ttc: float = 0.0
    multicurrency_code: str = ""
    payment_terms: int = 0
    delivery_date: str = ""


class CreateOrderLineParam(BaseModel):
    desc: str
    qty: float
    subprice: float
    product_id: int = 0
    tva_tx: float = 0.0
    remise_percent: float = 0.0
    price_base_type: str = "HT"
    date_start: str = ""
    date_end: str = ""
    product_type: int = 0
    rang: int = 0


class CreateInvoiceParam(BaseModel):
    socid: int
    date: str
    type: int
    ref: str = ""
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    total_ht: float = 0.0
    total_tva: float = 0.0
    total_ttc: float = 0.0
    multicurrency_code: str = ""
    payment_terms: int = 0


class CreateInvoiceLineParam(BaseModel):
    desc: str
    qty: float
    subprice: float
    product_id: int = 0
    tva_tx: float = 0.0
    remise_percent: float = 0.0
    price_base_type: str = "HT"
    date_start: str = ""
    date_end: str = ""
    product_type: int = 0
    rang: int = 0


class CreateInvoicePaymentParam(BaseModel):
    datepaye: str
    paymentid: int
    accountid: int
    closepaidinvoices: str = "no"
    num_payment: str = ""
    comment: str = ""
    amount: float = 0.0
    chqemetteur: str = ""
    chqbank: str = ""


class CreateInvoiceContactParam(BaseModel):
    fk_socpeople: int
    type_contact: str
    source: str = "external"
    notrigger: int = 0


class CreateTicketMessageParam(BaseModel):
    track_id: str
    message: str
    fk_user_author: int = 0
    note_public: str = ""
    note_private: str = ""


class CreateBankAccountParam(BaseModel):
    ref: str
    label: str
    type: int
    currency_code: str
    account_number: str = ""
    country_id: int = 0
    bank: str = ""
    code_banque: str = ""
    code_guichet: str = ""
    cle_rib: str = ""
    bic: str = ""
    iban: str = ""
    domiciliation: str = ""
    state_id: int = 0
    opening_balance: float = 0.0
    min_balance: float = 0.0
    proprio: str = ""
    note_public: str = ""
    note_private: str = ""
    status: int = 1


class CreateBankAccountLineParam(BaseModel):
    date: str
    type: str
    label: str
    amount: float
    category: int = 0
    cheque_number: str = ""
    cheque_writer: str = ""
    cheque_bank: str = ""
    accountancycode: str = ""
    datev: str = ""
    num_releve: str = ""


class CreateBankAccountTransferParam(BaseModel):
    bankaccount_from_id: int
    bankaccount_to_id: int
    date: str
    description: str
    amount: float
    amount_to: float = 0.0
    cheque_number: str = ""


class CreateSupplierOrderParam(BaseModel):
    socid: int
    date: str
    ref: str = ""
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    total_ht: float = 0.0
    total_tva: float = 0.0
    total_ttc: float = 0.0
    multicurrency_code: str = ""


class CreateSupplierOrderLineParam(BaseModel):
    desc: str
    qty: float
    subprice: float
    product_id: int = 0
    tva_tx: float = 0.0
    remise_percent: float = 0.0
    price_base_type: str = "HT"
    date_start: str = ""
    date_end: str = ""
    product_type: int = 0
    rang: int = 0


class CreateSupplierInvoiceParam(BaseModel):
    socid: int
    date: str
    ref: str = ""
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    total_ht: float = 0.0
    total_tva: float = 0.0
    total_ttc: float = 0.0
    multicurrency_code: str = ""


class CreateSupplierInvoiceLineParam(BaseModel):
    desc: str
    qty: float
    subprice: float
    product_id: int = 0
    tva_tx: float = 0.0
    remise_percent: float = 0.0
    price_base_type: str = "HT"


class CreateSupplierInvoicePaymentParam(BaseModel):
    datepaye: str
    payment_mode_id: int
    accountid: int
    closepaidinvoices: str = "no"
    num_payment: str = ""
    comment: str = ""
    amount: float = 0.0


class CreateSupplierProposalParam(BaseModel):
    socid: int
    date: str
    ref: str = ""
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    total_ht: float = 0.0
    total_tva: float = 0.0
    total_ttc: float = 0.0


class CreateContractParam(BaseModel):
    socid: int
    ref: str
    date_contrat: str
    commercial_signature_id: int = 0
    commercial_suivi_id: int = 0
    status: int = 0
    note_public: str = ""
    note_private: str = ""


class CreateContractLineParam(BaseModel):
    desc: str = ""
    qty: float = 0.0
    subprice: float = 0.0
    product_id: int = 0
    tva_tx: float = 0.0
    date_start: str = ""
    date_end: str = ""
    remise_percent: float = 0.0
    price_base_type: str = "HT"


class CreateContractActivateLineParam(BaseModel):
    datestart: str
    dateend: str = ""
    comment: str = ""


class CreateBomParam(BaseModel):
    ref: str
    label: str
    fk_product: int
    qty: float
    bomtype: int = 0
    status: int = 0
    description: str = ""
    note_public: str = ""
    note_private: str = ""
    duration: float = 0.0
    efficiency: float = 0.0
    warehouse_id: int = 0


class CreateBomLineParam(BaseModel):
    fk_product: int = 0
    qty: float = 0.0
    desc: str = ""
    warehouse_id: int = 0
    position: int = 0


class CreateMOParam(BaseModel):
    ref: str
    label: str
    fk_product: int
    qty: float
    fk_warehouse: int
    mrptype: int = 0
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    date_planned: str = ""
    bom_id: int = 0
    priority: int = 0


class CreateProjectParam(BaseModel):
    ref: str
    title: str
    socid: int = 0
    description: str = ""
    note_public: str = ""
    note_private: str = ""
    status: int = 0
    date_start: str = ""
    date_end: str = ""
    budget_amount: float = 0.0
    usage_opportunity: int = 0
    usage_task: int = 0
    usage_bill_time: int = 0
    usage_organize_event: int = 0
    public: int = 0
    percent: int = 0



class CreateTaskParam(BaseModel):
    ref: str
    label: str
    fk_project: int
    description: str = ""
    note_public: str = ""
    note_private: str = ""
    status: int = 0
    date_start: str = ""
    date_end: str = ""
    planned_workload: float = 0.0
    progress: int = 0
    budget_amount: float = 0.0


class CreateTaskTimeSpentParam(BaseModel):
    date: str
    duration: float
    product_id: int = 0
    user_id: int = 0
    note: str = ""
    progress: int = 0


class CreateShipmentParam(BaseModel):
    socid: int
    ref: str
    origin_id: int = 0
    origin_type: str = ""
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    date_delivery: str = ""
    shipping_method_id: int = 0
    warehouse_id: int = 0
    total_ht: float = 0.0
    total_tva: float = 0.0
    total_ttc: float = 0.0
    weight: float = 0.0
    volume: float = 0.0


class CreateReceptionParam(BaseModel):
    socid: int
    ref: str
    origin_id: int = 0
    origin_type: str = ""
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    date_delivery: str = ""
    warehouse_id: int = 0
    total_ht: float = 0.0
    total_tva: float = 0.0
    total_ttc: float = 0.0


class CreateInterventionParam(BaseModel):
    socid: int
    ref: str = ""
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    date: str = ""
    description: str = ""
    fk_user_author: int = 0
    fk_user_intervenant: int = 0
    fk_project: int = 0


class CreateInterventionLineParam(BaseModel):
    description: str = ""
    duration: float = 0.0
    product_id: int = 0
    qty: float = 0.0
    subprice: float = 0.0
    tva_tx: float = 0.0
    date: str = ""
    price_base_type: str = "HT"
    rang: int = 0


class CreateExpenseReportParam(BaseModel):
    fk_user: int
    date_debut: str
    date_fin: str
    fk_user_author: int
    ref: str = ""
    status: int = 0
    note_public: str = ""
    note_private: str = ""
    total_ht: float = 0.0
    total_tva: float = 0.0
    total_ttc: float = 0.0
    fk_project: int = 0


class CreateExpenseReportLineParam(BaseModel):
    date: str
    fk_c_type_fees: int
    qty: float
    value_unit: float
    product_id: int = 0
    comment: str = ""
    vatrate: float = 0.0
    localtax1_tx: float = 0.0
    localtax2_tx: float = 0.0
    fk_project: int = 0
    fk_soc: int = 0


class CreateHolidayParam(BaseModel):
    fk_user: int
    date_debut: str
    date_fin: str
    halfday: int
    fk_type: int
    fk_validator: int = 0
    note: str = ""
    status: int = 0


class CreateAgendaEventParam(BaseModel):
    type_code: str
    datep: str
    label: str
    note: str = ""
    author_user_id: int = 0
    userownerid: int = 0
    socid: int = 0
    fk_project: int = 0
    datep2: str = ""
    duration: int = 0
    location: str = ""
    percent: int = 0
    fulldayevent: int = 0
    punctual: int = 0


class UpdateContactParam(BaseModel):
    lastname: Optional[str] = None
    socid: Optional[int] = None
    firstname: Optional[str] = None
    address: Optional[str] = None
    zip: Optional[str] = None
    town: Optional[str] = None
    country_id: Optional[int] = None
    phone: Optional[str] = None
    phone_mobile: Optional[str] = None
    email: Optional[str] = None
    skype: Optional[str] = None
    note_public: Optional[str] = None
    note_private: Optional[str] = None
    status: Optional[int] = None
    birthday: Optional[str] = None
    poste: Optional[str] = None
    default_lang: Optional[str] = None


class CreateCategoryParam(BaseModel):
    ref: str
    label: str
    type: str
    description: str = ""
    color: str = ""
    parent: int = 0
    note_public: str = ""
    note_private: str = ""
    status: int = 1


class CreateMailingParam(BaseModel):
    title: str
    sujet: str
    body: str
    email_from: str
    mail_template_id: int = 0
    mail_subject: str = ""
    note: str = ""
    status: int = 0
    email_to: str = ""
    email_cc: str = ""
    email_bcc: str = ""
    lang: str = ""


class CreateMultiCurrencyParam(BaseModel):
    code: str
    name: str
    rate: float = 1.0
    status: int = 1
    note: str = ""


class CreateTicketParam(BaseModel):
    subject: str
    type_code: str
    severity_code: str
    category_code: str
    socid: int = 0
    note_public: str = ""
    note_private: str = ""
    track_id: str = ""
    fk_user_assign: int = 0
    email: str = ""
    origin: str = ""
    origin_id: int = 0
    message: str = ""



class CreateObjectLinkParam(BaseModel):
    fk_source: int
    sourcetype: str
    fk_target: int
    targettype: str
    relationtype: str = ""


class ReceiveLine(BaseModel):
    id: int
    qty: float
    warehouse: int
    fk_product: int


class ConsumeLine(BaseModel):
    objectid: int
    qty: float
    fk_warehouse: int


class ProduceLine(BaseModel):
    objectid: int
    qty: float
    fk_warehouse: int


# ============================================================
# Status
# ============================================================
@mcp.tool(tags={"basic", "dolibarr", "read"})
async def status_get(ctx: Context = None) -> dict[str, Any]:
    """Check connectivity to the Dolibarr backend."""
    import httpx
    client = get_client()
    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            response = await http_client.get(f"{client.base_url}/status/", headers={"Authorization": f"Bearer {get_user_token()}"})
            return {"status": "connected", "backend_response": response.status_code}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}

# ============================================================
# Documents
# ============================================================
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def documents_list(
    modulepart: str,
    id: int,
    ref: str = "",
    include_all_fields: bool = False,
    sortfield: str = "",
    sortorder: str = "ASC",
    limit: int = 100,
    page: int = 0,
    ctx: Context = None
) -> dict[str, Any]:
    """List documents/attachments for a given element.

    Use documents_list_types first to discover which modulepart values are available.

    Args:
        modulepart: Object type to list documents for. Accepted values (any common alias works):
            "thirdparty"/"societe"/"company" - Third parties
            "user" - Users
            "member"/"adherent" - Members
            "proposal"/"propal" - Commercial proposals
            "supplier_proposal" - Supplier proposals
            "order"/"commande" - Customer orders
            "supplier_order"/"commande_fournisseur" - Supplier orders
            "shipment"/"expedition"/"shipping" - Shipments
            "invoice"/"facture" - Customer invoices
            "supplier_invoice"/"facture_fournisseur" - Supplier invoices
            "product"/"produit"/"service" - Products and services
            "event"/"agenda"/"action" - Agenda events
            "expense_report"/"expensereport" - Expense reports
            "holiday" - Leave requests
            "ticket" - Tickets
            "knowledge"/"knowledgemanagement" - Knowledge records
            "category"/"categorie" - Categories
            "contract"/"contrat" - Contracts
            "intervention"/"fichinter" - Interventions
            "project"/"projet" - Projects
            "task"/"project_task" - Project tasks
            "mrp"/"manufacturing_order" - Manufacturing orders
            "contact"/"socpeople" - Contacts
            "stock"/"warehouse"/"entrepot" - Warehouses/stock
            "bank"/"banque"/"bankaccount" - Bank accounts.
        id: The unique ID of the resource.
        ref: Reference.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
    """
    data = await get_client().documents_list(
        get_user_token(), modulepart=modulepart, id=id, ref=ref,
        include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False, sortfield=sortfield,
        sortorder=sortorder, limit=limit, page=page
    )
    return {"items": json_to_toon(data)}


@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def documents_list_types(ctx: Context = None) -> dict[str, Any]:
    """List all available document module types that can be used with documents_list.

    Use this tool first to discover valid modulepart values,
    then call documents_list with the chosen modulepart and an object ID.
    """
    return {
        "types": [
            {"type": "thirdparty", "aliases": ["societe", "company"], "description": "Third parties"},
            {"type": "user", "aliases": [], "description": "Users"},
            {"type": "member", "aliases": ["adherent"], "description": "Members"},
            {"type": "proposal", "aliases": ["propal"], "description": "Commercial proposals"},
            {"type": "supplier_proposal", "aliases": [], "description": "Supplier proposals"},
            {"type": "order", "aliases": ["commande"], "description": "Customer orders"},
            {"type": "supplier_order", "aliases": ["commande_fournisseur"], "description": "Supplier orders"},
            {"type": "shipment", "aliases": ["expedition", "shipping"], "description": "Shipments"},
            {"type": "invoice", "aliases": ["facture"], "description": "Customer invoices"},
            {"type": "supplier_invoice", "aliases": ["facture_fournisseur"], "description": "Supplier invoices"},
            {"type": "product", "aliases": ["produit", "service"], "description": "Products and services"},
            {"type": "event", "aliases": ["agenda", "action"], "description": "Agenda events"},
            {"type": "expense_report", "aliases": ["expensereport"], "description": "Expense reports"},
            {"type": "holiday", "aliases": [], "description": "Leave requests"},
            {"type": "ticket", "aliases": [], "description": "Tickets"},
            {"type": "knowledge", "aliases": ["knowledgemanagement"], "description": "Knowledge records"},
            {"type": "category", "aliases": ["categorie"], "description": "Categories"},
            {"type": "contract", "aliases": ["contrat"], "description": "Contracts"},
            {"type": "intervention", "aliases": ["fichinter"], "description": "Interventions"},
            {"type": "project", "aliases": ["projet"], "description": "Projects"},
            {"type": "task", "aliases": ["project_task"], "description": "Project tasks"},
            {"type": "mrp", "aliases": ["manufacturing_order"], "description": "Manufacturing orders"},
            {"type": "contact", "aliases": ["socpeople"], "description": "Contacts"},
            {"type": "stock", "aliases": ["warehouse", "entrepot"], "description": "Warehouses and stock"},
            {"type": "bank", "aliases": ["banque", "bankaccount"], "description": "Bank accounts"},
        ]
    }


# ============================================================
# Third Parties
# ============================================================
@mcp.tool(tags={"basic", "dolibarr", "read"})
async def thirdparties_list(
    sortfield: str = "",
    sortorder: str = "ASC",
    limit: int = 100,
    page: int = 0,
    mode: str = "",
    category: int = 0,
    sqlfilters: str = "",
    include_all_fields: bool = False,
    ctx: Context = None
) -> dict[str, Any]:
    """List all third parties (customers, suppliers, prospects).

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        mode: Mode.
        category: Category ID filter.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().thirdparties_list(
        get_user_token(), sortfield=sortfield, sortorder=sortorder,
        limit=limit, page=page, mode=mode, category=category,
        sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False
    )
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"basic", "dolibarr", "read"})
async def thirdparties_get(
    id: int,
    include_all_fields: bool = False,
    ctx: Context = None
) -> dict[str, Any]:
    """Get a single third party by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().thirdparties_get(
        id, get_user_token(), include_all_fields=include_all_fields
    )

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def thirdparties_create(
    name: str,
    client: int,
    fournisseur: int,
    address: str = "",
    zip: str = "",
    town: str = "",
    country_id: int = 0,
    country_code: str = "",
    phone: str = "",
    email: str = "",
    url: str = "",
    code_client: str = "",
    code_fournisseur: str = "",
    capital: int = 0,
    siren: str = "",
    siret: str = "",
    ape: str = "",
    tva_intra: str = "",
    status: int = 1,
    note_public: str = "",
    note_private: str = "",
    parent: int = 0,
    price_level: int = 0,
    outstanding_limit: float = 0.0,
    multicurrency_code: str = "",
    ctx: Context = None
) -> dict[str, Any]:
    """Create a new third party.

    Args:
        name: Name.
        client: Is a customer (1=yes, 0=no).
        fournisseur: Is a supplier (1=yes, 0=no).
        address: Street address.
        zip: Postal/ZIP code.
        town: City/town.
        country_id: Country ID.
        country_code: Country code.
        phone: Phone number.
        email: Email address.
        url: Website URL.
        code_client: Customer code.
        code_fournisseur: Supplier code.
        capital: Company capital.
        siren: SIREN number.
        siret: SIRET number.
        ape: APE code.
        tva_intra: Intra-community VAT number.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        parent: Parent ID.
        price_level: Price level.
        outstanding_limit: Outstanding bill limit.
        multicurrency_code: Multi-currency code.
    """
    params = CreateThirdPartyParam(
        name=name, client=client, fournisseur=fournisseur,
        address=address, zip=zip, town=town, country_id=country_id,
        country_code=country_code, phone=phone, email=email, url=url,
        code_client=code_client, code_fournisseur=code_fournisseur,
        capital=capital, siren=siren, siret=siret, ape=ape,
        tva_intra=tva_intra, status=status, note_public=note_public,
        note_private=note_private, parent=parent, price_level=price_level,
        outstanding_limit=outstanding_limit, multicurrency_code=multicurrency_code,
    )
    return await get_client().thirdparties_create(
        params.model_dump(), get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def thirdparties_update(
    id: int,
    name: Optional[str] = None,
    client: Optional[int] = None,
    fournisseur: Optional[int] = None,
    address: Optional[str] = None,
    zip: Optional[str] = None,
    town: Optional[str] = None,
    country_id: Optional[int] = None,
    country_code: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    url: Optional[str] = None,
    code_client: Optional[str] = None,
    code_fournisseur: Optional[str] = None,
    capital: Optional[int] = None,
    siren: Optional[str] = None,
    siret: Optional[str] = None,
    ape: Optional[str] = None,
    tva_intra: Optional[str] = None,
    status: Optional[int] = None,
    note_public: Optional[str] = None,
    note_private: Optional[str] = None,
    parent: Optional[int] = None,
    price_level: Optional[int] = None,
    outstanding_limit: Optional[float] = None,
    multicurrency_code: Optional[str] = None,
    ctx: Context = None
) -> dict[str, Any]:
    """Update an existing third party.

    Args:
        id: The unique ID of the resource.
        name: Name.
        client: Is a customer (1=yes, 0=no).
        fournisseur: Is a supplier (1=yes, 0=no).
        address: Street address.
        zip: Postal/ZIP code.
        town: City/town.
        country_id: Country ID.
        country_code: Country code.
        phone: Phone number.
        email: Email address.
        url: Website URL.
        code_client: Customer code.
        code_fournisseur: Supplier code.
        capital: Company capital.
        siren: SIREN number.
        siret: SIRET number.
        ape: APE code.
        tva_intra: Intra-community VAT number.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        parent: Parent ID.
        price_level: Price level.
        outstanding_limit: Outstanding bill limit.
        multicurrency_code: Multi-currency code.
    """
    params = UpdateThirdPartyParam(
        name=name, client=client, fournisseur=fournisseur,
        address=address, zip=zip, town=town, country_id=country_id,
        country_code=country_code, phone=phone, email=email, url=url,
        code_client=code_client, code_fournisseur=code_fournisseur,
        capital=capital, siren=siren, siret=siret, ape=ape,
        tva_intra=tva_intra, status=status, note_public=note_public,
        note_private=note_private, parent=parent, price_level=price_level,
        outstanding_limit=outstanding_limit, multicurrency_code=multicurrency_code,
    )
    return await get_client().thirdparties_update(
        id, params.model_dump(exclude_none=True), get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def thirdparties_delete(
    id: int,
    ctx: Context = None
) -> dict[str, Any]:
    """Delete a third party by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().thirdparties_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def thirdparties_get_outstanding_proposals(
    id: int,
    mode: str = "",
    ctx: Context = None
) -> dict[str, Any]:
    """Get outstanding proposals for a third party.

    Args:
        id: The unique ID of the resource.
        mode: Mode.
    """
    data = await get_client().thirdparties_get_outstanding_proposals(id, get_user_token(), mode=mode)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def thirdparties_get_outstanding_orders(
    id: int,
    mode: str = "",
    ctx: Context = None
) -> dict[str, Any]:
    """Get outstanding orders for a third party.

    Args:
        id: The unique ID of the resource.
        mode: Mode.
    """
    data = await get_client().thirdparties_get_outstanding_orders(id, get_user_token(), mode=mode)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def thirdparties_get_outstanding_invoices(
    id: int,
    mode: str = "",
    ctx: Context = None
) -> dict[str, Any]:
    """Get outstanding invoices for a third party.

    Args:
        id: The unique ID of the resource.
        mode: Mode.
    """
    data = await get_client().thirdparties_get_outstanding_invoices(id, get_user_token(), mode=mode)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def thirdparties_get_representatives(
    id: int,
    mode: int = 0,
    ctx: Context = None
) -> dict[str, Any]:
    """Get representatives for a third party.

    Args:
        id: The unique ID of the resource.
        mode: Mode.
    """
    data = await get_client().thirdparties_get_representatives(id, get_user_token(), mode=mode)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def thirdparties_add_representative(id: int, fk_user: int, ctx: Context = None) -> dict[str, Any]:
    """Add a representative to a third party.

    Args:
        id: The unique ID of the third party.
        fk_user: User ID to set as representative.
    """
    return await get_client().thirdparties_add_representative(id, fk_user, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def thirdparties_delete_representative(id: int, representative_id: int, ctx: Context = None) -> dict[str, Any]:
    """Remove a representative from a third party.

    Args:
        id: The unique ID of the third party.
        representative_id: ID of the representative to remove.
    """
    return await get_client().thirdparties_delete_representative(id, representative_id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def thirdparties_get_categories(
    id: int,
    sortfield: str = "",
    sortorder: str = "ASC",
    limit: int = 100,
    page: int = 0,
    ctx: Context = None
) -> dict[str, Any]:
    """Get categories for a third party.

    Args:
        id: The unique ID of the resource.
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
    """
    data = await get_client().thirdparties_get_categories(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page)
    return {"items": json_to_toon(data)}

# ============================================================
# Contacts
# ============================================================
@mcp.tool(tags={"basic", "dolibarr", "read"})
async def contacts_list(
    sortfield: str = "",
    sortorder: str = "ASC",
    limit: int = 100,
    page: int = 0,
    thirdparty_ids: str = "",
    category: int = 0,
    sqlfilters: str = "",
    include_all_fields: bool = False,
    ctx: Context = None
) -> dict[str, Any]:
    """List all contacts.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        category: Category ID filter.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().contacts_list(
        get_user_token(), sortfield=sortfield, sortorder=sortorder,
        limit=limit, page=page, thirdparty_ids=thirdparty_ids,
        category=category, sqlfilters=sqlfilters,
        include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False
    )
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"basic", "dolibarr", "read"})
async def contacts_get(
    id: int,
    include_all_fields: bool = False,
    ctx: Context = None
) -> dict[str, Any]:
    """Get a single contact by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().contacts_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"basic", "dolibarr", "write"})
async def contacts_create(
    lastname: str,
    socid: int,
    firstname: str = "",
    address: str = "",
    zip: str = "",
    town: str = "",
    country_id: int = 0,
    phone: str = "",
    phone_mobile: str = "",
    email: str = "",
    skype: str = "",
    note_public: str = "",
    note_private: str = "",
    status: int = 1,
    birthday: str = "",
    poste: str = "",
    default_lang: str = "",
    ctx: Context = None
) -> dict[str, Any]:
    """Create a new contact.

    Args:
        lastname: Last name.
        socid: Third party ID.
        firstname: First name.
        address: Street address.
        zip: Postal/ZIP code.
        town: City/town.
        country_id: Country ID.
        phone: Phone number.
        phone_mobile: Mobile phone number.
        email: Email address.
        skype: Skype ID.
        note_public: Public note.
        note_private: Private note.
        status: Status.
        birthday: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        poste: Job position.
        default_lang: Default language code.
    """
    birthday = _normalize_datetime(birthday)
    params = CreateContactParam(
        lastname=lastname, socid=socid, firstname=firstname,
        address=address, zip=zip, town=town, country_id=country_id,
        phone=phone, phone_mobile=phone_mobile, email=email, skype=skype,
        note_public=note_public, note_private=note_private, status=status,
        birthday=birthday, poste=poste, default_lang=default_lang
    )
    return await get_client().contacts_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def contacts_update(
    id: int,
    lastname: Optional[str] = None,
    socid: Optional[int] = None,
    firstname: Optional[str] = None,
    address: Optional[str] = None,
    zip: Optional[str] = None,
    town: Optional[str] = None,
    country_id: Optional[int] = None,
    phone: Optional[str] = None,
    phone_mobile: Optional[str] = None,
    email: Optional[str] = None,
    skype: Optional[str] = None,
    note_public: Optional[str] = None,
    note_private: Optional[str] = None,
    status: Optional[int] = None,
    birthday: Optional[str] = None,
    poste: Optional[str] = None,
    default_lang: Optional[str] = None,
    ctx: Context = None
) -> dict[str, Any]:
    """Update an existing contact.

    Args:
        id: The unique ID of the resource.
        lastname: Last name.
        socid: Third party ID.
        firstname: First name.
        address: Street address.
        zip: Postal/ZIP code.
        town: City/town.
        country_id: Country ID.
        phone: Phone number.
        phone_mobile: Mobile phone number.
        email: Email address.
        skype: Skype ID.
        note_public: Public note.
        note_private: Private note.
        status: Status.
        birthday: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        poste: Job position.
        default_lang: Default language code.
    """
    birthday = _normalize_datetime(birthday) if birthday else birthday
    params = UpdateContactParam(
        lastname=lastname, socid=socid, firstname=firstname,
        address=address, zip=zip, town=town, country_id=country_id,
        phone=phone, phone_mobile=phone_mobile, email=email, skype=skype,
        note_public=note_public, note_private=note_private, status=status,
        birthday=birthday, poste=poste, default_lang=default_lang,
    )
    return await get_client().contacts_update(id, params.model_dump(exclude_none=True), get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def contacts_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a contact by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().contacts_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def contacts_get_categories(
    id: int,
    sortfield: str = "",
    sortorder: str = "ASC",
    limit: int = 100,
    page: int = 0,
    ctx: Context = None
) -> dict[str, Any]:
    """Get categories for a contact.

    Args:
        id: The unique ID of the resource.
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
    """
    data = await get_client().contacts_get_categories(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page)
    return {"items": json_to_toon(data)}

# ============================================================
# Products
# ============================================================
@mcp.tool(tags={"basic", "dolibarr", "read"})
async def products_list(
    sortfield: str = "",
    sortorder: str = "ASC",
    limit: int = 100,
    page: int = 0,
    mode: int = 0,
    category: int = 0,
    sqlfilters: str = "",
    variant_filter: str = "",
    include_all_fields: bool = False,
    ctx: Context = None
) -> dict[str, Any]:
    """List all products/services.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        mode: Mode.
        category: Category ID filter.
        sqlfilters: Dolibarr SQL filter syntax.
        variant_filter: Variant filter.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().products_list(
        get_user_token(), sortfield=sortfield, sortorder=sortorder,
        limit=limit, page=page, mode=mode, category=category,
        sqlfilters=sqlfilters, variant_filter=variant_filter,
        include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False
    )
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"basic", "dolibarr", "read"})
async def products_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single product by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().products_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"basic", "dolibarr", "write"})
async def products_create(
    ref: str, label: str, type: int, status: int, price: float, price_base_type: str,
    description: str = "", note_public: str = "", note_private: str = "",
    duration_value: float = 0.0, duration_unit: str = "", barcode: str = "",
    tva_tx: float = 0.0, stock: float = 0.0, pmp: float = 0.0,
    weight: float = 0.0, weight_units: int = 0, length: float = 0.0, width: float = 0.0,
    height: float = 0.0, surface: float = 0.0, volume: float = 0.0,
    country_id: int = 0, seuil_stock_alerte: float = 0.0, desiredstock: float = 0.0,
    accountancy_code_sell: str = "", accountancy_code_buy: str = "",
    customcode: str = "", multicurrency_code: str = "", multicurrency_price: float = 0.0,
    ctx: Context = None
) -> dict[str, Any]:
    """Create a new product or service.

    Args:
        ref: Reference.
        label: Label.
        type: Type.
        status: Status.
        price: Unit price.
        price_base_type: Price base type (HT or TTC).
        description: Description.
        note_public: Public note.
        note_private: Private note.
        duration_value: Duration value.
        duration_unit: Duration unit.
        barcode: Barcode.
        tva_tx: VAT rate.
        stock: Stock quantity.
        pmp: Average cost price.
        weight: Weight.
        weight_units: Weight units.
        length: Length.
        width: Width.
        height: Height.
        surface: Surface area.
        volume: Volume.
        country_id: Country ID.
        seuil_stock_alerte: Stock alert threshold.
        desiredstock: Desired stock level.
        accountancy_code_sell: Accounting code for sales.
        accountancy_code_buy: Accounting code for purchases.
        customcode: Customs code.
        multicurrency_code: Multi-currency code.
        multicurrency_price: Multi-currency price.
    """
    params = CreateProductParam(
        ref=ref, label=label, type=type, status=status, price=price,
        price_base_type=price_base_type, description=description,
        note_public=note_public, note_private=note_private,
        duration_value=duration_value, duration_unit=duration_unit,
        barcode=barcode, tva_tx=tva_tx, stock=stock, pmp=pmp,
        weight=weight, weight_units=weight_units, length=length,
        width=width, height=height, surface=surface, volume=volume,
        country_id=country_id, seuil_stock_alerte=seuil_stock_alerte,
        desiredstock=desiredstock, accountancy_code_sell=accountancy_code_sell,
        accountancy_code_buy=accountancy_code_buy, customcode=customcode,
        multicurrency_code=multicurrency_code, multicurrency_price=multicurrency_price
    )
    return await get_client().products_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def products_update(
    id: int,
    ref: Optional[str] = None, label: Optional[str] = None, type: Optional[int] = None,
    status: Optional[int] = None, price: Optional[float] = None, price_base_type: Optional[str] = None,
    description: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None,
    duration_value: Optional[float] = None, duration_unit: Optional[str] = None, barcode: Optional[str] = None,
    tva_tx: Optional[float] = None, stock: Optional[float] = None, pmp: Optional[float] = None,
    weight: Optional[float] = None, weight_units: Optional[int] = None, length: Optional[float] = None,
    width: Optional[float] = None, height: Optional[float] = None, surface: Optional[float] = None,
    volume: Optional[float] = None, country_id: Optional[int] = None,
    seuil_stock_alerte: Optional[float] = None, desiredstock: Optional[float] = None,
    accountancy_code_sell: Optional[str] = None, accountancy_code_buy: Optional[str] = None,
    customcode: Optional[str] = None, multicurrency_code: Optional[str] = None,
    multicurrency_price: Optional[float] = None,
    ctx: Context = None
) -> dict[str, Any]:
    """Update an existing product.

    Args:
        id: The unique ID of the resource.
        ref: Reference.
        label: Label.
        type: Type.
        status: Status.
        price: Unit price.
        price_base_type: Price base type (HT or TTC).
        description: Description.
        note_public: Public note.
        note_private: Private note.
        duration_value: Duration value.
        duration_unit: Duration unit.
        barcode: Barcode.
        tva_tx: VAT rate.
        stock: Stock quantity.
        pmp: Average cost price.
        weight: Weight.
        weight_units: Weight units.
        length: Length.
        width: Width.
        height: Height.
        surface: Surface area.
        volume: Volume.
        country_id: Country ID.
        seuil_stock_alerte: Stock alert threshold.
        desiredstock: Desired stock level.
        accountancy_code_sell: Accounting code for sales.
        accountancy_code_buy: Accounting code for purchases.
        customcode: Customs code.
        multicurrency_code: Multi-currency code.
        multicurrency_price: Multi-currency price.
    """
    payload = {k: v for k, v in {
        "ref": ref, "label": label, "type": type, "status": status,
        "price": price, "price_base_type": price_base_type,
        "description": description, "note_public": note_public, "note_private": note_private,
        "duration_value": duration_value, "duration_unit": duration_unit, "barcode": barcode,
        "tva_tx": tva_tx, "stock": stock, "pmp": pmp, "weight": weight,
        "weight_units": weight_units, "length": length, "width": width, "height": height,
        "surface": surface, "volume": volume, "country_id": country_id,
        "seuil_stock_alerte": seuil_stock_alerte, "desiredstock": desiredstock,
        "accountancy_code_sell": accountancy_code_sell,
        "accountancy_code_buy": accountancy_code_buy, "customcode": customcode,
        "multicurrency_code": multicurrency_code, "multicurrency_price": multicurrency_price,
    }.items() if v is not None}
    return await get_client().products_update(id, payload, get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def products_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a product by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().products_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def products_get_subproducts(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get sub-products for a product.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().products_get_subproducts(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def products_get_categories(
    id: int, sortfield: str = "", sortorder: str = "ASC",
    limit: int = 100, page: int = 0, ctx: Context = None
) -> dict[str, Any]:
    """Get categories for a product.

    Args:
        id: The unique ID of the resource.
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
    """
    data = await get_client().products_get_categories(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def products_get_stock(id: int, selected_warehouse_id: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Get stock information for a product.

    Args:
        id: The unique ID of the resource.
        selected_warehouse_id: Warehouse ID filter.
    """
    return await get_client().products_get_stock(id, get_user_token(), selected_warehouse_id=selected_warehouse_id)

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def products_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get contacts linked to a product.

    Args:
        id: The unique ID of the resource.
        type: Type.
    """
    data = await get_client().products_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

# ============================================================
# Warehouses
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def warehouses_list(
    sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0,
    category: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None
) -> dict[str, Any]:
    """List all warehouses.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        category: Category ID filter.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().warehouses_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, category=category, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def warehouses_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single warehouse by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().warehouses_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def warehouses_create(ref: str, label: str, status: int, description: str = "", lieu: str = "", address: str = "", zip: str = "", town: str = "", country_id: int = 0, phone: str = "", fax: str = "", accountancy_code: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a new warehouse.

    Args:
        ref: Reference.
        label: Label.
        status: Status.
        description: Description.
        lieu: Location.
        address: Street address.
        zip: Postal/ZIP code.
        town: City/town.
        country_id: Country ID.
        phone: Phone number.
        fax: Fax number.
        accountancy_code: Accounting code.
    """
    params = CreateWarehouseParam(ref=ref, label=label, status=status, description=description, lieu=lieu, address=address, zip=zip, town=town, country_id=country_id, phone=phone, fax=fax, accountancy_code=accountancy_code)
    return await get_client().warehouses_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def warehouses_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, status: Optional[int] = None, description: Optional[str] = None, lieu: Optional[str] = None, address: Optional[str] = None, zip: Optional[str] = None, town: Optional[str] = None, country_id: Optional[int] = None, phone: Optional[str] = None, fax: Optional[str] = None, accountancy_code: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing warehouse.

    Args:
        id: The unique ID of the resource.
        ref: Reference.
        label: Label.
        status: Status.
        description: Description.
        lieu: Location.
        address: Street address.
        zip: Postal/ZIP code.
        town: City/town.
        country_id: Country ID.
        phone: Phone number.
        fax: Fax number.
        accountancy_code: Accounting code.
    """
    payload = {k: v for k, v in {"ref": ref, "label": label, "status": status, "description": description, "lieu": lieu, "address": address, "zip": zip, "town": town, "country_id": country_id, "phone": phone, "fax": fax, "accountancy_code": accountancy_code}.items() if v is not None}
    return await get_client().warehouses_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def warehouses_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a warehouse by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().warehouses_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def warehouses_list_products(id: int, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List products in a warehouse.

    Args:
        id: The unique ID of the resource.
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().warehouses_list_products(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

# ============================================================
# Stock Movements
# ============================================================
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def stockmovements_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all stock movements.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().stockmovements_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def stockmovements_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single stock movement by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().stockmovements_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def stockmovements_create(product_id: int, warehouse_id: int, qty: float, type: int, batch: str = "", movementcode: str = "", label: str = "", price: float = 0.0, datem: str = "", sellBy: str = "", eatBy: str = "", origin_type: str = "", origin_id: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a new stock movement.

    Args:
        product_id: Product ID.
        warehouse_id: Warehouse ID.
        qty: Quantity.
        type: Type.
        batch: Batch number.
        movementcode: Movement code.
        label: Label.
        price: Unit price.
        datem: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        sellBy: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        eatBy: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        origin_type: Origin object type.
        origin_id: Origin object ID.
    """
    datem = _normalize_datetime(datem)
    eatBy = _normalize_datetime(eatBy)
    sellBy = _normalize_datetime(sellBy)
    params = CreateStockMovementParam(product_id=product_id, warehouse_id=warehouse_id, qty=qty, type=type, batch=batch, movementcode=movementcode, label=label, price=price, datem=datem, sellBy=sellBy, eatBy=eatBy, origin_type=origin_type, origin_id=origin_id)
    return await get_client().stockmovements_create(params.model_dump(exclude_unset=True), get_user_token())

# ============================================================
# Product Lots
# ============================================================
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def productlots_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all product lots/batches.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().productlots_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def productlots_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single product lot by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().productlots_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def productlots_create(ref: str, fk_product: int, batch: str, qty: float = 0.0, warehouse_id: int = 0, price: float = 0.0, datem: str = "", eatby: str = "", sellby: str = "", note_public: str = "", note_private: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a new product lot/batch.

    Args:
        ref: Reference.
        fk_product: Product ID.
        batch: Batch number.
        qty: Quantity.
        warehouse_id: Warehouse ID.
        price: Unit price.
        datem: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        eatby: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        sellby: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        note_public: Public note.
        note_private: Private note.
    """
    datem = _normalize_datetime(datem)
    eatby = _normalize_datetime(eatby)
    sellby = _normalize_datetime(sellby)
    params = CreateProductLotParam(ref=ref, fk_product=fk_product, batch=batch, qty=qty, warehouse_id=warehouse_id, price=price, datem=datem, eatby=eatby, sellby=sellby, note_public=note_public, note_private=note_private)
    return await get_client().productlots_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def productlots_update(id: int, ref: Optional[str] = None, fk_product: Optional[int] = None, batch: Optional[str] = None, qty: Optional[float] = None, warehouse_id: Optional[int] = None, price: Optional[float] = None, datem: Optional[str] = None, eatby: Optional[str] = None, sellby: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing product lot.

    Args:
        id: The unique ID of the resource.
        ref: Reference.
        fk_product: Product ID.
        batch: Batch number.
        qty: Quantity.
        warehouse_id: Warehouse ID.
        price: Unit price.
        datem: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        eatby: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        sellby: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        note_public: Public note.
        note_private: Private note.
    """
    payload = {k: v for k, v in {"ref": ref, "fk_product": fk_product, "batch": batch, "qty": qty, "warehouse_id": warehouse_id, "price": price, "datem": datem, "eatby": eatby, "sellby": sellby, "note_public": note_public, "note_private": note_private}.items() if v is not None}
    for key in ['datem', 'eatby', 'sellby']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().productlots_update(id, payload, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def productlots_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a product lot by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().productlots_delete(id, get_user_token())

# ============================================================
# Proposals
# ============================================================
@mcp.tool(tags={"basic", "dolibarr", "read"})
async def proposals_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all commercial proposals.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().proposals_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"basic", "dolibarr", "read"})
async def proposals_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single proposal by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().proposals_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"basic", "dolibarr", "write"})
async def proposals_create(socid: int, date: str, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, multicurrency_code: str = "", payment_terms: int = 0, delivery_date: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a new commercial proposal.

    Args:
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        multicurrency_code: Multi-currency code.
        payment_terms: Payment terms.
        delivery_date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
    """
    params = CreateProposalParam(
        socid=socid, date=_normalize_datetime(date), ref=ref,
        status=status, note_public=note_public,
        note_private=note_private, total_ht=total_ht,
        total_tva=total_tva, total_ttc=total_ttc,
        multicurrency_code=multicurrency_code,
        payment_terms=payment_terms,
        delivery_date=_normalize_datetime(delivery_date),
    )
    return await get_client().proposals_create(params.model_dump(), get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def proposals_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, multicurrency_code: Optional[str] = None, payment_terms: Optional[int] = None, delivery_date: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing proposal.

    Args:
        id: The unique ID of the resource.
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        multicurrency_code: Multi-currency code.
        payment_terms: Payment terms.
        delivery_date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
    """
    payload = {k: v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code, "payment_terms": payment_terms, "delivery_date": delivery_date}.items() if v is not None}
    for key in ['date', 'delivery_date']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().proposals_update(id, payload, get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def proposals_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a proposal by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().proposals_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def proposals_get_lines(id: int, sqlfilters: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get lines for a proposal.

    Args:
        id: The unique ID of the resource.
        sqlfilters: Dolibarr SQL filter syntax.
    """
    data = await get_client().proposals_get_lines(id, get_user_token(), sqlfilters=sqlfilters)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def proposals_create_line(id: int, desc: str, qty: float, subprice: float, product_id: int = 0, tva_tx: float = 0.0, remise_percent: float = 0.0, remise: float = 0.0, price_base_type: str = "HT", date_start: str = "", date_end: str = "", product_type: int = 0, rang: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add a line to a proposal.

    Args:
        id: The unique ID of the resource.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        remise_percent: Discount percentage.
        remise: Discount amount.
        price_base_type: Price base type (HT or TTC).
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        product_type: Product type (0=product, 1=service).
        rang: Line position.
    """
    date_end = _normalize_datetime(date_end)
    date_start = _normalize_datetime(date_start)
    params = CreateProposalLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, remise_percent=remise_percent, remise=remise, price_base_type=price_base_type, date_start=date_start, date_end=date_end, product_type=product_type, rang=rang)
    return await get_client().proposals_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def proposals_update_line(id: int, lineid: int, desc: Optional[str] = None, qty: Optional[float] = None, subprice: Optional[float] = None, product_id: Optional[int] = None, tva_tx: Optional[float] = None, remise_percent: Optional[float] = None, remise: Optional[float] = None, price_base_type: Optional[str] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, product_type: Optional[int] = None, rang: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a line in a proposal.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        remise_percent: Discount percentage.
        remise: Discount amount.
        price_base_type: Price base type (HT or TTC).
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        product_type: Product type (0=product, 1=service).
        rang: Line position.
    """
    payload = {k: v for k, v in {"desc": desc, "qty": qty, "subprice": subprice, "product_id": product_id, "tva_tx": tva_tx, "remise_percent": remise_percent, "remise": remise, "price_base_type": price_base_type, "date_start": date_start, "date_end": date_end, "product_type": product_type, "rang": rang}.items() if v is not None}
    for key in ['date_end', 'date_start']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().proposals_update_line(id, lineid, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def proposals_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a line from a proposal.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
    """
    return await get_client().proposals_delete_line(id, lineid, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def proposals_settodraft(id: int, ctx: Context = None) -> dict[str, Any]:
    """Set a proposal to draft status.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().proposals_settodraft(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def proposals_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a proposal.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().proposals_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def proposals_close(id: int, status: int, note_private: str = "", note_public: str = "", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Close a proposal.

    Args:
        id: The unique ID of the resource.
        status: Status.
        note_private: Private note.
        note_public: Public note.
        notrigger: Disable triggers flag.
    """
    return await get_client().proposals_close(id, get_user_token(), status=status, note_private=note_private, note_public=note_public, notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def proposals_setinvoiced(id: int, ctx: Context = None) -> dict[str, Any]:
    """Set a proposal as invoiced.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().proposals_setinvoiced(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def proposals_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get contacts linked to a proposal.

    Args:
        id: The unique ID of the resource.
        type: Type.
    """
    data = await get_client().proposals_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def proposals_add_contact(id: int, contactid: int, type: str, source: str = "external", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add a contact to a proposal.

    Args:
        id: The unique ID of the resource.
        contactid: Contact ID.
        type: Type.
        source: Source.
        notrigger: Disable triggers flag.
    """
    return await get_client().proposals_add_contact(id, contactid, type, get_user_token(), source=source, notrigger=notrigger)

# ============================================================
# Orders
# ============================================================
@mcp.tool(tags={"basic", "dolibarr", "read"})
async def orders_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all customer orders.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().orders_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"basic", "dolibarr", "read"})
async def orders_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single order by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().orders_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"basic", "dolibarr", "write"})
async def orders_create(socid: int, date: str, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, multicurrency_code: str = "", payment_terms: int = 0, delivery_date: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a new customer order.

    Args:
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        multicurrency_code: Multi-currency code.
        payment_terms: Payment terms.
        delivery_date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
    """
    params = CreateOrderParam(
        socid=socid, date=_normalize_datetime(date), ref=ref,
        status=status, note_public=note_public,
        note_private=note_private, total_ht=total_ht,
        total_tva=total_tva, total_ttc=total_ttc,
        multicurrency_code=multicurrency_code,
        payment_terms=payment_terms,
        delivery_date=_normalize_datetime(delivery_date),
    )
    return await get_client().orders_create(params.model_dump(), get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def orders_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, multicurrency_code: Optional[str] = None, payment_terms: Optional[int] = None, delivery_date: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing order.

    Args:
        id: The unique ID of the resource.
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        multicurrency_code: Multi-currency code.
        payment_terms: Payment terms.
        delivery_date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
    """
    payload = {k: v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code, "payment_terms": payment_terms, "delivery_date": delivery_date}.items() if v is not None}
    for key in ['date', 'delivery_date']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().orders_update(id, payload, get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def orders_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an order by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().orders_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def orders_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get lines for an order.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().orders_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def orders_get_line(id: int, lineid: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single line from an order.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().orders_get_line(id, lineid, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def orders_create_line(id: int, desc: str, qty: float, subprice: float, product_id: int = 0, tva_tx: float = 0.0, remise_percent: float = 0.0, price_base_type: str = "HT", date_start: str = "", date_end: str = "", product_type: int = 0, rang: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add a line to an order.

    Args:
        id: The unique ID of the resource.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        remise_percent: Discount percentage.
        price_base_type: Price base type (HT or TTC).
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        product_type: Product type (0=product, 1=service).
        rang: Line position.
    """
    date_end = _normalize_datetime(date_end)
    date_start = _normalize_datetime(date_start)
    params = CreateOrderLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, remise_percent=remise_percent, price_base_type=price_base_type, date_start=date_start, date_end=date_end, product_type=product_type, rang=rang)
    return await get_client().orders_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def orders_update_line(id: int, lineid: int, desc: Optional[str] = None, qty: Optional[float] = None, subprice: Optional[float] = None, product_id: Optional[int] = None, tva_tx: Optional[float] = None, remise_percent: Optional[float] = None, price_base_type: Optional[str] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, product_type: Optional[int] = None, rang: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a line in an order.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        remise_percent: Discount percentage.
        price_base_type: Price base type (HT or TTC).
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        product_type: Product type (0=product, 1=service).
        rang: Line position.
    """
    payload = {k: v for k, v in {"desc": desc, "qty": qty, "subprice": subprice, "product_id": product_id, "tva_tx": tva_tx, "remise_percent": remise_percent, "price_base_type": price_base_type, "date_start": date_start, "date_end": date_end, "product_type": product_type, "rang": rang}.items() if v is not None}
    for key in ['date_end', 'date_start']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().orders_update_line(id, lineid, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def orders_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a line from an order.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
    """
    return await get_client().orders_delete_line(id, lineid, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def orders_settodraft(id: int, idwarehouse: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Set an order to draft status.

    Args:
        id: The unique ID of the resource.
        idwarehouse: Warehouse ID.
    """
    return await get_client().orders_settodraft(id, get_user_token(), idwarehouse=idwarehouse)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def orders_validate(id: int, idwarehouse: int = 0, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate an order.

    Args:
        id: The unique ID of the resource.
        idwarehouse: Warehouse ID.
        notrigger: Disable triggers flag.
    """
    return await get_client().orders_validate(id, get_user_token(), idwarehouse=idwarehouse, notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def orders_close(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Close an order.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().orders_close(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def orders_reopen(id: int, ctx: Context = None) -> dict[str, Any]:
    """Reopen a closed order.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().orders_reopen(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def orders_setinvoiced(id: int, ctx: Context = None) -> dict[str, Any]:
    """Set an order as invoiced.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().orders_setinvoiced(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def orders_create_from_proposal(proposalid: int, ctx: Context = None) -> dict[str, Any]:
    """Create an order from a proposal.

    Args:
        proposalid: Proposal ID.
    """
    return await get_client().orders_create_from_proposal(proposalid, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def orders_get_shipments(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get shipments for an order.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().orders_get_shipments(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def orders_create_shipment(id: int, warehouse_id: int, ctx: Context = None) -> dict[str, Any]:
    """Create a shipment from an order.

    Args:
        id: The unique ID of the resource.
        warehouse_id: Warehouse ID.
    """
    return await get_client().orders_create_shipment(id, warehouse_id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def orders_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get contacts linked to an order.

    Args:
        id: The unique ID of the resource.
        type: Type.
    """
    data = await get_client().orders_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

# ============================================================
# Invoices
# ============================================================
@mcp.tool(tags={"basic", "dolibarr", "read"})
async def invoices_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", status: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all customer invoices.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        status: Status.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().invoices_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, status=status, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"basic", "dolibarr", "read"})
async def invoices_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single invoice by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().invoices_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"basic", "dolibarr", "write"})
async def invoices_create(socid: int, date: str, type: int, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, multicurrency_code: str = "", payment_terms: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a new customer invoice.

    Args:
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        type: Type.
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        multicurrency_code: Multi-currency code.
        payment_terms: Payment terms.
    """
    params = CreateInvoiceParam(
        socid=socid, date=_normalize_datetime(date), type=type, ref=ref,
        status=status, note_public=note_public,
        note_private=note_private, total_ht=total_ht,
        total_tva=total_tva, total_ttc=total_ttc,
        multicurrency_code=multicurrency_code,
        payment_terms=payment_terms,
    )
    return await get_client().invoices_create(params.model_dump(), get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def invoices_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, type: Optional[int] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, multicurrency_code: Optional[str] = None, payment_terms: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing invoice.

    Args:
        id: The unique ID of the resource.
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        type: Type.
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        multicurrency_code: Multi-currency code.
        payment_terms: Payment terms.
    """
    payload = {k: v for k, v in {"socid": socid, "date": date, "type": type, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code, "payment_terms": payment_terms}.items() if v is not None}
    for key in ['date']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().invoices_update(id, payload, get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def invoices_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an invoice by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().invoices_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def invoices_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get lines for an invoice.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().invoices_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_create_line(id: int, desc: str, qty: float, subprice: float, product_id: int = 0, tva_tx: float = 0.0, remise_percent: float = 0.0, price_base_type: str = "HT", date_start: str = "", date_end: str = "", product_type: int = 0, rang: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add a line to an invoice.

    Args:
        id: The unique ID of the resource.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        remise_percent: Discount percentage.
        price_base_type: Price base type (HT or TTC).
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        product_type: Product type (0=product, 1=service).
        rang: Line position.
    """
    date_end = _normalize_datetime(date_end)
    date_start = _normalize_datetime(date_start)
    params = CreateInvoiceLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, remise_percent=remise_percent, price_base_type=price_base_type, date_start=date_start, date_end=date_end, product_type=product_type, rang=rang)
    return await get_client().invoices_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_update_line(id: int, lineid: int, desc: Optional[str] = None, qty: Optional[float] = None, subprice: Optional[float] = None, product_id: Optional[int] = None, tva_tx: Optional[float] = None, remise_percent: Optional[float] = None, price_base_type: Optional[str] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, product_type: Optional[int] = None, rang: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a line in an invoice.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        remise_percent: Discount percentage.
        price_base_type: Price base type (HT or TTC).
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        product_type: Product type (0=product, 1=service).
        rang: Line position.
    """
    payload = {k: v for k, v in {"desc": desc, "qty": qty, "subprice": subprice, "product_id": product_id, "tva_tx": tva_tx, "remise_percent": remise_percent, "price_base_type": price_base_type, "date_start": date_start, "date_end": date_end, "product_type": product_type, "rang": rang}.items() if v is not None}
    for key in ['date_end', 'date_start']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().invoices_update_line(id, lineid, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a line from an invoice.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
    """
    return await get_client().invoices_delete_line(id, lineid, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_create_from_order(orderid: int, ctx: Context = None) -> dict[str, Any]:
    """Create an invoice from an order.

    Args:
        orderid: Order ID.
    """
    return await get_client().invoices_create_from_order(orderid, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_settodraft(id: int, ctx: Context = None) -> dict[str, Any]:
    """Set an invoice to draft status.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().invoices_settodraft(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_validate(id: int, force_number: int = 0, idwarehouse: int = 0, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate an invoice.

    Args:
        id: The unique ID of the resource.
        force_number: Force document number flag.
        idwarehouse: Warehouse ID.
        notrigger: Disable triggers flag.
    """
    return await get_client().invoices_validate(id, get_user_token(), force_number=force_number, idwarehouse=idwarehouse, notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_settopaid(id: int, close_code: str = "", close_note: str = "", ctx: Context = None) -> dict[str, Any]:
    """Set an invoice as paid.

    Args:
        id: The unique ID of the resource.
        close_code: Close code.
        close_note: Close note.
    """
    return await get_client().invoices_settopaid(id, get_user_token(), close_code=close_code, close_note=close_note)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_settounpaid(id: int, ctx: Context = None) -> dict[str, Any]:
    """Set an invoice as unpaid.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().invoices_settounpaid(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def invoices_get_payments(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get payments for an invoice.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().invoices_get_payments(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_add_payment(id: int, datepaye: str, paymentid: int, accountid: int, closepaidinvoices: str = "no", num_payment: str = "", comment: str = "", amount: float = 0.0, chqemetteur: str = "", chqbank: str = "", ctx: Context = None) -> dict[str, Any]:
    """Add a payment to an invoice.

    Args:
        id: The unique ID of the resource.
        datepaye: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        paymentid: Payment type ID.
        accountid: Account ID.
        closepaidinvoices: Close paid invoices flag ("yes" or "no").
        num_payment: Payment number.
        comment: Comment.
        amount: Amount to pay.
        chqemetteur: Check issuer.
        chqbank: Check bank.
    """
    datepaye = _normalize_datetime(datepaye)
    params = CreateInvoicePaymentParam(datepaye=datepaye, paymentid=paymentid, accountid=accountid, closepaidinvoices=closepaidinvoices, num_payment=num_payment, comment=comment, amount=amount, chqemetteur=chqemetteur, chqbank=chqbank)
    return await get_client().invoices_add_payment(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def invoices_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get contacts linked to an invoice.

    Args:
        id: The unique ID of the resource.
        type: Type.
    """
    data = await get_client().invoices_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_add_contact(id: int, fk_socpeople: int, type_contact: str, source: str = "external", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add a contact to an invoice.

    Args:
        id: The unique ID of the resource.
        fk_socpeople: Contact ID.
        type_contact: Contact type.
        source: Source.
        notrigger: Disable triggers flag.
    """
    params = CreateInvoiceContactParam(fk_socpeople=fk_socpeople, type_contact=type_contact, source=source, notrigger=notrigger)
    return await get_client().invoices_add_contact(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_delete_contact(id: int, contactid: int, type: str, ctx: Context = None) -> dict[str, Any]:
    """Delete a contact from an invoice.

    Args:
        id: The unique ID of the resource.
        contactid: Contact ID.
        type: Type.
    """
    return await get_client().invoices_delete_contact(id, contactid, type, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def invoices_get_discount(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get available discount for an invoice.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().invoices_get_discount(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_use_discount(id: int, discountid: int, ctx: Context = None) -> dict[str, Any]:
    """Apply a discount to an invoice.

    Args:
        id: The unique ID of the resource.
        discountid: Discount ID.
    """
    return await get_client().invoices_use_discount(id, discountid, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def invoices_mark_as_credit_available(id: int, ctx: Context = None) -> dict[str, Any]:
    """Mark a credit note as available to be used as a discount.

    Args:
        id: The unique ID of the validated credit note.
    """
    return await get_client().invoices_mark_as_credit_available(id, get_user_token())

# ============================================================
# Payments
# ============================================================
@mcp.tool(tags={"basic", "dolibarr", "read"})
async def payments_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all customer payments.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().payments_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"basic", "dolibarr", "read"})
async def payments_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single payment by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().payments_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"basic", "dolibarr", "write"})
async def payments_create(datepaye: str, paymentid: int, amount: float, accountid: int, closepaidinvoices: str = "no", socid: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a new payment.

    Args:
        datepaye: Payment date (use ISO 8601 format, required).
        paymentid: Payment type ID.
        amount: Amount.
        accountid: Bank account ID.
        closepaidinvoices: Close paid invoices (yes/no).
        socid: Thirdparty ID for the placeholder invoice.
    """
    pay_inv = await get_client().invoices_create({"socid": socid, "date": int(_to_timestamp(datepaye)), "type": 0}, get_user_token())
    pay_inv_id = pay_inv.get("id") if isinstance(pay_inv, dict) else int(pay_inv)
    line_data = {"desc": "Payment line", "qty": 1, "subprice": amount, "tva_tx": 0.0, "price_base_type": "HT"}
    await get_client().invoices_create_line(pay_inv_id, line_data, get_user_token())
    payload = CreateInvoicePaymentParam(datepaye=datepaye, paymentid=paymentid, accountid=accountid, closepaidinvoices=closepaidinvoices, amount=amount).model_dump(exclude_unset=True)
    payload["datepaye"] = _to_timestamp(str(payload["datepaye"])) if "T" in str(payload["datepaye"]) or " " in str(payload["datepaye"]) else int(str(payload["datepaye"]))
    result = await get_client().invoices_add_payment(pay_inv_id, payload, get_user_token())
    pay_id = result.get("id") if isinstance(result, dict) else result
    return {"id": pay_id, "_placeholder_invoice_id": pay_inv_id}

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def payments_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a payment by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().payments_delete(id, get_user_token())

# ============================================================
# Bank Accounts
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def bankaccounts_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, category: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all bank accounts.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        category: Category ID filter.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().bankaccounts_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, category=category, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def bankaccounts_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single bank account by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().bankaccounts_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def bankaccounts_create(ref: str, label: str, type: int, currency_code: str, account_number: str = "", country_id: int = 0, bank: str = "", code_banque: str = "", code_guichet: str = "", cle_rib: str = "", bic: str = "", iban: str = "", domiciliation: str = "", state_id: int = 0, opening_balance: float = 0.0, min_balance: float = 0.0, proprio: str = "", note_public: str = "", note_private: str = "", status: int = 1, ctx: Context = None) -> dict[str, Any]:
    """Create a new bank account.

    Args:
        ref: Reference.
        label: Label.
        type: Type.
        currency_code: Currency Code.
        account_number: Account Number.
        country_id: Country ID.
        bank: Bank.
        code_banque: Bank code.
        code_guichet: Branch code.
        cle_rib: RIB key.
        bic: BIC code.
        iban: IBAN.
        domiciliation: Bank branch address.
        state_id: State/region ID.
        opening_balance: Opening balance.
        min_balance: Minimum balance.
        proprio: Owner.
        note_public: Public note.
        note_private: Private note.
        status: Status.
    """
    params = CreateBankAccountParam(ref=ref, label=label, type=type, currency_code=currency_code, account_number=account_number, country_id=country_id, bank=bank, code_banque=code_banque, code_guichet=code_guichet, cle_rib=cle_rib, bic=bic, iban=iban, domiciliation=domiciliation, state_id=state_id, opening_balance=opening_balance, min_balance=min_balance, proprio=proprio, note_public=note_public, note_private=note_private, status=status)
    return await get_client().bankaccounts_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def bankaccounts_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, type: Optional[int] = None, currency_code: Optional[str] = None, account_number: Optional[str] = None, bank: Optional[str] = None, code_banque: Optional[str] = None, code_guichet: Optional[str] = None, cle_rib: Optional[str] = None, bic: Optional[str] = None, iban: Optional[str] = None, domiciliation: Optional[str] = None, state_id: Optional[int] = None, opening_balance: Optional[float] = None, min_balance: Optional[float] = None, proprio: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, status: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing bank account.

    Args:
        id: The unique ID of the resource.
        ref: Reference.
        label: Label.
        type: Type.
        currency_code: Currency Code.
        account_number: Account Number.
        bank: Bank.
        code_banque: Bank code.
        code_guichet: Branch code.
        cle_rib: RIB key.
        bic: BIC code.
        iban: IBAN.
        domiciliation: Bank branch address.
        state_id: State/region ID.
        opening_balance: Opening balance.
        min_balance: Minimum balance.
        proprio: Owner.
        note_public: Public note.
        note_private: Private note.
        status: Status.
    """
    payload = {k: v for k, v in {"ref": ref, "label": label, "type": type, "currency_code": currency_code, "account_number": account_number, "bank": bank, "code_banque": code_banque, "code_guichet": code_guichet, "cle_rib": cle_rib, "bic": bic, "iban": iban, "domiciliation": domiciliation, "state_id": state_id, "opening_balance": opening_balance, "min_balance": min_balance, "proprio": proprio, "note_public": note_public, "note_private": note_private, "status": status}.items() if v is not None}
    return await get_client().bankaccounts_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def bankaccounts_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a bank account by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().bankaccounts_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def bankaccounts_transfer(bankaccount_from_id: int, bankaccount_to_id: int, date: str, description: str, amount: float, amount_to: float = 0.0, cheque_number: str = "", ctx: Context = None) -> dict[str, Any]:
    """Bankaccounts Transfer.

    Args:
        bankaccount_from_id: Source bank account ID.
        bankaccount_to_id: Destination bank account ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        description: Description.
        amount: Amount.
        amount_to: Destination amount.
        cheque_number: Check number.
    """
    params = CreateBankAccountTransferParam(bankaccount_from_id=bankaccount_from_id, bankaccount_to_id=bankaccount_to_id, date=date, description=description, amount=amount, amount_to=amount_to, cheque_number=cheque_number).model_dump(exclude_unset=True)
    params["date"] = _to_timestamp(params["date"]) if "T" in str(params["date"]) or " " in str(params["date"]) else int(str(params["date"]))
    return await get_client().bankaccounts_transfer(params, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def bankaccounts_get_lines(id: int, sqlfilters: str = "", ctx: Context = None) -> dict[str, Any]:
    """Bankaccounts Get Lines.

    Args:
        id: The unique ID of the resource.
        sqlfilters: Dolibarr SQL filter syntax.
    """
    data = await get_client().bankaccounts_get_lines(id, get_user_token(), sqlfilters=sqlfilters)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def bankaccounts_create_line(id: int, date: str, type: str, label: str, amount: float, category: int = 0, cheque_number: str = "", cheque_writer: str = "", cheque_bank: str = "", accountancycode: str = "", datev: str = "", num_releve: str = "", ctx: Context = None) -> dict[str, Any]:
    """Add a line to a bank account.

    Args:
        id: The unique ID of the resource.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        type: Type.
        label: Label.
        amount: Amount.
        category: Category ID filter.
        cheque_number: Check number.
        cheque_writer: Check writer.
        cheque_bank: Cheque Bank.
        accountancycode: Accounting code.
        datev: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        num_releve: Statement number.
    """
    params = CreateBankAccountLineParam(date=date, type=type, label=label, amount=amount, category=category, cheque_number=cheque_number, cheque_writer=cheque_writer, cheque_bank=cheque_bank, accountancycode=accountancycode, datev=datev, num_releve=num_releve)
    return await get_client().bankaccounts_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def bankaccounts_get_line(line_id: int, ctx: Context = None) -> dict[str, Any]:
    """Bankaccounts Get Line.

    Args:
        line_id: Line ID.
    """
    return await get_client().bankaccounts_get_line(line_id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def bankaccounts_update_line(id: int, line_id: int, label: str, ctx: Context = None) -> dict[str, Any]:
    """Update a line in a bank account.

    Args:
        id: The unique ID of the resource.
        line_id: Line ID.
        label: Label.
    """
    result = await get_client().bankaccounts_update_line(id, line_id, label, get_user_token())
    return {"id": result}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def bankaccounts_delete_line(id: int, line_id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a line from a bank account.

    Args:
        id: The unique ID of the resource.
        line_id: Line ID.
    """
    return await get_client().bankaccounts_delete_line(id, line_id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def bankaccounts_get_balance(id: int, ctx: Context = None) -> dict[str, Any]:
    """Bankaccounts Get Balance.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().bankaccounts_get_balance(id, get_user_token())

# ============================================================
# Supplier Orders
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def supplier_orders_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", product_ids: str = "", status: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders List.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        product_ids: Comma-separated product IDs.
        status: Status.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().supplier_orders_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, product_ids=product_ids, status=status, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def supplier_orders_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Get.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().supplier_orders_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_orders_create(socid: int, date: str, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, multicurrency_code: str = "", ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Create.

    Args:
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        multicurrency_code: Multi-currency code.
    """
    params = CreateSupplierOrderParam(
        socid=socid, date=_normalize_datetime(date), ref=ref,
        status=status, note_public=note_public,
        note_private=note_private, total_ht=total_ht,
        total_tva=total_tva, total_ttc=total_ttc,
        multicurrency_code=multicurrency_code,
    )
    return await get_client().supplier_orders_create(params.model_dump(), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_orders_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, multicurrency_code: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Update.

    Args:
        id: The unique ID of the resource.
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        multicurrency_code: Multi-currency code.
    """
    payload = {k: v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code}.items() if v is not None}
    for key in ['date']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().supplier_orders_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_orders_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Delete.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().supplier_orders_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_orders_create_line(id: int, desc: str, qty: float, subprice: float, product_id: int = 0, tva_tx: float = 0.0, remise_percent: float = 0.0, price_base_type: str = "HT", date_start: str = "", date_end: str = "", product_type: int = 0, rang: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Create Line.

    Args:
        id: The unique ID of the resource.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        remise_percent: Discount percentage.
        price_base_type: Price base type (HT or TTC).
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        product_type: Product type (0=product, 1=service).
        rang: Line position.
    """
    date_end = _normalize_datetime(date_end)
    date_start = _normalize_datetime(date_start)
    params = CreateSupplierOrderLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, remise_percent=remise_percent, price_base_type=price_base_type, date_start=date_start, date_end=date_end, product_type=product_type, rang=rang)
    return await get_client().supplier_orders_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def supplier_orders_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Get Contacts.

    Args:
        id: The unique ID of the resource.
        type: Type.
    """
    data = await get_client().supplier_orders_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_orders_add_contact(id: int, contactid: int, type: str, source: str, ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Add Contact.

    Args:
        id: The unique ID of the resource.
        contactid: Contact ID.
        type: Type.
        source: Source.
    """
    return await get_client().supplier_orders_add_contact(id, contactid, type, source, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_orders_delete_contact(id: int, contactid: int, type: str, source: str, ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Delete Contact.

    Args:
        id: The unique ID of the resource.
        contactid: Contact ID.
        type: Type.
        source: Source.
    """
    return await get_client().supplier_orders_delete_contact(id, contactid, type, source, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_orders_validate(id: int, idwarehouse: int = 0, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Validate.

    Args:
        id: The unique ID of the resource.
        idwarehouse: Warehouse ID.
        notrigger: Disable triggers flag.
    """
    return await get_client().supplier_orders_validate(id, get_user_token(), idwarehouse=idwarehouse, notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_orders_approve(id: int, idwarehouse: int = 0, secondlevel: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Approve.

    Args:
        id: The unique ID of the resource.
        idwarehouse: Warehouse ID.
        secondlevel: Second approval level flag.
    """
    return await get_client().supplier_orders_approve(id, get_user_token(), idwarehouse=idwarehouse, secondlevel=secondlevel)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_orders_receive(id: int, closeopenorder: int = 0, comment: str = "", lines: list[ReceiveLine] = None, ctx: Context = None) -> dict[str, Any]:
    """Supplier Orders Receive.

    Args:
        id: The unique ID of the resource.
        closeopenorder: Close open order flag.
        comment: Comment.
        lines: List of line objects with id, qty, warehouse, fk_product.
    """
    return await get_client().supplier_orders_receive(id, get_user_token(), closeopenorder=closeopenorder, comment=comment, lines=lines or [])

# ============================================================
# Supplier Invoices
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def supplier_invoices_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", status: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices List.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        status: Status.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().supplier_invoices_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, status=status, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def supplier_invoices_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Get.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().supplier_invoices_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_invoices_create(socid: int, date: str, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, multicurrency_code: str = "", ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Create.

    Args:
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        multicurrency_code: Multi-currency code.
    """
    params = CreateSupplierInvoiceParam(
        socid=socid, date=_normalize_datetime(date), ref=ref,
        status=status, note_public=note_public,
        note_private=note_private, total_ht=total_ht,
        total_tva=total_tva, total_ttc=total_ttc,
        multicurrency_code=multicurrency_code,
    )
    return await get_client().supplier_invoices_create(params.model_dump(), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_invoices_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, multicurrency_code: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Update.

    Args:
        id: The unique ID of the resource.
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        multicurrency_code: Multi-currency code.
    """
    payload = {k: v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code}.items() if v is not None}
    for key in ['date']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().supplier_invoices_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_invoices_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Delete.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().supplier_invoices_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def supplier_invoices_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Get Lines.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().supplier_invoices_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_invoices_create_line(id: int, desc: str, qty: float, subprice: float, product_id: int = 0, tva_tx: float = 0.0, remise_percent: float = 0.0, price_base_type: str = "HT", ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Create Line.

    Args:
        id: The unique ID of the resource.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        remise_percent: Discount percentage.
        price_base_type: Price base type (HT or TTC).
    """
    params = CreateSupplierInvoiceLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, remise_percent=remise_percent, price_base_type=price_base_type)
    return await get_client().supplier_invoices_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_invoices_update_line(id: int, lineid: int, desc: Optional[str] = None, qty: Optional[float] = None, subprice: Optional[float] = None, product_id: Optional[int] = None, tva_tx: Optional[float] = None, remise_percent: Optional[float] = None, price_base_type: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Update Line.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        remise_percent: Discount percentage.
        price_base_type: Price base type (HT or TTC).
    """
    payload = {k: v for k, v in {"desc": desc, "qty": qty, "subprice": subprice, "product_id": product_id, "tva_tx": tva_tx, "remise_percent": remise_percent, "price_base_type": price_base_type}.items() if v is not None}
    return await get_client().supplier_invoices_update_line(id, lineid, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_invoices_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Delete Line.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
    """
    return await get_client().supplier_invoices_delete_line(id, lineid, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_invoices_validate(id: int, idwarehouse: int = 0, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Validate.

    Args:
        id: The unique ID of the resource.
        idwarehouse: Warehouse ID.
        notrigger: Disable triggers flag.
    """
    return await get_client().supplier_invoices_validate(id, get_user_token(), idwarehouse=idwarehouse, notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_invoices_settopaid(id: int, close_code: str = "", close_note: str = "", ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Settopaid.

    Args:
        id: The unique ID of the resource.
        close_code: Close code.
        close_note: Close note.
    """
    return await get_client().supplier_invoices_settopaid(id, get_user_token(), close_code=close_code, close_note=close_note)

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def supplier_invoices_get_payments(id: int, ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Get Payments.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().supplier_invoices_get_payments(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_invoices_add_payment(id: int, datepaye: str, payment_mode_id: int, accountid: int, closepaidinvoices: str = "no", num_payment: str = "", comment: str = "", amount: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Supplier Invoices Add Payment.

    Args:
        id: The unique ID of the resource.
        datepaye: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        payment_mode_id: Payment mode ID.
        accountid: Account ID.
        closepaidinvoices: Close paid invoices flag.
        num_payment: Payment number.
        comment: Comment.
        amount: Amount.
    """
    params = CreateSupplierInvoicePaymentParam(datepaye=datepaye, payment_mode_id=payment_mode_id, accountid=accountid, closepaidinvoices=closepaidinvoices, num_payment=num_payment, comment=comment, amount=amount).model_dump(exclude_unset=True)
    params["datepaye"] = _to_timestamp(str(params["datepaye"])) if "T" in str(params["datepaye"]) or " " in str(params["datepaye"]) else int(str(params["datepaye"]))
    return await get_client().supplier_invoices_add_payment(id, params, get_user_token())

# ============================================================
# Supplier Proposals
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def supplier_proposals_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Supplier Proposals List.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().supplier_proposals_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def supplier_proposals_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Supplier Proposals Get.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().supplier_proposals_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_proposals_create(socid: int, date: str, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Supplier Proposals Create.

    Args:
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
    """
    params = CreateSupplierProposalParam(
        socid=socid, date=_normalize_datetime(date), ref=ref,
        status=status, note_public=note_public,
        note_private=note_private, total_ht=total_ht,
        total_tva=total_tva, total_ttc=total_ttc,
    )
    return await get_client().supplier_proposals_create(params.model_dump(), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_proposals_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, ctx: Context = None) -> dict[str, Any]:
    """Supplier Proposals Update.

    Args:
        id: The unique ID of the resource.
        socid: Third party ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
    """
    payload = {k: v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc}.items() if v is not None}
    for key in ['date']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().supplier_proposals_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def supplier_proposals_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Supplier Proposals Delete.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().supplier_proposals_delete(id, get_user_token())

# ============================================================
# Contracts
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def contracts_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all contracts.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().contracts_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def contracts_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single contract by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().contracts_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def contracts_create(socid: int, ref: str, date_contrat: str, commercial_signature_id: int = 0, commercial_suivi_id: int = 0, status: int = 0, note_public: str = "", note_private: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a new contract.

    Args:
        socid: Third party ID.
        ref: Reference.
        date_contrat: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        commercial_signature_id: Commercial signature contact ID.
        commercial_suivi_id: Commercial follow-up contact ID.
        status: Status.
        note_public: Public note.
        note_private: Private note.
    """
    date_contrat = _normalize_datetime(date_contrat)
    params = CreateContractParam(socid=socid, ref=ref, date_contrat=date_contrat, commercial_signature_id=commercial_signature_id, commercial_suivi_id=commercial_suivi_id, status=status, note_public=note_public, note_private=note_private)
    return await get_client().contracts_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def contracts_update(id: int, socid: Optional[int] = None, ref: Optional[str] = None, date_contrat: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing contract.

    Args:
        id: The unique ID of the resource.
        socid: Third party ID.
        ref: Reference.
        date_contrat: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        status: Status.
        note_public: Public note.
        note_private: Private note.
    """
    payload = {k: v for k, v in {"socid": socid, "ref": ref, "date_contrat": date_contrat, "status": status, "note_public": note_public, "note_private": note_private}.items() if v is not None}
    for key in ['date_contrat']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().contracts_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def contracts_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a contract by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().contracts_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def contracts_get_lines(id: int, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get lines for a contract.

    Args:
        id: The unique ID of the resource.
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().contracts_get_lines(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def contracts_create_line(id: int, desc: str = "", qty: float = 0.0, subprice: float = 0.0, product_id: int = 0, tva_tx: float = 0.0, date_start: str = "", date_end: str = "", remise_percent: float = 0.0, price_base_type: str = "HT", ctx: Context = None) -> dict[str, Any]:
    """Add a line to a contract.

    Args:
        id: The unique ID of the resource.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        remise_percent: Discount percentage.
        price_base_type: Price base type (HT or TTC).
    """
    date_end = _normalize_datetime(date_end)
    date_start = _normalize_datetime(date_start)
    params = CreateContractLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, date_start=date_start, date_end=date_end, remise_percent=remise_percent, price_base_type=price_base_type)
    return await get_client().contracts_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def contracts_update_line(id: int, lineid: int, desc: Optional[str] = None, qty: Optional[float] = None, subprice: Optional[float] = None, product_id: Optional[int] = None, tva_tx: Optional[float] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, remise_percent: Optional[float] = None, price_base_type: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Contracts Update Line.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
        desc: Desc.
        qty: Quantity.
        subprice: Unit price.
        product_id: Product ID.
        tva_tx: VAT rate.
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        remise_percent: Discount percentage.
        price_base_type: Price base type (HT or TTC).
    """
    payload = {k: v for k, v in {"desc": desc, "qty": qty, "subprice": subprice, "product_id": product_id, "tva_tx": tva_tx, "date_start": date_start, "date_end": date_end, "remise_percent": remise_percent, "price_base_type": price_base_type}.items() if v is not None}
    for key in ['date_end', 'date_start']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().contracts_update_line(id, lineid, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def contracts_activate_line(id: int, lineid: int, datestart: str, dateend: str = "", comment: str = "", ctx: Context = None) -> dict[str, Any]:
    """Contracts Activate Line.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
        datestart: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        dateend: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        comment: Comment.
    """
    params = CreateContractActivateLineParam(datestart=datestart, dateend=dateend, comment=comment).model_dump(exclude_unset=True)
    params["datestart"] = _to_timestamp(str(params["datestart"])) if "T" in str(params["datestart"]) or " " in str(params["datestart"]) else int(str(params["datestart"]))
    if params.get("dateend"):
        params["dateend"] = _to_timestamp(str(params["dateend"])) if "T" in str(params["dateend"]) or " " in str(params["dateend"]) else int(str(params["dateend"]))
    return await get_client().contracts_activate_line(id, lineid, params, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def contracts_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Contracts Delete Line.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
    """
    return await get_client().contracts_delete_line(id, lineid, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def contracts_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a contract.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().contracts_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def contracts_close(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Contracts Close.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().contracts_close(id, get_user_token(), notrigger=notrigger)

# ============================================================
# BOMs
# ============================================================
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def boms_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all bills of materials.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().boms_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def boms_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single BOM by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().boms_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def boms_create(ref: str, label: str, fk_product: int, qty: float, bomtype: int = 0, status: int = 0, description: str = "", note_public: str = "", note_private: str = "", duration: float = 0.0, efficiency: float = 0.0, warehouse_id: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a new bill of materials.

    Args:
        ref: Reference.
        label: Label.
        fk_product: Product ID.
        qty: Quantity.
        bomtype: BOM type (0=manufacturing, 1=...).
        status: Status.
        description: Description.
        note_public: Public note.
        note_private: Private note.
        duration: Duration.
        efficiency: Efficiency rate.
        warehouse_id: Warehouse ID.
    """
    params = CreateBomParam(ref=ref, label=label, fk_product=fk_product, qty=qty, bomtype=bomtype, status=status, description=description, note_public=note_public, note_private=note_private, duration=duration, efficiency=efficiency, warehouse_id=warehouse_id)
    return await get_client().boms_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def boms_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, fk_product: Optional[int] = None, qty: Optional[float] = None, status: Optional[int] = None, description: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, duration: Optional[float] = None, efficiency: Optional[float] = None, warehouse_id: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing BOM.

    Args:
        id: The unique ID of the resource.
        ref: Reference.
        label: Label.
        fk_product: Product ID.
        qty: Quantity.
        status: Status.
        description: Description.
        note_public: Public note.
        note_private: Private note.
        duration: Duration.
        efficiency: Efficiency rate.
        warehouse_id: Warehouse ID.
    """
    payload = {k: v for k, v in {"ref": ref, "label": label, "fk_product": fk_product, "qty": qty, "status": status, "description": description, "note_public": note_public, "note_private": note_private, "duration": duration, "efficiency": efficiency, "warehouse_id": warehouse_id}.items() if v is not None}
    return await get_client().boms_update(id, payload, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def boms_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a BOM by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().boms_delete(id, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def boms_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get lines for a BOM.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().boms_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def boms_create_line(id: int, fk_product: int = 0, qty: float = 0.0, desc: str = "", warehouse_id: int = 0, position: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add a line to a BOM.

    Args:
        id: The unique ID of the resource.
        fk_product: Product ID.
        qty: Quantity.
        desc: Desc.
        warehouse_id: Warehouse ID.
        position: Position.
    """
    params = CreateBomLineParam(fk_product=fk_product, qty=qty, desc=desc, warehouse_id=warehouse_id, position=position)
    return await get_client().boms_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def boms_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a line from a BOM.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
    """
    return await get_client().boms_delete_line(id, lineid, get_user_token())

# ============================================================
# MOs (Manufacturing Orders)
# ============================================================
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def mos_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Mos List.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().mos_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def mos_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Mos Get.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().mos_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def mos_create(ref: str, label: str, fk_product: int, qty: float, fk_warehouse: int, mrptype: int = 0, status: int = 0, note_public: str = "", note_private: str = "", date_planned: str = "", bom_id: int = 0, priority: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Mos Create.

    Args:
        ref: Reference.
        label: Label.
        fk_product: Product ID.
        qty: Quantity.
        fk_warehouse: Warehouse ID.
        mrptype: MO type (0=...).
        status: Status.
        note_public: Public note.
        note_private: Private note.
        date_planned: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        bom_id: BOM ID.
        priority: Priority.
    """
    date_planned = _normalize_datetime(date_planned)
    params = CreateMOParam(ref=ref, label=label, fk_product=fk_product, qty=qty, fk_warehouse=fk_warehouse, mrptype=mrptype, status=status, note_public=note_public, note_private=note_private, date_planned=date_planned, bom_id=bom_id, priority=priority)
    return await get_client().mos_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def mos_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, fk_product: Optional[int] = None, qty: Optional[float] = None, fk_warehouse: Optional[int] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, date_planned: Optional[str] = None, bom_id: Optional[int] = None, priority: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Mos Update.

    Args:
        id: The unique ID of the resource.
        ref: Reference.
        label: Label.
        fk_product: Product ID.
        qty: Quantity.
        fk_warehouse: Warehouse ID.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        date_planned: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        bom_id: BOM ID.
        priority: Priority.
    """
    payload = {k: v for k, v in {"ref": ref, "label": label, "fk_product": fk_product, "qty": qty, "fk_warehouse": fk_warehouse, "status": status, "note_public": note_public, "note_private": note_private, "date_planned": date_planned, "bom_id": bom_id, "priority": priority}.items() if v is not None}
    for key in ['date_planned']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().mos_update(id, payload, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def mos_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Mos Delete.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().mos_delete(id, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def mos_produce_and_consume(id: int, inventorylabel: str, inventorycode: str, arraytoconsume: list[ConsumeLine] = None, arraytoproduce: list[ProduceLine] = None, autoclose: int = 1, ctx: Context = None) -> dict[str, Any]:
    """Record consumption of raw materials and production of finished product for a manufacturing order.

    The MO must be in Validated (1) or In Progress (2) status.

    Args:
        id: The unique ID of the MO.
        inventorylabel: Inventory movement label.
        inventorycode: Inventory movement code.
        arraytoconsume: List of objects to consume, each with objectid (MoLine rowid), qty, fk_warehouse.
        arraytoproduce: List of objects to produce, each with objectid (MoLine rowid), qty, fk_warehouse.
        autoclose: Auto-close MO after production (1=yes, 0=no).
    """
    payload = {
        "inventorylabel": inventorylabel,
        "inventorycode": inventorycode,
        "autoclose": autoclose,
        "arraytoconsume": [l.model_dump() for l in (arraytoconsume or [])],
        "arraytoproduce": [l.model_dump() for l in (arraytoproduce or [])],
    }
    return await get_client().mos_produce_and_consume(id, payload, get_user_token())

# ============================================================
# Projects
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def projects_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", category: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all projects.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        category: Category ID filter.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().projects_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, category=category, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def projects_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single project by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().projects_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def projects_create(ref: str, title: str, socid: int = 0, description: str = "", note_public: str = "", note_private: str = "", status: int = 0, date_start: str = "", date_end: str = "", budget_amount: float = 0.0, usage_opportunity: int = 0, usage_task: int = 0, usage_bill_time: int = 0, usage_organize_event: int = 0, public: int = 0, percent: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a new project.

    Args:
        ref: Reference.
        title: Title.
        socid: Third party ID.
        description: Description.
        note_public: Public note.
        note_private: Private note.
        status: Status.
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        budget_amount: Budget amount.
        usage_opportunity: Usage opportunity flag.
        usage_task: Usage task flag.
        usage_bill_time: Usage bill time flag.
        usage_organize_event: Usage organize event flag.
        public: Public access flag.
        percent: Progress percentage.
    """
    date_end = _normalize_datetime(date_end)
    date_start = _normalize_datetime(date_start)
    params = CreateProjectParam(ref=ref, title=title, socid=socid, description=description, note_public=note_public, note_private=note_private, status=status, date_start=date_start, date_end=date_end, budget_amount=budget_amount, usage_opportunity=usage_opportunity, usage_task=usage_task, usage_bill_time=usage_bill_time, usage_organize_event=usage_organize_event, public=public, percent=percent)
    return await get_client().projects_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def projects_update(id: int, ref: Optional[str] = None, title: Optional[str] = None, socid: Optional[int] = None, description: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, status: Optional[int] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, budget_amount: Optional[float] = None, usage_opportunity: Optional[int] = None, usage_task: Optional[int] = None, usage_bill_time: Optional[int] = None, usage_organize_event: Optional[int] = None, public: Optional[int] = None, percent: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing project.

    Args:
        id: The unique ID of the resource.
        ref: Reference.
        title: Title.
        socid: Third party ID.
        description: Description.
        note_public: Public note.
        note_private: Private note.
        status: Status.
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        budget_amount: Budget amount.
        usage_opportunity: Usage opportunity flag.
        usage_task: Usage task flag.
        usage_bill_time: Usage bill time flag.
        usage_organize_event: Usage organize event flag.
        public: Public access flag.
        percent: Progress percentage.
    """
    payload = {k: v for k, v in {"ref": ref, "title": title, "socid": socid, "description": description, "note_public": note_public, "note_private": note_private, "status": status, "date_start": date_start, "date_end": date_end, "budget_amount": budget_amount, "usage_opportunity": usage_opportunity, "usage_task": usage_task, "usage_bill_time": usage_bill_time, "usage_organize_event": usage_organize_event, "public": public, "percent": percent}.items() if v is not None}
    for key in ['date_end', 'date_start']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().projects_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def projects_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a project by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().projects_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def projects_get_tasks(id: int, includetimespent: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Get tasks for a project.

    Args:
        id: The unique ID of the resource.
        includetimespent: Include time spent flag.
    """
    data = await get_client().projects_get_tasks(id, get_user_token(), includetimespent=includetimespent)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def projects_get_timespent(id: int, ctx: Context = None) -> dict[str, Any]:
    """Projects Get Timespent.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().projects_get_timespent(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def projects_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Projects Validate.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().projects_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def projects_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get contacts linked to a project.

    Args:
        id: The unique ID of the resource.
        type: Type.
    """
    data = await get_client().projects_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

# ============================================================
# Tasks
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def tasks_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all project tasks.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().tasks_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def tasks_get(id: int, includetimespent: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single task by ID.

    Args:
        id: The unique ID of the resource.
        includetimespent: Include time spent flag.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().tasks_get(id, get_user_token(), includetimespent=includetimespent, include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def tasks_create(ref: str, label: str, fk_project: int, description: str = "", note_public: str = "", note_private: str = "", status: int = 0, date_start: str = "", date_end: str = "", planned_workload: float = 0.0, progress: int = 0, budget_amount: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Create a new project task.

    Args:
        ref: Reference.
        label: Label.
        fk_project: Project ID.
        description: Description.
        note_public: Public note.
        note_private: Private note.
        status: Status.
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        planned_workload: Planned workload.
        progress: Progress percentage.
        budget_amount: Budget amount.
    """
    date_end = _normalize_datetime(date_end)
    date_start = _normalize_datetime(date_start)
    params = CreateTaskParam(ref=ref, label=label, fk_project=fk_project, description=description, note_public=note_public, note_private=note_private, status=status, date_start=date_start, date_end=date_end, planned_workload=planned_workload, progress=progress, budget_amount=budget_amount)
    return await get_client().tasks_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def tasks_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, fk_project: Optional[int] = None, description: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, status: Optional[int] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, planned_workload: Optional[float] = None, progress: Optional[int] = None, budget_amount: Optional[float] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing task.

    Args:
        id: The unique ID of the resource.
        ref: Reference.
        label: Label.
        fk_project: Project ID.
        description: Description.
        note_public: Public note.
        note_private: Private note.
        status: Status.
        date_start: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_end: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        planned_workload: Planned workload.
        progress: Progress percentage.
        budget_amount: Budget amount.
    """
    payload = {k: v for k, v in {"ref": ref, "label": label, "fk_project": fk_project, "description": description, "note_public": note_public, "note_private": note_private, "status": status, "date_start": date_start, "date_end": date_end, "planned_workload": planned_workload, "progress": progress, "budget_amount": budget_amount}.items() if v is not None}
    for key in ['date_end', 'date_start']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().tasks_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def tasks_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a task by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().tasks_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def tasks_get_timespent(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get time spent entries for a task.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().tasks_get_timespent(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def tasks_add_timespent(id: int, date: str, duration: float, product_id: int = 0, user_id: int = 0, note: str = "", progress: int = 0, billable: int = 1, ctx: Context = None) -> dict[str, Any]:
    """Add time spent to a task.

    Args:
        id: The unique ID of the resource.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        duration: Duration.
        product_id: Product ID.
        user_id: User ID.
        note: Note.
        progress: Progress percentage.
        billable: Billable (1 = yes, 0 = no).
    """
    date = _normalize_datetime(date)
    params = CreateTaskTimeSpentParam(date=date, duration=duration, product_id=product_id, user_id=user_id, note=note, progress=progress)
    payload = params.model_dump(exclude_unset=True)
    if billable != 1:
        payload["billable"] = billable
    result = await get_client().tasks_add_timespent(id, payload, get_user_token())
    # Fetch the timespent list to get the created entry's ID
    timespent_list = await get_client().tasks_get_timespent(id, get_user_token())
    if isinstance(timespent_list, list) and timespent_list:
        ts = timespent_list[-1]
        tsid = ts.get("timespent_line_id", 0)
        return {"id": tsid, "success": {"code": 200, "message": "Time spent added"}}
    return result

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def tasks_update_timespent(id: int, timespent_id: int, date: Optional[str] = None, duration: Optional[float] = None, product_id: Optional[int] = None, user_id: Optional[int] = None, note: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Tasks Update Timespent.

    Args:
        id: The unique ID of the resource.
        timespent_id: Timespent Id.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        duration: Duration.
        product_id: Product ID.
        user_id: User ID.
        note: Note.
    """
    payload = {k: v for k, v in {"date": date, "duration": duration, "product_id": product_id, "user_id": user_id, "note": note}.items() if v is not None}
    for key in ['date']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().tasks_update_timespent(id, timespent_id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def tasks_delete_timespent(id: int, timespent_id: int, ctx: Context = None) -> dict[str, Any]:
    """Tasks Delete Timespent.

    Args:
        id: The unique ID of the resource.
        timespent_id: Timespent Id.
    """
    return await get_client().tasks_delete_timespent(id, timespent_id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def tasks_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get contacts linked to a task.

    Args:
        id: The unique ID of the resource.
        type: Type.
    """
    data = await get_client().tasks_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

# ============================================================
# Shipments
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def shipments_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all shipments.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().shipments_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def shipments_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single shipment by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().shipments_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def shipments_create(socid: int, ref: str, origin_id: int = 0, origin_type: str = "", status: int = 0, note_public: str = "", note_private: str = "", date_delivery: str = "", shipping_method_id: int = 0, warehouse_id: int = 0, total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, weight: float = 0.0, volume: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Create a new shipment.

    Args:
        socid: Third party ID.
        ref: Reference.
        origin_id: Origin object ID.
        origin_type: Origin object type (e.g. commande).
        status: Status.
        note_public: Public note.
        note_private: Private note.
        date_delivery: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        shipping_method_id: Shipping method ID.
        warehouse_id: Warehouse ID.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        weight: Weight.
        volume: Volume.
    """
    date_delivery = _normalize_datetime(date_delivery)
    params = CreateShipmentParam(socid=socid, ref=ref, origin_id=origin_id, origin_type=origin_type, status=status, note_public=note_public, note_private=note_private, date_delivery=date_delivery, shipping_method_id=shipping_method_id, warehouse_id=warehouse_id, total_ht=total_ht, total_tva=total_tva, total_ttc=total_ttc, weight=weight, volume=volume)
    return await get_client().shipments_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def shipments_update(id: int, socid: Optional[int] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, date_delivery: Optional[str] = None, shipping_method_id: Optional[int] = None, warehouse_id: Optional[int] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, weight: Optional[float] = None, volume: Optional[float] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing shipment.

    Args:
        id: The unique ID of the resource.
        socid: Third party ID.
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        date_delivery: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        shipping_method_id: Shipping method ID.
        warehouse_id: Warehouse ID.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        weight: Weight.
        volume: Volume.
    """
    payload = {k: v for k, v in {"socid": socid, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "date_delivery": date_delivery, "shipping_method_id": shipping_method_id, "warehouse_id": warehouse_id, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "weight": weight, "volume": volume}.items() if v is not None}
    for key in ['date_delivery']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().shipments_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def shipments_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a shipment by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().shipments_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def shipments_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a shipment.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().shipments_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def shipments_close(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Close a shipment.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().shipments_close(id, get_user_token(), notrigger=notrigger)

# ============================================================
# Receptions
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def receptions_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all receptions.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().receptions_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def receptions_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single reception by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().receptions_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def receptions_create(socid: int, ref: str, origin_id: int = 0, origin_type: str = "", status: int = 0, note_public: str = "", note_private: str = "", date_delivery: str = "", warehouse_id: int = 0, total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Create a new reception.

    Args:
        socid: Third party ID.
        ref: Reference.
        origin_id: Origin object ID.
        origin_type: Origin object type (e.g. commande_fournisseur).
        status: Status.
        note_public: Public note.
        note_private: Private note.
        date_delivery: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        warehouse_id: Warehouse ID.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
    """
    date_delivery = _normalize_datetime(date_delivery)
    params = CreateReceptionParam(socid=socid, ref=ref, origin_id=origin_id, origin_type=origin_type, status=status, note_public=note_public, note_private=note_private, date_delivery=date_delivery, warehouse_id=warehouse_id, total_ht=total_ht, total_tva=total_tva, total_ttc=total_ttc)
    return await get_client().receptions_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def receptions_update(id: int, socid: Optional[int] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, date_delivery: Optional[str] = None, warehouse_id: Optional[int] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing reception.

    Args:
        id: The unique ID of the resource.
        socid: Third party ID.
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        date_delivery: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        warehouse_id: Warehouse ID.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
    """
    payload = {k: v for k, v in {"socid": socid, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "date_delivery": date_delivery, "warehouse_id": warehouse_id, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc}.items() if v is not None}
    for key in ['date_delivery']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().receptions_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def receptions_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a reception by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().receptions_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def receptions_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a reception.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().receptions_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def receptions_close(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Receptions Close.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().receptions_close(id, get_user_token(), notrigger=notrigger)

# ============================================================
# Interventions
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def interventions_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all interventions.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        thirdparty_ids: Comma-separated third party IDs.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().interventions_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def interventions_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single intervention by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().interventions_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def interventions_create(socid: int, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", date: str = "", description: str = "", fk_user_author: int = 0, fk_user_intervenant: int = 0, fk_project: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a new intervention.

    Args:
        socid: Third party ID.
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        description: Description.
        fk_user_author: Author user ID.
        fk_user_intervenant: Intervening user ID.
        fk_project: Project ID.
    """
    date = _normalize_datetime(date)
    params = CreateInterventionParam(socid=socid, ref=ref, status=status, note_public=note_public, note_private=note_private, date=date, description=description, fk_user_author=fk_user_author, fk_user_intervenant=fk_user_intervenant, fk_project=fk_project)
    return await get_client().interventions_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def interventions_update(id: int, socid: Optional[int] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, date: Optional[str] = None, description: Optional[str] = None, fk_user_author: Optional[int] = None, fk_user_intervenant: Optional[int] = None, fk_project: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing intervention.

    Args:
        id: The unique ID of the resource.
        socid: Third party ID.
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        description: Description.
        fk_user_author: Author user ID.
        fk_user_intervenant: Intervening user ID.
        fk_project: Project ID.
    """
    payload = {k: v for k, v in {"socid": socid, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "date": date, "description": description, "fk_user_author": fk_user_author, "fk_user_intervenant": fk_user_intervenant, "fk_project": fk_project}.items() if v is not None}
    for key in ['date']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().interventions_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def interventions_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an intervention by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().interventions_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def interventions_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get lines for an intervention.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().interventions_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def interventions_create_line(id: int, description: str = "", duration: float = 0.0, product_id: int = 0, qty: float = 0.0, subprice: float = 0.0, tva_tx: float = 0.0, date: str = "", price_base_type: str = "HT", rang: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add a line to an intervention.

    Args:
        id: The unique ID of the resource.
        description: Description.
        duration: Duration.
        product_id: Product ID.
        qty: Quantity.
        subprice: Unit price.
        tva_tx: VAT rate.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        price_base_type: Price base type (HT or TTC).
        rang: Line position.
    """
    date = _normalize_datetime(date)
    params = CreateInterventionLineParam(description=description, duration=duration, product_id=product_id, qty=qty, subprice=subprice, tva_tx=tva_tx, date=date, price_base_type=price_base_type, rang=rang)
    return await get_client().interventions_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def interventions_update_line(id: int, lineid: int, desc: Optional[str] = None, duration: Optional[float] = None, product_id: Optional[int] = None, qty: Optional[float] = None, subprice: Optional[float] = None, tva_tx: Optional[float] = None, date: Optional[str] = None, price_base_type: Optional[str] = None, rang: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a line in an intervention.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
        desc: Desc.
        duration: Duration.
        product_id: Product ID.
        qty: Quantity.
        subprice: Unit price.
        tva_tx: VAT rate.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        price_base_type: Price base type (HT or TTC).
        rang: Line position.
    """
    payload = {k: v for k, v in {"desc": desc, "duration": duration, "product_id": product_id, "qty": qty, "subprice": subprice, "tva_tx": tva_tx, "date": date, "price_base_type": price_base_type, "rang": rang}.items() if v is not None}
    for key in ['date']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().interventions_update_line(id, lineid, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def interventions_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a line from an intervention.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
    """
    return await get_client().interventions_delete_line(id, lineid, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def interventions_settodraft(id: int, ctx: Context = None) -> dict[str, Any]:
    """Set an intervention to draft status.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().interventions_settodraft(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def interventions_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate an intervention.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().interventions_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def interventions_close(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Interventions Close.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().interventions_close(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def interventions_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get contacts linked to an intervention.

    Args:
        id: The unique ID of the resource.
        type: Type.
    """
    data = await get_client().interventions_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

# ============================================================
# Expense Reports
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def expense_reports_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports List.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        user_ids: Comma-separated user IDs.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().expense_reports_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, user_ids=user_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def expense_reports_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Get.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().expense_reports_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_create(fk_user: int, date_debut: str, date_fin: str, fk_user_author: int, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, fk_project: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Create.

    Args:
        fk_user: User ID.
        date_debut: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_fin: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        fk_user_author: Author user ID.
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        fk_project: Project ID.
    """
    params = CreateExpenseReportParam(
        fk_user=fk_user, date_debut=_normalize_datetime(date_debut),
        date_fin=_normalize_datetime(date_fin),
        fk_user_author=fk_user_author, ref=ref, status=status,
        note_public=note_public, note_private=note_private,
        total_ht=total_ht, total_tva=total_tva,
        total_ttc=total_ttc, fk_project=fk_project,
    )
    return await get_client().expense_reports_create(params.model_dump(), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_update(id: int, fk_user: Optional[int] = None, date_debut: Optional[str] = None, date_fin: Optional[str] = None, fk_user_author: Optional[int] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, fk_project: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Update.

    Args:
        id: The unique ID of the resource.
        fk_user: User ID.
        date_debut: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_fin: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        fk_user_author: Author user ID.
        ref: Reference.
        status: Status.
        note_public: Public note.
        note_private: Private note.
        total_ht: Total before tax.
        total_tva: Total VAT.
        total_ttc: Total including tax.
        fk_project: Project ID.
    """
    payload = {k: v for k, v in {"fk_user": fk_user, "date_debut": date_debut, "date_fin": date_fin, "fk_user_author": fk_user_author, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "fk_project": fk_project}.items() if v is not None}
    for key in ['date_debut', 'date_fin']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().expense_reports_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Delete.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().expense_reports_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def expense_reports_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Get Lines.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().expense_reports_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_create_line(id: int, date: str, fk_c_type_fees: int, qty: float, value_unit: float, product_id: int = 0, comment: str = "", vatrate: float = 0.0, localtax1_tx: float = 0.0, localtax2_tx: float = 0.0, fk_project: int = 0, fk_soc: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Create Line.

    Args:
        id: The unique ID of the resource.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        fk_c_type_fees: Fee type ID.
        qty: Quantity.
        value_unit: Value Unit.
        product_id: Product ID.
        comment: Comment.
        vatrate: VAT rate.
        localtax1_tx: Localtax1 Tx.
        localtax2_tx: Localtax2 Tx.
        fk_project: Project ID.
        fk_soc: Third party ID.
    """
    date = _normalize_datetime(date)
    params = CreateExpenseReportLineParam(date=date, fk_c_type_fees=fk_c_type_fees, qty=qty, value_unit=value_unit, product_id=product_id, comment=comment, vatrate=vatrate, localtax1_tx=localtax1_tx, localtax2_tx=localtax2_tx, fk_project=fk_project, fk_soc=fk_soc)
    return await get_client().expense_reports_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_update_line(id: int, lineid: int, date: Optional[str] = None, fk_c_type_fees: Optional[int] = None, qty: Optional[float] = None, value_unit: Optional[float] = None, product_id: Optional[int] = None, comment: Optional[str] = None, tva_tx: Optional[float] = None, localtax1_tx: Optional[float] = None, localtax2_tx: Optional[float] = None, fk_project: Optional[int] = None, fk_soc: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Update Line.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
        date: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        fk_c_type_fees: Fee type ID.
        qty: Quantity.
        value_unit: Value Unit.
        product_id: Product ID.
        comment: Comment.
        tva_tx: VAT rate.
        localtax1_tx: Localtax1 Tx.
        localtax2_tx: Localtax2 Tx.
        fk_project: Project ID.
        fk_soc: Third party ID.
    """
    payload = {k: v for k, v in {"date": date, "fk_c_type_fees": fk_c_type_fees, "qty": qty, "value_unit": value_unit, "product_id": product_id, "comment": comment, "tva_tx": tva_tx, "localtax1_tx": localtax1_tx, "localtax2_tx": localtax2_tx, "fk_project": fk_project, "fk_soc": fk_soc}.items() if v is not None}
    for key in ['date']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().expense_reports_update_line(id, lineid, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Delete Line.

    Args:
        id: The unique ID of the resource.
        lineid: The line ID.
    """
    return await get_client().expense_reports_delete_line(id, lineid, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_settodraft(id: int, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Settodraft.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().expense_reports_settodraft(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Validate.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().expense_reports_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_approve(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Approve.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().expense_reports_approve(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_deny(id: int, details: str = "", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Deny.

    Args:
        id: The unique ID of the resource.
        details: Details.
        notrigger: Disable triggers flag.
    """
    return await get_client().expense_reports_deny(id, get_user_token(), details=details, notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def expense_reports_cancel(id: int, detail: str = "", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Expense Reports Cancel.

    Args:
        id: The unique ID of the resource.
        detail: Detail.
        notrigger: Disable triggers flag.
    """
    return await get_client().expense_reports_cancel(id, get_user_token(), detail=detail, notrigger=notrigger)

# ============================================================
# Holidays
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def holidays_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all leave/holiday requests.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        user_ids: Comma-separated user IDs.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().holidays_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, user_ids=user_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def holidays_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single leave request by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().holidays_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def holidays_create(fk_user: int, date_debut: str, date_fin: str, halfday: int, fk_type: int, fk_validator: int = 0, note: str = "", status: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a new leave/holiday request.

    Args:
        fk_user: User ID.
        date_debut: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_fin: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        halfday: Half day flag (0=full, 1=morning, 2=afternoon).
        fk_type: Leave type ID.
        fk_validator: Validator user ID.
        note: Note.
        status: Status.
    """
    date_debut = _normalize_datetime(date_debut)
    date_fin = _normalize_datetime(date_fin)
    params = CreateHolidayParam(fk_user=fk_user, date_debut=date_debut, date_fin=date_fin, halfday=halfday, fk_type=fk_type, fk_validator=fk_validator, note=note, status=status)
    return await get_client().holidays_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def holidays_update(id: int, fk_user: Optional[int] = None, date_debut: Optional[str] = None, date_fin: Optional[str] = None, halfday: Optional[int] = None, fk_type: Optional[int] = None, note: Optional[str] = None, status: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing leave request.

    Args:
        id: The unique ID of the resource.
        fk_user: User ID.
        date_debut: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        date_fin: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        halfday: Half day flag (0=full, 1=morning, 2=afternoon).
        fk_type: Leave type ID.
        note: Note.
        status: Status.
    """
    payload = {k: v for k, v in {"fk_user": fk_user, "date_debut": date_debut, "date_fin": date_fin, "halfday": halfday, "fk_type": fk_type, "note": note, "status": status}.items() if v is not None}
    for key in ['date_debut', 'date_fin']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().holidays_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def holidays_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a leave request by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().holidays_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def holidays_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a leave request.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().holidays_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def holidays_approve(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Approve a leave request.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().holidays_approve(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def holidays_cancel(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Holidays Cancel.

    Args:
        id: The unique ID of the resource.
        notrigger: Disable triggers flag.
    """
    return await get_client().holidays_cancel(id, get_user_token(), notrigger=notrigger)

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def holidays_refuse(id: int, detail_refuse: str = "", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Holidays Refuse.

    Args:
        id: The unique ID of the resource.
        detail_refuse: Refusal detail.
        notrigger: Disable triggers flag.
    """
    return await get_client().holidays_refuse(id, get_user_token(), detail_refuse=detail_refuse, notrigger=notrigger)

# ============================================================
# Agenda Events
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def agenda_events_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Agenda Events List.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        user_ids: Comma-separated user IDs.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().agenda_events_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, user_ids=user_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def agenda_events_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Agenda Events Get.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().agenda_events_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def agenda_events_create(type_code: str, datep: str, label: str, note: str = "", author_user_id: int = 0, userownerid: int = 0, socid: int = 0, fk_project: int = 0, datep2: str = "", duration: int = 0, location: str = "", percent: int = 0, fulldayevent: int = 0, punctual: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Agenda Events Create.

    Args:
        type_code: Event type code.
        datep: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        label: Label.
        note: Note.
        author_user_id: Author user ID.
        userownerid: Owner user ID.
        socid: Third party ID.
        fk_project: Project ID.
        datep2: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        duration: Duration.
        location: Location.
        percent: Progress percentage.
        fulldayevent: Full day event flag.
        punctual: Punctual event flag.
    """
    datep = _normalize_datetime(datep)
    datep2 = _normalize_datetime(datep2)
    params = CreateAgendaEventParam(type_code=type_code, datep=datep, label=label, note=note, author_user_id=author_user_id, userownerid=userownerid, socid=socid, fk_project=fk_project, datep2=datep2, duration=duration, location=location, percent=percent, fulldayevent=fulldayevent, punctual=punctual)
    return await get_client().agenda_events_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def agenda_events_update(id: int, type_code: Optional[str] = None, datep: Optional[str] = None, label: Optional[str] = None, note: Optional[str] = None, author_user_id: Optional[int] = None, userownerid: Optional[int] = None, socid: Optional[int] = None, fk_project: Optional[int] = None, datep2: Optional[str] = None, duration: Optional[int] = None, location: Optional[str] = None, percent: Optional[int] = None, fulldayevent: Optional[int] = None, punctual: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Agenda Events Update.

    Args:
        id: The unique ID of the resource.
        type_code: Event type code.
        datep: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        label: Label.
        note: Note.
        author_user_id: Author user ID.
        userownerid: Owner user ID.
        socid: Third party ID.
        fk_project: Project ID.
        datep2: Use ISO 8601 format with explicit UTC offset (2026-06-22T15:00:00-04:00).
        duration: Duration.
        location: Location.
        percent: Progress percentage.
        fulldayevent: Full day event flag.
        punctual: Punctual event flag.
    """
    payload = {k: v for k, v in {"type_code": type_code, "datep": datep, "label": label, "note": note, "author_user_id": author_user_id, "userownerid": userownerid, "socid": socid, "fk_project": fk_project, "datep2": datep2, "duration": duration, "location": location, "percent": percent, "fulldayevent": fulldayevent, "punctual": punctual}.items() if v is not None}
    for key in ['datep', 'datep2']:
        if isinstance(payload.get(key), str) and payload[key]:
            payload[key] = _normalize_datetime(payload[key])
    return await get_client().agenda_events_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def agenda_events_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Agenda Events Delete.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().agenda_events_delete(id, get_user_token())

# ============================================================
# Categories
# ============================================================
@mcp.tool(tags={"dolibarr", "primary", "read"})
async def categories_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, type: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all categories.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        type: Type.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().categories_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, type=type, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def categories_get(id: int, include_childs: bool = False, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single category by ID.

    Args:
        id: The unique ID of the resource.
        include_childs: Include child categories flag.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().categories_get(id, get_user_token(), include_childs=include_childs, include_all_fields=include_all_fields)
@mcp.tool(tags={"dolibarr", "primary", "write"})
async def categories_create(ref: str, label: str, type: str, description: str = "", color: str = "", parent: int = 0, note_public: str = "", note_private: str = "", status: int = 1, ctx: Context = None) -> dict[str, Any]:
    """Create a new category.

    Args:
        ref: Reference.
        label: Label.
        type: Type.
        description: Description.
        color: Color.
        parent: Parent ID.
        note_public: Public note.
        note_private: Private note.
        status: Status.
    """
    params = CreateCategoryParam(ref=ref, label=label, type=type, description=description, color=color, parent=parent, note_public=note_public, note_private=note_private, status=status)
    return await get_client().categories_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def categories_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, type: Optional[str] = None, description: Optional[str] = None, color: Optional[str] = None, parent: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, status: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing category.

    Args:
        id: The unique ID of the resource.
        ref: Reference.
        label: Label.
        type: Type.
        description: Description.
        color: Color.
        parent: Parent ID.
        note_public: Public note.
        note_private: Private note.
        status: Status.
    """
    payload = {k: v for k, v in {"ref": ref, "label": label, "type": type, "description": description, "color": color, "parent": parent, "note_public": note_public, "note_private": note_private, "status": status}.items() if v is not None}
    return await get_client().categories_update(id, payload, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "write"})
async def categories_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a category by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().categories_delete(id, get_user_token())

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def categories_get_types(ctx: Context = None) -> dict[str, Any]:
    """Get all category types."""
    data = {"product":"Products","service":"Services","customer":"ProspectsOrCustomers","supplier":"Suppliers","member":"Members","contact":"Contacts","user":"Users","account":"Accounts","bank_account":"BankAccounts","bank_line":"BankTransactions","project":"Projects","warehouse":"Warehouse","actioncomm":"AgendaEvents","website_page":"WebsitePages","ticket":"Tickets","knowledgemanagement":"KnowledgeRecords","fichinter":"Interventions","order":"Orders","invoice":"Invoices","supplier_order":"SuppliersOrders","supplier_invoice":"SuppliersInvoices","stock_movement":"StockMovements","expense_report":"ExpenseReports","taxable":"Taxable","tax":"Taxes","shipping":"Shipments"}
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"dolibarr", "primary", "read"})
async def categories_get_for_object(type: str, id: int, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Categories Get For Object.

    Args:
        type: Type.
        id: The unique ID of the resource.
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
    """
    data = await get_client().categories_get_for_object(type, id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def categories_link_object_by_id(id: int, type: str, object_id: int, ctx: Context = None) -> dict[str, Any]:
    """Categories Link Object By Id.

    Args:
        id: The unique ID of the resource.
        type: Type.
        object_id: Object ID.
    """
    return await get_client().categories_link_object_by_id(id, type, object_id, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def categories_link_object_by_ref(id: int, type: str, object_ref: str, ctx: Context = None) -> dict[str, Any]:
    """Categories Link Object By Ref.

    Args:
        id: The unique ID of the resource.
        type: Type.
        object_ref: Object reference.
    """
    return await get_client().categories_link_object_by_ref(id, type, object_ref, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def categories_unlink_object(id: int, type: str, object_id: int, ctx: Context = None) -> dict[str, Any]:
    """Categories Unlink Object.

    Args:
        id: The unique ID of the resource.
        type: Type.
        object_id: Object ID.
    """
    return await get_client().categories_unlink_object(id, type, object_id, get_user_token())

# ============================================================
# Mailings
# ============================================================
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def mailings_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all mailings.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().mailings_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def mailings_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single mailing by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().mailings_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def mailings_create(title: str, sujet: str, body: str, email_from: str, mail_template_id: int = 0, mail_subject: str = "", note: str = "", status: int = 0, email_to: str = "", email_cc: str = "", email_bcc: str = "", lang: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a new mailing.

    Args:
        title: Title.
        sujet: Subject.
        body: Body.
        email_from: From email.
        mail_template_id: Mail template ID.
        mail_subject: Mail subject.
        note: Note.
        status: Status.
        email_to: To email.
        email_cc: CC email.
        email_bcc: BCC email.
        lang: Language code.
    """
    params = CreateMailingParam(title=title, sujet=sujet, body=body, email_from=email_from, mail_template_id=mail_template_id, mail_subject=mail_subject, note=note, status=status, email_to=email_to, email_cc=email_cc, email_bcc=email_bcc, lang=lang)
    return await get_client().mailings_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def mailings_update(id: int, title: Optional[str] = None, mail_template_id: Optional[int] = None, mail_subject: Optional[str] = None, note: Optional[str] = None, status: Optional[int] = None, sujet: Optional[str] = None, body: Optional[str] = None, email_from: Optional[str] = None, email_to: Optional[str] = None, email_cc: Optional[str] = None, email_bcc: Optional[str] = None, lang: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing mailing.

    Args:
        id: The unique ID of the resource.
        title: Title.
        mail_template_id: Mail template ID.
        mail_subject: Mail subject.
        note: Note.
        status: Status.
        sujet: Subject.
        body: Body.
        email_from: From email.
        email_to: To email.
        email_cc: CC email.
        email_bcc: BCC email.
        lang: Language code.
    """
    payload = {k: v for k, v in {"title": title, "mail_template_id": mail_template_id, "mail_subject": mail_subject, "note": note, "status": status, "sujet": sujet, "body": body, "email_from": email_from, "email_to": email_to, "email_cc": email_cc, "email_bcc": email_bcc, "lang": lang}.items() if v is not None}
    return await get_client().mailings_update(id, payload, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def mailings_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a mailing by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().mailings_delete(id, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def mailings_validate(id: int, ctx: Context = None) -> dict[str, Any]:
    """Mailings Validate.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().mailings_validate(id, get_user_token())

# ============================================================
# Multi Currencies
# ============================================================
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def multi_currencies_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Multi Currencies List.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().multi_currencies_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def multi_currencies_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Multi Currencies Get.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().multi_currencies_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def multi_currencies_create(code: str, name: str, rate: float = 1.0, status: int = 1, note: str = "", ctx: Context = None) -> dict[str, Any]:
    """Multi Currencies Create.

    Args:
        code: Code.
        name: Name.
        rate: Exchange rate.
        status: Status.
        note: Note.
    """
    params = CreateMultiCurrencyParam(code=code, name=name, rate=rate, status=status, note=note)
    return await get_client().multi_currencies_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def multi_currencies_update(id: int, code: Optional[str] = None, name: Optional[str] = None, rate: Optional[float] = None, status: Optional[int] = None, note: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Multi Currencies Update.

    Args:
        id: The unique ID of the resource.
        code: Code.
        name: Name.
        rate: Exchange rate.
        status: Status.
        note: Note.
    """
    payload = {k: v for k, v in {"code": code, "name": name, "rate": rate, "status": status, "note": note}.items() if v is not None}
    return await get_client().multi_currencies_update(id, payload, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def multi_currencies_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Multi Currencies Delete.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().multi_currencies_delete(id, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def multi_currencies_get_rates(id: int, ctx: Context = None) -> dict[str, Any]:
    """Multi Currencies Get Rates.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().multi_currencies_get_rates(id, get_user_token())
    return {"items": json_to_toon(data)}

# ============================================================
# Tickets
# ============================================================
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def tickets_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, socid: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all tickets.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        socid: Third party ID.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().tickets_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, socid=socid, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def tickets_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single ticket by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().tickets_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def tickets_create(subject: str, type_code: str, severity_code: str, category_code: str, socid: int = 0, note_public: str = "", note_private: str = "", track_id: str = "", fk_user_assign: int = 0, email: str = "", origin: str = "", origin_id: int = 0, message: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a new ticket.

    Args:
        subject: Subject.
        type_code: Event type code.
        severity_code: Severity code.
        category_code: Category code.
        socid: Third party ID.
        note_public: Public note.
        note_private: Private note.
        track_id: Track ID.
        fk_user_assign: Assigned user ID.
        email: Email address.
        origin: Origin.
        origin_id: Origin object ID.
        message: Message.
    """
    params = CreateTicketParam(subject=subject, type_code=type_code, severity_code=severity_code, category_code=category_code, socid=socid, note_public=note_public, note_private=note_private, track_id=track_id, fk_user_assign=fk_user_assign, email=email, origin=origin, origin_id=origin_id, message=message)
    return await get_client().tickets_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def tickets_update(id: int, subject: Optional[str] = None, type_code: Optional[str] = None, severity_code: Optional[str] = None, category_code: Optional[str] = None, socid: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, track_id: Optional[str] = None, fk_user_assign: Optional[int] = None, email: Optional[str] = None, origin: Optional[str] = None, origin_id: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing ticket.

    Args:
        id: The unique ID of the resource.
        subject: Subject.
        type_code: Event type code.
        severity_code: Severity code.
        category_code: Category code.
        socid: Third party ID.
        note_public: Public note.
        note_private: Private note.
        track_id: Track ID.
        fk_user_assign: Assigned user ID.
        email: Email address.
        origin: Origin.
        origin_id: Origin object ID.
    """
    payload = {k: v for k, v in {"subject": subject, "type_code": type_code, "severity_code": severity_code, "category_code": category_code, "socid": socid, "note_public": note_public, "note_private": note_private, "track_id": track_id, "fk_user_assign": fk_user_assign, "email": email, "origin": origin, "origin_id": origin_id}.items() if v is not None}
    return await get_client().tickets_update(id, payload, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def tickets_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a ticket by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().tickets_delete(id, get_user_token())


@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def tickets_create_message(track_id: str, message: str, fk_user_author: int = 0, note_public: str = "", note_private: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a message on a ticket identified by its track_id.

    Args:
        track_id: The ticket's track_id (UUID string, not numeric ID).
        message: The message text.
        fk_user_author: User author ID.
        note_public: Public note.
        note_private: Private note.
    """
    params = CreateTicketMessageParam(track_id=track_id, message=message, fk_user_author=fk_user_author, note_public=note_public, note_private=note_private)
    result = await get_client().tickets_create_message(params.model_dump(exclude_unset=True), get_user_token())
    if not isinstance(result, dict):
        return {"id": result}
    return result

# ============================================================
# Workstations
# ============================================================
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def workstations_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all workstations.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().workstations_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def workstations_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single workstation by ID.

    Args:
        id: The unique ID of the resource.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().workstations_get(id, get_user_token(), include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def workstations_create(label: str, status: int = 0, ref: str = "", type: str = "", nb_operator: int = 1, cost: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Create a new workstation.

    Args:
        label: Label.
        status: Status (0=draft, 1=active).
        ref: Reference.
        type: Type.
        nb_operator: Number of operators.
        cost: Cost.
    """
    params = {"label": label, "status": status}
    if ref: params["ref"] = ref
    if type: params["type"] = type
    if nb_operator != 1: params["nb_operator"] = nb_operator
    if cost: params["cost"] = cost
    return await get_client().workstations_create(params, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def workstations_update(id: int, label: Optional[str] = None, status: Optional[int] = None, type: Optional[str] = None, nb_operator: Optional[int] = None, cost: Optional[float] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing workstation.

    Args:
        id: The unique ID of the resource.
        label: Label.
        status: Status.
        type: Type.
        nb_operator: Number of operators.
        cost: Cost.
    """
    payload = {k: v for k, v in {"label": label, "status": status, "type": type, "nb_operator": nb_operator, "cost": cost}.items() if v is not None}
    return await get_client().workstations_update(id, payload, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def workstations_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a workstation by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().workstations_delete(id, get_user_token())

# ============================================================
# Object Links
# ============================================================
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def object_links_get(id: int, ctx: Context = None) -> dict[str, Any]:
    """Object Links Get.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().object_links_get(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def object_links_create(fk_source: int, sourcetype: str, fk_target: int, targettype: str, relationtype: str = "", ctx: Context = None) -> dict[str, Any]:
    """Object Links Create.

    Args:
        fk_source: Source object ID.
        sourcetype: Source object type.
        fk_target: Target object ID.
        targettype: Target object type.
        relationtype: Relation type.
    """
    def _map_type(t: str) -> str:
        return {"thirdparty": "societe", "contact": "societe", "subscription": "adherent", "conferenceorboothattendee": "projet"}.get(t, t)
    st = _map_type(sourcetype)
    tt = _map_type(targettype)
    params = CreateObjectLinkParam(fk_source=fk_source, sourcetype=st, fk_target=fk_target, targettype=tt, relationtype=relationtype)
    return await get_client().object_links_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def object_links_get_by_values(fk_source: int = 0, sourcetype: str = "", fk_target: int = 0, targettype: str = "", relationtype: str = "", ctx: Context = None) -> dict[str, Any]:
    """Object Links Get By Values.

    Args:
        fk_source: Source object ID.
        sourcetype: Source object type.
        fk_target: Target object ID.
        targettype: Target object type.
        relationtype: Relation type.
    """
    def _map_type(t: str) -> str:
        return {"thirdparty": "societe", "contact": "societe", "subscription": "adherent", "conferenceorboothattendee": "projet"}.get(t, t)
    st = _map_type(sourcetype)
    tt = _map_type(targettype)
    return await get_client().object_links_get_by_values(get_user_token(), fk_source=fk_source, sourcetype=st, fk_target=fk_target, targettype=tt, relationtype=relationtype)

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def object_links_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Object Links Delete.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().object_links_delete(id, get_user_token())

# ============================================================
# Users
# ============================================================
@mcp.tool(tags={"basic", "dolibarr", "read"})
async def users_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", category: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List all users.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        user_ids: Comma-separated user IDs.
        category: Category ID filter.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().users_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, user_ids=user_ids, category=category, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"basic", "dolibarr", "read"})
async def users_get(id: int, includepermissions: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single user by ID.

    Args:
        id: The unique ID of the resource.
        includepermissions: Include permissions flag.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().users_get(id, get_user_token(), includepermissions=includepermissions, include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def users_get_by_login(login: str, includepermissions: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Users Get By Login.

    Args:
        login: Login.
        includepermissions: Include permissions flag.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().users_get_by_login(login, get_user_token(), includepermissions=includepermissions, include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def users_get_by_email(email: str, includepermissions: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Users Get By Email.

    Args:
        email: Email address.
        includepermissions: Include permissions flag.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().users_list(get_user_token(), sqlfilters=f"(email:=:'{email}')", limit=1)
    user = isinstance(data, list) and len(data) > 0 and data[0] or {}
    return isinstance(user, dict) and user or {}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def users_get_info(includepermissions: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Users Get Info.

    Args:
        includepermissions: Include permissions flag.
    """
    return await get_client().users_get_info(get_user_token(), includepermissions=includepermissions)

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def users_list_groups(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, group_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Users List Groups.

    Args:
        sortfield: Field to sort by.
        sortorder: Sort order (ASC or DESC).
        limit: Maximum number of results.
        page: Page number (0-based).
        group_ids: Group Ids.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    data = await get_client().users_list_groups(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, group_ids=group_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields if ALLOW_ALL_AGGREGATE else False)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def users_get_group(id: int, load_members: int = 0, includepermissions: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Users Get Group.

    Args:
        id: The unique ID of the resource.
        load_members: Load Members.
        includepermissions: Include permissions flag.
        include_all_fields: When False (default), returns only commonly used fields. Set to True to retrieve all available fields.
    """
    return await get_client().users_get_group(id, get_user_token(), load_members=load_members, includepermissions=includepermissions, include_all_fields=include_all_fields)
@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def users_get_user_groups(id: int, ctx: Context = None) -> dict[str, Any]:
    """Users Get User Groups.

    Args:
        id: The unique ID of the resource.
    """
    data = await get_client().users_get_user_groups(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def users_create(login: str, email: str, password: str, lastname: str = "", firstname: str = "", status: int = 1, ctx: Context = None) -> dict[str, Any]:
    """Create a new user.

    Args:
        login: Login.
        email: Email.
        password: Password.
        lastname: Last name.
        firstname: First name.
        status: Status (0=disabled, 1=enabled).
    """
    payload = {"login": login, "email": email, "password": password, "lastname": lastname, "firstname": firstname, "status": status}
    return await get_client().users_create(payload, get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def users_update(id: int, email: Optional[str] = None, lastname: Optional[str] = None, firstname: Optional[str] = None, status: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an existing user.

    Args:
        id: The unique ID of the resource.
        email: Email.
        lastname: Last name.
        firstname: First name.
        status: Status.
    """
    payload = {k: v for k, v in {"email": email, "lastname": lastname, "firstname": firstname, "status": status}.items() if v is not None}
    return await get_client().users_update(id, payload, get_user_token())

@mcp.tool(tags={"basic", "dolibarr", "write"})
async def users_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a user by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().users_delete(id, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def groups_create(name: str, ctx: Context = None) -> dict[str, Any]:
    """Create a new user group.

    Args:
        name: Group name.
    """
    payload = {"nom": name}
    return await get_client().groups_create(payload, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "write"})
async def groups_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a group by ID.

    Args:
        id: The unique ID of the resource.
    """
    return await get_client().groups_delete(id, get_user_token())

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def payment_types_list(active: int = 1, ctx: Context = None) -> dict[str, Any]:
    """List payment types (from dictionary data).

    Args:
        active: Filter on active types (default 1).
    """
    data = await get_client().payment_types_list(get_user_token(), active=active)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def expense_types_list(active: int = 1, ctx: Context = None) -> dict[str, Any]:
    """List expense report types (from dictionary data).

    Args:
        active: Filter on active types (default 1).
    """
    data = await get_client().expense_types_list(get_user_token(), active=active)
    return {"items": json_to_toon(data)}

@mcp.tool(tags={"advanced", "dolibarr", "read"})
async def holiday_types_list(active: int = 1, ctx: Context = None) -> dict[str, Any]:
    """List holiday types (from dictionary data).

    Args:
        active: Filter on active types (default 1).
    """
    data = await get_client().holiday_types_list(get_user_token(), active=active)
    return {"items": json_to_toon(data)}

# ============================================================
# Main Entry Point
# ============================================================
def main() -> None:
    """Run the MCP server."""
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "6033"))
    base_url = os.getenv("DOLIBARR_BASE_URL", "")
    IS_STATEFUL = os.getenv("IS_STATEFUL", "false").lower() in ("true", "1", "yes")
    if not base_url:
        print("ERROR: DOLIBARR_BASE_URL environment variable is required.")
        sys.exit(1)
    app = AuthMiddleware(mcp.http_app(json_response=True, stateless_http=not IS_STATEFUL))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
