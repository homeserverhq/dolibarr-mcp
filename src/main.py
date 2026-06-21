import os
import sys
from contextvars import ContextVar
from typing import Any, Optional

from fastmcp import FastMCP, Context
from pydantic import BaseModel
from toon_mcp import json_to_toon

from .client import DolibarrClient, _normalize_datetime

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
    closepaidinvoices: int = 0
    num_payment: str = ""
    comment: str = ""
    chqemetteur: str = ""
    chqbank: str = ""


class CreateInvoiceContactParam(BaseModel):
    fk_socpeople: int
    type_contact: str
    source: str = "external"
    notrigger: int = 0


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
    closepaidinvoices: int = 0
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


class CreateProjectTaskParam(BaseModel):
    ref: str
    label: str
    description: str = ""
    note_public: str = ""
    note_private: str = ""
    status: int = 0
    date_start: str = ""
    date_end: str = ""
    planned_workload: float = 0.0
    progress: int = 0
    budget_amount: float = 0.0


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
    desc: str = ""
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
    tva_tx: float = 0.0
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
    mail_template_id: int
    mail_subject: str
    note: str = ""
    status: int = 0
    sujet: str = ""
    body: str = ""
    email_from: str = ""
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


class CreateTicketMessageParam(BaseModel):
    ticket_id: int
    message: str
    fk_user_author: int = 0
    note_public: str = ""
    note_private: str = ""


class CreateObjectLinkParam(BaseModel):
    fk_source: int
    sourcetype: str
    fk_target: int
    targettype: str
    relationtype: str = ""

# ============================================================
# Status
# ============================================================
@mcp.tool()
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
@mcp.tool()
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
    Args:
        modulepart: Module type (e.g. invoice, order, product) (required).
        id: ID of the parent element (required).
        ref: Reference of the parent element.
        include_all_fields: When False (default), returns only commonly used fields.
        sortfield: Field to sort by.
        sortorder: Sort order. Defaults to ASC.
        limit: Maximum results. Defaults to 100.
        page: Page number (0-based). Defaults to 0.
    """
    data = await get_client().documents_list(
        get_user_token(), modulepart=modulepart, id=id, ref=ref,
        include_all_fields=include_all_fields, sortfield=sortfield,
        sortorder=sortorder, limit=limit, page=page
    )
    return {"items": json_to_toon(data)}

# ============================================================
# Third Parties
# ============================================================
@mcp.tool()
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
        sortorder: Sort order. Defaults to ASC.
        limit: Maximum results. Defaults to 100.
        page: Page number (0-based). Defaults to 0.
        mode: Filter mode (1=customer, 2=prospect, 3=supplier).
        category: Category ID filter.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields.
    """
    data = await get_client().thirdparties_list(
        get_user_token(), sortfield=sortfield, sortorder=sortorder,
        limit=limit, page=page, mode=mode, category=category,
        sqlfilters=sqlfilters, include_all_fields=include_all_fields
    )
    return {"items": json_to_toon(data)}

@mcp.tool()
async def thirdparties_get(
    id: int,
    include_all_fields: bool = False,
    ctx: Context = None
) -> dict[str, Any]:
    """Get a single third party by ID.
    Args:
        id: The unique ID of the third party (required).
        include_all_fields: When False (default), returns only commonly used fields.
    """
    return await get_client().thirdparties_get(
        id, get_user_token(), include_all_fields=include_all_fields
    )

@mcp.tool()
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
        name: Company name (required).
        client: Is a customer (1=yes, 0=no) (required).
        fournisseur: Is a supplier (1=yes, 0=no) (required).
        address: Street address.
        zip: Postal/ZIP code.
        town: City/town.
        country_id: Country ID.
        country_code: Country code (e.g. US, FR).
        phone: Phone number.
        email: Email address.
        url: Website URL.
        code_client: Customer code.
        code_fournisseur: Supplier code.
        capital: Company capital.
        siren: SIREN number (France).
        siret: SIRET number (France).
        ape: APE code (France).
        tva_intra: Intra-community VAT number.
        status: Status (1=active, 0=inactive). Defaults to 1.
        note_public: Public note.
        note_private: Private note.
        parent: Parent third party ID.
        price_level: Price level.
        outstanding_limit: Outstanding bill limit.
        multicurrency_code: Multi-currency code.
    """
    payload = {k: v for k, v in {"name": name, "client": client, "fournisseur": fournisseur, "address": address, "zip": zip, "town": town, "country_id": country_id, "country_code": country_code, "phone": phone, "email": email, "url": url, "code_client": code_client, "code_fournisseur": code_fournisseur, "capital": capital, "siren": siren, "siret": siret, "ape": ape, "tva_intra": tva_intra, "status": status, "note_public": note_public, "note_private": note_private, "parent": parent, "price_level": price_level, "outstanding_limit": outstanding_limit, "multicurrency_code": multicurrency_code}.items() if v != "" or k in ("name", "client", "fournisseur")}
    return await get_client().thirdparties_create(
        payload, get_user_token()
    )

@mcp.tool()
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
        id: The unique ID of the third party (required).
        name: Company name.
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
        status: Status (1=active, 0=inactive).
        note_public: Public note.
        note_private: Private note.
        parent: Parent third party ID.
        price_level: Price level.
        outstanding_limit: Outstanding bill limit.
        multicurrency_code: Multi-currency code.
    """
    payload = {k: v for k, v in {"name": name, "client": client, "fournisseur": fournisseur, "address": address, "zip": zip, "town": town, "country_id": country_id, "country_code": country_code, "phone": phone, "email": email, "url": url, "code_client": code_client, "code_fournisseur": code_fournisseur, "capital": capital, "siren": siren, "siret": siret, "ape": ape, "tva_intra": tva_intra, "status": status, "note_public": note_public, "note_private": note_private, "parent": parent, "price_level": price_level, "outstanding_limit": outstanding_limit, "multicurrency_code": multicurrency_code}.items() if v is not None}
    return await get_client().thirdparties_update(
        id, payload, get_user_token()
    )

@mcp.tool()
async def thirdparties_delete(
    id: int,
    ctx: Context = None
) -> dict[str, Any]:
    """Delete a third party by ID.
    Args:
        id: The unique ID of the third party (required).
    """
    return await get_client().thirdparties_delete(id, get_user_token())

@mcp.tool()
async def thirdparties_get_outstanding_proposals(
    id: int,
    mode: str = "",
    ctx: Context = None
) -> dict[str, Any]:
    """Get outstanding proposals for a third party.
    Args:
        id: Third party ID (required).
        mode: Filter mode.
    """
    data = await get_client().thirdparties_get_outstanding_proposals(id, get_user_token(), mode=mode)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def thirdparties_get_outstanding_orders(
    id: int,
    mode: str = "",
    ctx: Context = None
) -> dict[str, Any]:
    """Get outstanding orders for a third party.
    Args:
        id: Third party ID (required).
        mode: Filter mode.
    """
    data = await get_client().thirdparties_get_outstanding_orders(id, get_user_token(), mode=mode)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def thirdparties_get_outstanding_invoices(
    id: int,
    mode: str = "",
    ctx: Context = None
) -> dict[str, Any]:
    """Get outstanding invoices for a third party.
    Args:
        id: Third party ID (required).
        mode: Filter mode.
    """
    data = await get_client().thirdparties_get_outstanding_invoices(id, get_user_token(), mode=mode)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def thirdparties_get_representatives(
    id: int,
    mode: int = 0,
    ctx: Context = None
) -> dict[str, Any]:
    """Get sales representatives for a third party.
    Args:
        id: Third party ID (required).
        mode: Mode.
    """
    data = await get_client().thirdparties_get_representatives(id, get_user_token(), mode=mode)
    return {"items": json_to_toon(data)}

@mcp.tool()
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
        id: Third party ID (required).
        sortfield: Field to sort by.
        sortorder: Sort order. Defaults to ASC.
        limit: Maximum results. Defaults to 100.
        page: Page number (0-based). Defaults to 0.
    """
    data = await get_client().thirdparties_get_categories(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page)
    return {"items": json_to_toon(data)}

# ============================================================
# Contacts
# ============================================================
@mcp.tool()
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
        sortorder: Sort order. Defaults to ASC.
        limit: Maximum results. Defaults to 100.
        page: Page number (0-based). Defaults to 0.
        thirdparty_ids: Comma-separated third party IDs.
        category: Category ID filter.
        sqlfilters: Dolibarr SQL filter syntax.
        include_all_fields: When False (default), returns only commonly used fields.
    """
    data = await get_client().contacts_list(
        get_user_token(), sortfield=sortfield, sortorder=sortorder,
        limit=limit, page=page, thirdparty_ids=thirdparty_ids,
        category=category, sqlfilters=sqlfilters,
        include_all_fields=include_all_fields
    )
    return {"items": json_to_toon(data)}

@mcp.tool()
async def contacts_get(
    id: int,
    include_all_fields: bool = False,
    ctx: Context = None
) -> dict[str, Any]:
    """Get a single contact by ID.
    Args:
        id: The unique ID of the contact (required).
        include_all_fields: When False (default), returns only commonly used fields.
    """
    return await get_client().contacts_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
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
        lastname: Last name (required).
        socid: Third party ID (required).
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
        status: Status (1=active, 0=inactive). Defaults to 1.
        birthday: Birthday (ISO 8601 with explicit UTC offset).
        poste: Job position.
        default_lang: Default language code.
    """
    params = CreateContactParam(
        lastname=lastname, socid=socid, firstname=firstname,
        address=address, zip=zip, town=town, country_id=country_id,
        phone=phone, phone_mobile=phone_mobile, email=email, skype=skype,
        note_public=note_public, note_private=note_private, status=status,
        birthday=birthday, poste=poste, default_lang=default_lang
    )
    return await get_client().contacts_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
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
        id: The unique ID of the contact (required).
        lastname: Last name.
        socid: Third party ID.
        firstname: First name.
        address: Address.
        zip: Postal code.
        town: City.
        country_id: Country ID.
        phone: Phone.
        phone_mobile: Mobile.
        email: Email.
        skype: Skype.
        note_public: Public note.
        note_private: Private note.
        status: Status.
        birthday: Birthday.
        poste: Position.
        default_lang: Language.
    """
    payload = {k: v for k, v in {"lastname": lastname, "socid": socid, "firstname": firstname, "address": address, "zip": zip, "town": town, "country_id": country_id, "phone": phone, "phone_mobile": phone_mobile, "email": email, "skype": skype, "note_public": note_public, "note_private": note_private, "status": status, "birthday": birthday, "poste": poste, "default_lang": default_lang}.items() if v is not None}
    return await get_client().contacts_update(id, payload, get_user_token())

@mcp.tool()
async def contacts_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a contact by ID.
    Args:
        id: The unique ID of the contact (required).
    """
    return await get_client().contacts_delete(id, get_user_token())

@mcp.tool()
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
        id: Contact ID (required).
        sortfield: Field to sort by.
        sortorder: Sort order.
        limit: Max results. Defaults to 100.
        page: Page number.
    """
    data = await get_client().contacts_get_categories(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page)
    return {"items": json_to_toon(data)}

# ============================================================
# Products
# ============================================================
@mcp.tool()
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
        sortorder: Sort order. Defaults to ASC.
        limit: Max results. Defaults to 100.
        page: Page number.
        mode: Mode (0=all, 1=product, 2=service).
        category: Category ID filter.
        sqlfilters: SQL filter.
        variant_filter: Variant filter.
        include_all_fields: When False, returns only common fields.
    """
    data = await get_client().products_list(
        get_user_token(), sortfield=sortfield, sortorder=sortorder,
        limit=limit, page=page, mode=mode, category=category,
        sqlfilters=sqlfilters, variant_filter=variant_filter,
        include_all_fields=include_all_fields
    )
    return {"items": json_to_toon(data)}

@mcp.tool()
async def products_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single product by ID.
    Args:
        id: Product ID (required).
        include_all_fields: When False, returns only common fields.
    """
    return await get_client().products_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
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
        ref: Product reference (required).
        label: Product label/name (required).
        type: Product type (0=product, 1=service) (required).
        status: Status (1=active, 0=inactive) (required).
        price: Unit price before tax (required).
        price_base_type: Price base type (HT or TTC) (required).
        description: Product description.
        note_public: Public note.
        note_private: Private note.
        duration_value: Duration value.
        duration_unit: Duration unit.
        barcode: Barcode.
        tva_tx: VAT rate.
        stock: Current stock.
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

@mcp.tool()
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
        id: Product ID (required).
        ref: Reference. label: Label. type: Type. status: Status. price: Price.
        price_base_type: Price base. description: Description. note_public: Public note.
        note_private: Private note. duration_value: Duration. duration_unit: Duration unit.
        barcode: Barcode. tva_tx: VAT. stock: Stock. pmp: Avg cost. weight: Weight.
        weight_units: Weight units. length: Length. width: Width. height: Height.
        surface: Surface. volume: Volume. country_id: Country.
        seuil_stock_alerte: Alert threshold. desiredstock: Desired stock.
        accountancy_code_sell: Sell account. accountancy_code_buy: Buy account.
        customcode: Customs. multicurrency_code: Currency. multicurrency_price: MCP.
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

@mcp.tool()
async def products_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a product by ID.
    Args:
        id: Product ID (required).
    """
    return await get_client().products_delete(id, get_user_token())

@mcp.tool()
async def products_get_subproducts(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get sub-products for a product.
    Args:
        id: Product ID (required).
    """
    data = await get_client().products_get_subproducts(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def products_get_categories(
    id: int, sortfield: str = "", sortorder: str = "ASC",
    limit: int = 100, page: int = 0, ctx: Context = None
) -> dict[str, Any]:
    """Get categories for a product.
    Args:
        id: Product ID (required). sortfield: Sort. sortorder: Order.
        limit: Max. Defaults to 100. page: Page.
    """
    data = await get_client().products_get_categories(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def products_get_stock(id: int, selected_warehouse_id: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Get stock information for a product.
    Args:
        id: Product ID (required). selected_warehouse_id: Warehouse filter.
    """
    return await get_client().products_get_stock(id, get_user_token(), selected_warehouse_id=selected_warehouse_id)

@mcp.tool()
async def products_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get contacts linked to a product.
    Args:
        id: Product ID (required). type: Contact type filter.
    """
    data = await get_client().products_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

# ============================================================
# Warehouses
# ============================================================
@mcp.tool()
async def warehouses_list(
    sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0,
    category: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None
) -> dict[str, Any]:
    """List all warehouses.
    Args:
        sortfield: Sort. sortorder: Order. limit: Max. Defaults to 100. page: Page.
        category: Category filter. sqlfilters: SQL filter.
        include_all_fields: When False, returns only common fields.
    """
    data = await get_client().warehouses_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, category=category, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def warehouses_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single warehouse by ID. Args: id: Warehouse ID (required). include_all_fields: When False, returns only common fields."""
    return await get_client().warehouses_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def warehouses_create(ref: str, label: str, status: int, description: str = "", lieu: str = "", address: str = "", zip: str = "", town: str = "", country_id: int = 0, phone: str = "", fax: str = "", accountancy_code: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a new warehouse. Args: ref: Reference (required). label: Label (required). status: Status (required). description: Desc. lieu: Location. address: Address. zip: Zip. town: Town. country_id: Country. phone: Phone. fax: Fax. accountancy_code: Acct code."""
    params = CreateWarehouseParam(ref=ref, label=label, status=status, description=description, lieu=lieu, address=address, zip=zip, town=town, country_id=country_id, phone=phone, fax=fax, accountancy_code=accountancy_code)
    return await get_client().warehouses_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def warehouses_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, status: Optional[int] = None, description: Optional[str] = None, lieu: Optional[str] = None, address: Optional[str] = None, zip: Optional[str] = None, town: Optional[str] = None, country_id: Optional[int] = None, phone: Optional[str] = None, fax: Optional[str] = None, accountancy_code: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a warehouse. Args: id: Warehouse ID (required)."""
    payload = {k: v for k, v in {"ref": ref, "label": label, "status": status, "description": description, "lieu": lieu, "address": address, "zip": zip, "town": town, "country_id": country_id, "phone": phone, "fax": fax, "accountancy_code": accountancy_code}.items() if v is not None}
    return await get_client().warehouses_update(id, payload, get_user_token())

@mcp.tool()
async def warehouses_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a warehouse. Args: id: Warehouse ID (required)."""
    return await get_client().warehouses_delete(id, get_user_token())

@mcp.tool()
async def warehouses_list_products(id: int, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List products in a warehouse. Args: id: Warehouse ID (required)."""
    data = await get_client().warehouses_list_products(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

# ============================================================
# Stock Movements
# ============================================================
@mcp.tool()
async def stockmovements_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List stock movements."""
    data = await get_client().stockmovements_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def stockmovements_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a stock movement by ID. Args: id: ID (required)."""
    return await get_client().stockmovements_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def stockmovements_create(product_id: int, warehouse_id: int, qty: float, type: int, batch: str = "", movementcode: str = "", label: str = "", price: float = 0.0, datem: str = "", sellBy: str = "", eatBy: str = "", origin_type: str = "", origin_id: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a stock movement. Args: product_id: Product ID (required). warehouse_id: Warehouse ID (required). qty: Quantity (required). type: Movement type (required)."""
    params = CreateStockMovementParam(product_id=product_id, warehouse_id=warehouse_id, qty=qty, type=type, batch=batch, movementcode=movementcode, label=label, price=price, datem=datem, sellBy=sellBy, eatBy=eatBy, origin_type=origin_type, origin_id=origin_id)
    return await get_client().stockmovements_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def stockmovements_update(id: int, product_id: Optional[int] = None, warehouse_id: Optional[int] = None, qty: Optional[float] = None, type: Optional[int] = None, batch: Optional[str] = None, movementcode: Optional[str] = None, label: Optional[str] = None, price: Optional[float] = None, datem: Optional[str] = None, sellBy: Optional[str] = None, eatBy: Optional[str] = None, origin_type: Optional[str] = None, origin_id: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a stock movement. Args: id: ID (required)."""
    payload = {k: v for k, v in {"product_id": product_id, "warehouse_id": warehouse_id, "qty": qty, "type": type, "batch": batch, "movementcode": movementcode, "label": label, "price": price, "datem": datem, "sellBy": sellBy, "eatBy": eatBy, "origin_type": origin_type, "origin_id": origin_id}.items() if v is not None}
    return await get_client().stockmovements_update(id, payload, get_user_token())

@mcp.tool()
async def stockmovements_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a stock movement. Args: id: ID (required)."""
    return await get_client().stockmovements_delete(id, get_user_token())

# ============================================================
# Product Lots
# ============================================================
@mcp.tool()
async def productlots_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List product lots/batches."""
    data = await get_client().productlots_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def productlots_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a product lot by ID. Args: id: ID (required)."""
    return await get_client().productlots_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def productlots_create(ref: str, fk_product: int, batch: str, qty: float = 0.0, warehouse_id: int = 0, price: float = 0.0, datem: str = "", eatby: str = "", sellby: str = "", note_public: str = "", note_private: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a product lot. Args: ref: Reference (required). fk_product: Product ID (required). batch: Batch (required)."""
    params = CreateProductLotParam(ref=ref, fk_product=fk_product, batch=batch, qty=qty, warehouse_id=warehouse_id, price=price, datem=datem, eatby=eatby, sellby=sellby, note_public=note_public, note_private=note_private)
    return await get_client().productlots_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def productlots_update(id: int, ref: Optional[str] = None, fk_product: Optional[int] = None, batch: Optional[str] = None, qty: Optional[float] = None, warehouse_id: Optional[int] = None, price: Optional[float] = None, datem: Optional[str] = None, eatby: Optional[str] = None, sellby: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a product lot. Args: id: ID (required)."""
    payload = {k: v for k, v in {"ref": ref, "fk_product": fk_product, "batch": batch, "qty": qty, "warehouse_id": warehouse_id, "price": price, "datem": datem, "eatby": eatby, "sellby": sellby, "note_public": note_public, "note_private": note_private}.items() if v is not None}
    return await get_client().productlots_update(id, payload, get_user_token())

@mcp.tool()
async def productlots_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a product lot. Args: id: ID (required)."""
    return await get_client().productlots_delete(id, get_user_token())

# ============================================================
# Proposals
# ============================================================
@mcp.tool()
async def proposals_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List commercial proposals (quotes)."""
    data = await get_client().proposals_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def proposals_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a proposal by ID. Args: id: ID (required)."""
    return await get_client().proposals_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def proposals_create(socid: int, date: str, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, multicurrency_code: str = "", payment_terms: int = 0, delivery_date: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a proposal. Args: socid: Third party ID (required). date: Date (ISO 8601 with offset) (required)."""
    payload = {k: _normalize_datetime(v) if isinstance(v, str) else v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code, "payment_terms": payment_terms, "delivery_date": delivery_date}.items()}
    return await get_client().proposals_create(payload, get_user_token())

@mcp.tool()
async def proposals_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, multicurrency_code: Optional[str] = None, payment_terms: Optional[int] = None, delivery_date: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a proposal. Args: id: ID (required)."""
    payload = {k: v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code, "payment_terms": payment_terms, "delivery_date": delivery_date}.items() if v is not None}
    return await get_client().proposals_update(id, payload, get_user_token())

@mcp.tool()
async def proposals_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a proposal. Args: id: ID (required)."""
    return await get_client().proposals_delete(id, get_user_token())

@mcp.tool()
async def proposals_get_lines(id: int, sqlfilters: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get lines for a proposal. Args: id: ID (required)."""
    data = await get_client().proposals_get_lines(id, get_user_token(), sqlfilters=sqlfilters)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def proposals_create_line(id: int, desc: str, qty: float, subprice: float, product_id: int = 0, tva_tx: float = 0.0, remise_percent: float = 0.0, remise: float = 0.0, price_base_type: str = "HT", date_start: str = "", date_end: str = "", product_type: int = 0, rang: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a line on a proposal. Args: id: Proposal ID (required). desc: Description (required). qty: Quantity (required). subprice: Unit price (required)."""
    params = CreateProposalLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, remise_percent=remise_percent, remise=remise, price_base_type=price_base_type, date_start=date_start, date_end=date_end, product_type=product_type, rang=rang)
    return await get_client().proposals_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def proposals_update_line(id: int, lineid: int, desc: Optional[str] = None, qty: Optional[float] = None, subprice: Optional[float] = None, product_id: Optional[int] = None, tva_tx: Optional[float] = None, remise_percent: Optional[float] = None, remise: Optional[float] = None, price_base_type: Optional[str] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, product_type: Optional[int] = None, rang: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a proposal line. Args: id: ID (required). lineid: Line ID (required)."""
    payload = {k: v for k, v in {"desc": desc, "qty": qty, "subprice": subprice, "product_id": product_id, "tva_tx": tva_tx, "remise_percent": remise_percent, "remise": remise, "price_base_type": price_base_type, "date_start": date_start, "date_end": date_end, "product_type": product_type, "rang": rang}.items() if v is not None}
    return await get_client().proposals_update_line(id, lineid, payload, get_user_token())

@mcp.tool()
async def proposals_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a line from a proposal. Args: id: ID (required). lineid: Line ID (required)."""
    return await get_client().proposals_delete_line(id, lineid, get_user_token())

@mcp.tool()
async def proposals_settodraft(id: int, ctx: Context = None) -> dict[str, Any]:
    """Set a proposal to draft. Args: id: ID (required)."""
    return await get_client().proposals_settodraft(id, get_user_token())

@mcp.tool()
async def proposals_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a proposal. Args: id: ID (required)."""
    return await get_client().proposals_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def proposals_close(id: int, status: int, note_private: str = "", note_public: str = "", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Close a proposal. Args: id: ID (required). status: Status (required)."""
    return await get_client().proposals_close(id, get_user_token(), status=status, note_private=note_private, note_public=note_public, notrigger=notrigger)

@mcp.tool()
async def proposals_setinvoiced(id: int, ctx: Context = None) -> dict[str, Any]:
    """Mark a proposal as invoiced. Args: id: ID (required)."""
    return await get_client().proposals_setinvoiced(id, get_user_token())

@mcp.tool()
async def proposals_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get contacts for a proposal. Args: id: ID (required)."""
    data = await get_client().proposals_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def proposals_add_contact(id: int, contactid: int, type: str, source: str = "external", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add a contact to a proposal. Args: id: ID (required). contactid: Contact ID (required). type: Contact type (required)."""
    return await get_client().proposals_add_contact(id, contactid, type, get_user_token(), source=source, notrigger=notrigger)

# ============================================================
# Orders
# ============================================================
@mcp.tool()
async def orders_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List customer orders."""
    data = await get_client().orders_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def orders_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get an order by ID. Args: id: ID (required)."""
    return await get_client().orders_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def orders_create(socid: int, date: str, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, multicurrency_code: str = "", payment_terms: int = 0, delivery_date: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create an order. Args: socid: Third party ID (required). date: Date (ISO 8601 with offset) (required)."""
    payload = {k: _normalize_datetime(v) if isinstance(v, str) else v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code, "payment_terms": payment_terms, "delivery_date": delivery_date}.items()}
    return await get_client().orders_create(payload, get_user_token())

@mcp.tool()
async def orders_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, multicurrency_code: Optional[str] = None, payment_terms: Optional[int] = None, delivery_date: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an order. Args: id: ID (required)."""
    payload = {k: v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code, "payment_terms": payment_terms, "delivery_date": delivery_date}.items() if v is not None}
    return await get_client().orders_update(id, payload, get_user_token())

@mcp.tool()
async def orders_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an order. Args: id: ID (required)."""
    return await get_client().orders_delete(id, get_user_token())

@mcp.tool()
async def orders_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get lines for an order. Args: id: ID (required)."""
    data = await get_client().orders_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def orders_get_line(id: int, lineid: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a single order line. Args: id: Order ID (required). lineid: Line ID (required)."""
    return await get_client().orders_get_line(id, lineid, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def orders_create_line(id: int, desc: str, qty: float, subprice: float, product_id: int = 0, tva_tx: float = 0.0, remise_percent: float = 0.0, price_base_type: str = "HT", date_start: str = "", date_end: str = "", product_type: int = 0, rang: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create an order line. Args: id: ID (required). desc: Desc (required). qty: Qty (required). subprice: Price (required)."""
    params = CreateOrderLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, remise_percent=remise_percent, price_base_type=price_base_type, date_start=date_start, date_end=date_end, product_type=product_type, rang=rang)
    return await get_client().orders_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def orders_update_line(id: int, lineid: int, desc: Optional[str] = None, qty: Optional[float] = None, subprice: Optional[float] = None, product_id: Optional[int] = None, tva_tx: Optional[float] = None, remise_percent: Optional[float] = None, price_base_type: Optional[str] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, product_type: Optional[int] = None, rang: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an order line. Args: id: ID (required). lineid: Line ID (required)."""
    payload = {k: v for k, v in {"desc": desc, "qty": qty, "subprice": subprice, "product_id": product_id, "tva_tx": tva_tx, "remise_percent": remise_percent, "price_base_type": price_base_type, "date_start": date_start, "date_end": date_end, "product_type": product_type, "rang": rang}.items() if v is not None}
    return await get_client().orders_update_line(id, lineid, payload, get_user_token())

@mcp.tool()
async def orders_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an order line. Args: id: ID (required). lineid: Line ID (required)."""
    return await get_client().orders_delete_line(id, lineid, get_user_token())

@mcp.tool()
async def orders_settodraft(id: int, idwarehouse: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Set order to draft. Args: id: ID (required)."""
    return await get_client().orders_settodraft(id, get_user_token(), idwarehouse=idwarehouse)

@mcp.tool()
async def orders_validate(id: int, idwarehouse: int = 0, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate an order. Args: id: ID (required)."""
    return await get_client().orders_validate(id, get_user_token(), idwarehouse=idwarehouse, notrigger=notrigger)

@mcp.tool()
async def orders_close(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Close an order. Args: id: ID (required)."""
    return await get_client().orders_close(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def orders_reopen(id: int, ctx: Context = None) -> dict[str, Any]:
    """Reopen an order. Args: id: ID (required)."""
    return await get_client().orders_reopen(id, get_user_token())

@mcp.tool()
async def orders_setinvoiced(id: int, ctx: Context = None) -> dict[str, Any]:
    """Mark order as invoiced. Args: id: ID (required)."""
    return await get_client().orders_setinvoiced(id, get_user_token())

@mcp.tool()
async def orders_create_from_proposal(proposalid: int, ctx: Context = None) -> dict[str, Any]:
    """Create order from proposal. Args: proposalid: Proposal ID (required)."""
    return await get_client().orders_create_from_proposal(proposalid, get_user_token())

@mcp.tool()
async def orders_get_shipments(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get shipments for an order. Args: id: ID (required)."""
    data = await get_client().orders_get_shipments(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def orders_create_shipment(id: int, warehouse_id: int, ctx: Context = None) -> dict[str, Any]:
    """Create a shipment from an order. Args: id: ID (required). warehouse_id: Warehouse ID (required)."""
    return await get_client().orders_create_shipment(id, warehouse_id, get_user_token())

@mcp.tool()
async def orders_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get contacts for an order. Args: id: ID (required)."""
    data = await get_client().orders_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

# ============================================================
# Invoices
# ============================================================
@mcp.tool()
async def invoices_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", status: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List customer invoices."""
    data = await get_client().invoices_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, status=status, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def invoices_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get an invoice by ID. Args: id: ID (required)."""
    return await get_client().invoices_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def invoices_create(socid: int, date: str, type: int, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, multicurrency_code: str = "", payment_terms: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create an invoice. Args: socid: Third party ID (required). date: Date (ISO 8601 with offset) (required). type: Type (0=standard, 1=credit, 2=deposit) (required)."""
    payload = {k: _normalize_datetime(v) if isinstance(v, str) else v for k, v in {"socid": socid, "date": date, "type": type, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code, "payment_terms": payment_terms}.items()}
    return await get_client().invoices_create(payload, get_user_token())

@mcp.tool()
async def invoices_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, type: Optional[int] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, multicurrency_code: Optional[str] = None, payment_terms: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an invoice. Args: id: ID (required)."""
    payload = {k: v for k, v in {"socid": socid, "date": date, "type": type, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code, "payment_terms": payment_terms}.items() if v is not None}
    return await get_client().invoices_update(id, payload, get_user_token())

@mcp.tool()
async def invoices_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an invoice. Args: id: ID (required)."""
    return await get_client().invoices_delete(id, get_user_token())

@mcp.tool()
async def invoices_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get invoice lines. Args: id: ID (required)."""
    data = await get_client().invoices_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def invoices_create_line(id: int, desc: str, qty: float, subprice: float, product_id: int = 0, tva_tx: float = 0.0, remise_percent: float = 0.0, price_base_type: str = "HT", date_start: str = "", date_end: str = "", product_type: int = 0, rang: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create an invoice line. Args: id: ID (required). desc: Desc (required). qty: Qty (required). subprice: Price (required)."""
    params = CreateInvoiceLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, remise_percent=remise_percent, price_base_type=price_base_type, date_start=date_start, date_end=date_end, product_type=product_type, rang=rang)
    return await get_client().invoices_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def invoices_update_line(id: int, lineid: int, desc: Optional[str] = None, qty: Optional[float] = None, subprice: Optional[float] = None, product_id: Optional[int] = None, tva_tx: Optional[float] = None, remise_percent: Optional[float] = None, price_base_type: Optional[str] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, product_type: Optional[int] = None, rang: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an invoice line. Args: id: ID (required). lineid: Line ID (required)."""
    payload = {k: v for k, v in {"desc": desc, "qty": qty, "subprice": subprice, "product_id": product_id, "tva_tx": tva_tx, "remise_percent": remise_percent, "price_base_type": price_base_type, "date_start": date_start, "date_end": date_end, "product_type": product_type, "rang": rang}.items() if v is not None}
    return await get_client().invoices_update_line(id, lineid, payload, get_user_token())

@mcp.tool()
async def invoices_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an invoice line. Args: id: ID (required). lineid: Line ID (required)."""
    return await get_client().invoices_delete_line(id, lineid, get_user_token())

@mcp.tool()
async def invoices_create_from_order(orderid: int, ctx: Context = None) -> dict[str, Any]:
    """Create invoice from order. Args: orderid: Order ID (required)."""
    return await get_client().invoices_create_from_order(orderid, get_user_token())

@mcp.tool()
async def invoices_settodraft(id: int, ctx: Context = None) -> dict[str, Any]:
    """Set invoice to draft. Args: id: ID (required)."""
    return await get_client().invoices_settodraft(id, get_user_token())

@mcp.tool()
async def invoices_validate(id: int, force_number: int = 0, idwarehouse: int = 0, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate an invoice. Args: id: ID (required)."""
    return await get_client().invoices_validate(id, get_user_token(), force_number=force_number, idwarehouse=idwarehouse, notrigger=notrigger)

@mcp.tool()
async def invoices_settopaid(id: int, close_code: str = "", close_note: str = "", ctx: Context = None) -> dict[str, Any]:
    """Mark invoice as paid. Args: id: ID (required)."""
    return await get_client().invoices_settopaid(id, get_user_token(), close_code=close_code, close_note=close_note)

@mcp.tool()
async def invoices_settounpaid(id: int, ctx: Context = None) -> dict[str, Any]:
    """Mark invoice as unpaid. Args: id: ID (required)."""
    return await get_client().invoices_settounpaid(id, get_user_token())

@mcp.tool()
async def invoices_get_payments(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get invoice payments. Args: id: ID (required)."""
    data = await get_client().invoices_get_payments(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def invoices_add_payment(id: int, datepaye: str, paymentid: int, accountid: int, closepaidinvoices: int = 0, num_payment: str = "", comment: str = "", chqemetteur: str = "", chqbank: str = "", ctx: Context = None) -> dict[str, Any]:
    """Add payment to invoice. Args: id: ID (required). datepaye: Payment date (required). paymentid: Payment type (required). accountid: Account ID (required)."""
    params = CreateInvoicePaymentParam(datepaye=datepaye, paymentid=paymentid, accountid=accountid, closepaidinvoices=closepaidinvoices, num_payment=num_payment, comment=comment, chqemetteur=chqemetteur, chqbank=chqbank)
    return await get_client().invoices_add_payment(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def invoices_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get invoice contacts. Args: id: ID (required)."""
    data = await get_client().invoices_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def invoices_add_contact(id: int, fk_socpeople: int, type_contact: str, source: str = "external", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add contact to invoice. Args: id: ID (required). fk_socpeople: Contact ID (required). type_contact: Type (required)."""
    params = CreateInvoiceContactParam(fk_socpeople=fk_socpeople, type_contact=type_contact, source=source, notrigger=notrigger)
    return await get_client().invoices_add_contact(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def invoices_delete_contact(id: int, contactid: int, type: str, ctx: Context = None) -> dict[str, Any]:
    """Delete contact from invoice. Args: id: ID (required). contactid: Contact ID (required). type: Type (required)."""
    return await get_client().invoices_delete_contact(id, contactid, type, get_user_token())

@mcp.tool()
async def invoices_get_discount(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get discount for invoice. Args: id: ID (required)."""
    return await get_client().invoices_get_discount(id, get_user_token())

@mcp.tool()
async def invoices_use_discount(id: int, discountid: int, ctx: Context = None) -> dict[str, Any]:
    """Apply discount to invoice. Args: id: ID (required). discountid: Discount ID (required)."""
    return await get_client().invoices_use_discount(id, discountid, get_user_token())

# ============================================================
# Payments
# ============================================================
@mcp.tool()
async def payments_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List payments."""
    data = await get_client().payments_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def payments_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a payment by ID. Args: id: ID (required)."""
    return await get_client().payments_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def payments_update(id: int, ctx: Context = None) -> dict[str, Any]:
    """Update a payment. Args: id: ID (required)."""
    return await get_client().payments_update(id, {}, get_user_token())

@mcp.tool()
async def payments_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a payment. Args: id: ID (required)."""
    return await get_client().payments_delete(id, get_user_token())

# ============================================================
# Bank Accounts
# ============================================================
@mcp.tool()
async def bankaccounts_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, category: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List bank accounts."""
    data = await get_client().bankaccounts_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, category=category, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def bankaccounts_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a bank account by ID."""
    return await get_client().bankaccounts_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def bankaccounts_create(ref: str, label: str, type: int, currency_code: str, account_number: str = "", country_id: int = 0, bank: str = "", code_banque: str = "", code_guichet: str = "", cle_rib: str = "", bic: str = "", iban: str = "", domiciliation: str = "", state_id: int = 0, opening_balance: float = 0.0, min_balance: float = 0.0, proprio: str = "", note_public: str = "", note_private: str = "", status: int = 1, ctx: Context = None) -> dict[str, Any]:
    """Create a bank account. Args: ref: Ref (required). label: Label (required). type: Type (required). currency_code: Currency (required)."""
    params = CreateBankAccountParam(ref=ref, label=label, type=type, currency_code=currency_code, account_number=account_number, country_id=country_id, bank=bank, code_banque=code_banque, code_guichet=code_guichet, cle_rib=cle_rib, bic=bic, iban=iban, domiciliation=domiciliation, state_id=state_id, opening_balance=opening_balance, min_balance=min_balance, proprio=proprio, note_public=note_public, note_private=note_private, status=status)
    return await get_client().bankaccounts_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def bankaccounts_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, type: Optional[int] = None, currency_code: Optional[str] = None, account_number: Optional[str] = None, bank: Optional[str] = None, code_banque: Optional[str] = None, code_guichet: Optional[str] = None, cle_rib: Optional[str] = None, bic: Optional[str] = None, iban: Optional[str] = None, domiciliation: Optional[str] = None, state_id: Optional[int] = None, opening_balance: Optional[float] = None, min_balance: Optional[float] = None, proprio: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, status: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a bank account. Args: id: ID (required)."""
    payload = {k: v for k, v in {"ref": ref, "label": label, "type": type, "currency_code": currency_code, "account_number": account_number, "bank": bank, "code_banque": code_banque, "code_guichet": code_guichet, "cle_rib": cle_rib, "bic": bic, "iban": iban, "domiciliation": domiciliation, "state_id": state_id, "opening_balance": opening_balance, "min_balance": min_balance, "proprio": proprio, "note_public": note_public, "note_private": note_private, "status": status}.items() if v is not None}
    return await get_client().bankaccounts_update(id, payload, get_user_token())

@mcp.tool()
async def bankaccounts_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a bank account. Args: id: ID (required)."""
    return await get_client().bankaccounts_delete(id, get_user_token())

@mcp.tool()
async def bankaccounts_transfer(bankaccount_from_id: int, bankaccount_to_id: int, date: str, description: str, amount: float, amount_to: float = 0.0, cheque_number: str = "", ctx: Context = None) -> dict[str, Any]:
    """Transfer funds between accounts. Args: bankaccount_from_id: Source (required). bankaccount_to_id: Target (required). date: Date (required). description: Desc (required). amount: Amount (required)."""
    params = CreateBankAccountTransferParam(bankaccount_from_id=bankaccount_from_id, bankaccount_to_id=bankaccount_to_id, date=date, description=description, amount=amount, amount_to=amount_to, cheque_number=cheque_number)
    return await get_client().bankaccounts_transfer(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def bankaccounts_get_lines(id: int, sqlfilters: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get bank account lines. Args: id: ID (required)."""
    data = await get_client().bankaccounts_get_lines(id, get_user_token(), sqlfilters=sqlfilters)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def bankaccounts_create_line(id: int, date: str, type: str, label: str, amount: float, category: int = 0, cheque_number: str = "", cheque_writer: str = "", cheque_bank: str = "", accountancycode: str = "", datev: str = "", num_releve: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a bank account line. Args: id: ID (required). date: Date (required). type: Type (required). label: Label (required). amount: Amount (required)."""
    params = CreateBankAccountLineParam(date=date, type=type, label=label, amount=amount, category=category, cheque_number=cheque_number, cheque_writer=cheque_writer, cheque_bank=cheque_bank, accountancycode=accountancycode, datev=datev, num_releve=num_releve)
    return await get_client().bankaccounts_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def bankaccounts_get_line(line_id: int, ctx: Context = None) -> dict[str, Any]:
    """Get a bank account line. Args: line_id: Line ID (required)."""
    return await get_client().bankaccounts_get_line(line_id, get_user_token())

@mcp.tool()
async def bankaccounts_update_line(id: int, line_id: int, label: str, ctx: Context = None) -> dict[str, Any]:
    """Update a bank account line. Args: id: ID (required). line_id: Line ID (required). label: Label (required)."""
    return await get_client().bankaccounts_update_line(id, line_id, label, get_user_token())

@mcp.tool()
async def bankaccounts_delete_line(id: int, line_id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a bank account line. Args: id: ID (required). line_id: Line ID (required)."""
    return await get_client().bankaccounts_delete_line(id, line_id, get_user_token())

@mcp.tool()
async def bankaccounts_get_balance(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get bank account balance. Args: id: ID (required)."""
    return await get_client().bankaccounts_get_balance(id, get_user_token())

# ============================================================
# Supplier Orders
# ============================================================
@mcp.tool()
async def supplier_orders_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", product_ids: str = "", status: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List supplier orders."""
    data = await get_client().supplier_orders_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, product_ids=product_ids, status=status, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def supplier_orders_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a supplier order by ID."""
    return await get_client().supplier_orders_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def supplier_orders_create(socid: int, date: str, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, multicurrency_code: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a supplier order. Args: socid: Supplier ID (required). date: Date (ISO 8601 with offset) (required)."""
    payload = {k: _normalize_datetime(v) if isinstance(v, str) else v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code}.items()}
    return await get_client().supplier_orders_create(payload, get_user_token())

@mcp.tool()
async def supplier_orders_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, multicurrency_code: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a supplier order. Args: id: ID (required)."""
    payload = {k: v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code}.items() if v is not None}
    return await get_client().supplier_orders_update(id, payload, get_user_token())

@mcp.tool()
async def supplier_orders_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a supplier order."""
    return await get_client().supplier_orders_delete(id, get_user_token())

@mcp.tool()
async def supplier_orders_create_line(id: int, desc: str, qty: float, subprice: float, product_id: int = 0, tva_tx: float = 0.0, remise_percent: float = 0.0, price_base_type: str = "HT", date_start: str = "", date_end: str = "", product_type: int = 0, rang: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create supplier order line. Args: id: ID (required). desc: Desc (required). qty: Qty (required). subprice: Price (required)."""
    params = CreateSupplierOrderLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, remise_percent=remise_percent, price_base_type=price_base_type, date_start=date_start, date_end=date_end, product_type=product_type, rang=rang)
    return await get_client().supplier_orders_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def supplier_orders_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get supplier order contacts."""
    data = await get_client().supplier_orders_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def supplier_orders_add_contact(id: int, contactid: int, type: str, source: str, ctx: Context = None) -> dict[str, Any]:
    """Add contact to supplier order. Args: id: ID (required). contactid: ID (required). type: Type (required). source: Source (required)."""
    return await get_client().supplier_orders_add_contact(id, contactid, type, source, get_user_token())

@mcp.tool()
async def supplier_orders_delete_contact(id: int, contactid: int, type: str, source: str, ctx: Context = None) -> dict[str, Any]:
    """Delete contact from supplier order. Args: id: ID (required). contactid: ID (required). type: Type (required). source: Source (required)."""
    return await get_client().supplier_orders_delete_contact(id, contactid, type, source, get_user_token())

@mcp.tool()
async def supplier_orders_validate(id: int, idwarehouse: int = 0, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a supplier order."""
    return await get_client().supplier_orders_validate(id, get_user_token(), idwarehouse=idwarehouse, notrigger=notrigger)

@mcp.tool()
async def supplier_orders_approve(id: int, idwarehouse: int = 0, secondlevel: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Approve a supplier order."""
    return await get_client().supplier_orders_approve(id, get_user_token(), idwarehouse=idwarehouse, secondlevel=secondlevel)

@mcp.tool()
async def supplier_orders_receive(id: int, closeopenorder: int = 0, comment: str = "", ctx: Context = None) -> dict[str, Any]:
    """Receive goods for a supplier order."""
    return await get_client().supplier_orders_receive(id, get_user_token(), closeopenorder=closeopenorder, comment=comment)

# ============================================================
# Supplier Invoices
# ============================================================
@mcp.tool()
async def supplier_invoices_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", status: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List supplier invoices."""
    data = await get_client().supplier_invoices_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, status=status, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def supplier_invoices_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a supplier invoice by ID."""
    return await get_client().supplier_invoices_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def supplier_invoices_create(socid: int, date: str, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, multicurrency_code: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a supplier invoice. Args: socid: Supplier ID (required). date: Date (ISO 8601 with offset) (required)."""
    payload = {k: _normalize_datetime(v) if isinstance(v, str) else v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code}.items()}
    return await get_client().supplier_invoices_create(payload, get_user_token())

@mcp.tool()
async def supplier_invoices_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, multicurrency_code: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a supplier invoice."""
    payload = {k: v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "multicurrency_code": multicurrency_code}.items() if v is not None}
    return await get_client().supplier_invoices_update(id, payload, get_user_token())

@mcp.tool()
async def supplier_invoices_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a supplier invoice."""
    return await get_client().supplier_invoices_delete(id, get_user_token())

@mcp.tool()
async def supplier_invoices_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get supplier invoice lines."""
    data = await get_client().supplier_invoices_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def supplier_invoices_create_line(id: int, desc: str, qty: float, subprice: float, product_id: int = 0, tva_tx: float = 0.0, remise_percent: float = 0.0, price_base_type: str = "HT", ctx: Context = None) -> dict[str, Any]:
    """Create supplier invoice line. Args: id: ID (required). desc: Desc (required). qty: Qty (required). subprice: Price (required)."""
    params = CreateSupplierInvoiceLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, remise_percent=remise_percent, price_base_type=price_base_type)
    return await get_client().supplier_invoices_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def supplier_invoices_update_line(id: int, lineid: int, desc: Optional[str] = None, qty: Optional[float] = None, subprice: Optional[float] = None, product_id: Optional[int] = None, tva_tx: Optional[float] = None, remise_percent: Optional[float] = None, price_base_type: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update supplier invoice line."""
    payload = {k: v for k, v in {"desc": desc, "qty": qty, "subprice": subprice, "product_id": product_id, "tva_tx": tva_tx, "remise_percent": remise_percent, "price_base_type": price_base_type}.items() if v is not None}
    return await get_client().supplier_invoices_update_line(id, lineid, payload, get_user_token())

@mcp.tool()
async def supplier_invoices_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete supplier invoice line."""
    return await get_client().supplier_invoices_delete_line(id, lineid, get_user_token())

@mcp.tool()
async def supplier_invoices_validate(id: int, idwarehouse: int = 0, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a supplier invoice."""
    return await get_client().supplier_invoices_validate(id, get_user_token(), idwarehouse=idwarehouse, notrigger=notrigger)

@mcp.tool()
async def supplier_invoices_settopaid(id: int, close_code: str = "", close_note: str = "", ctx: Context = None) -> dict[str, Any]:
    """Mark supplier invoice as paid."""
    return await get_client().supplier_invoices_settopaid(id, get_user_token(), close_code=close_code, close_note=close_note)

@mcp.tool()
async def supplier_invoices_get_payments(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get supplier invoice payments."""
    data = await get_client().supplier_invoices_get_payments(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def supplier_invoices_add_payment(id: int, datepaye: str, payment_mode_id: int, accountid: int, closepaidinvoices: int = 0, num_payment: str = "", comment: str = "", amount: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Add payment to supplier invoice. Args: id: ID (required). datepaye: Date (required). payment_mode_id: Mode (required). accountid: Account (required)."""
    params = CreateSupplierInvoicePaymentParam(datepaye=datepaye, payment_mode_id=payment_mode_id, accountid=accountid, closepaidinvoices=closepaidinvoices, num_payment=num_payment, comment=comment, amount=amount)
    return await get_client().supplier_invoices_add_payment(id, params.model_dump(exclude_unset=True), get_user_token())

# ============================================================
# Supplier Proposals
# ============================================================
@mcp.tool()
async def supplier_proposals_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List supplier proposals."""
    data = await get_client().supplier_proposals_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def supplier_proposals_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a supplier proposal by ID."""
    return await get_client().supplier_proposals_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def supplier_proposals_create(socid: int, date: str, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Create a supplier proposal. Args: socid: Supplier ID (required). date: Date (required)."""
    payload = {k: _normalize_datetime(v) if isinstance(v, str) else v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc}.items()}
    return await get_client().supplier_proposals_create(payload, get_user_token())

@mcp.tool()
async def supplier_proposals_update(id: int, socid: Optional[int] = None, date: Optional[str] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a supplier proposal."""
    payload = {k: v for k, v in {"socid": socid, "date": date, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc}.items() if v is not None}
    return await get_client().supplier_proposals_update(id, payload, get_user_token())

@mcp.tool()
async def supplier_proposals_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a supplier proposal."""
    return await get_client().supplier_proposals_delete(id, get_user_token())

# ============================================================
# Contracts
# ============================================================
@mcp.tool()
async def contracts_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List contracts."""
    data = await get_client().contracts_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def contracts_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a contract by ID."""
    return await get_client().contracts_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def contracts_create(socid: int, ref: str, date_contrat: str, status: int = 0, note_public: str = "", note_private: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a contract. Args: socid: Third party ID (required). ref: Reference (required). date_contrat: Contract date (required)."""
    params = CreateContractParam(socid=socid, ref=ref, date_contrat=date_contrat, status=status, note_public=note_public, note_private=note_private)
    return await get_client().contracts_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def contracts_update(id: int, socid: Optional[int] = None, ref: Optional[str] = None, date_contrat: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a contract."""
    payload = {k: v for k, v in {"socid": socid, "ref": ref, "date_contrat": date_contrat, "status": status, "note_public": note_public, "note_private": note_private}.items() if v is not None}
    return await get_client().contracts_update(id, payload, get_user_token())

@mcp.tool()
async def contracts_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a contract."""
    return await get_client().contracts_delete(id, get_user_token())

@mcp.tool()
async def contracts_get_lines(id: int, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get contract lines."""
    data = await get_client().contracts_get_lines(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def contracts_create_line(id: int, desc: str = "", qty: float = 0.0, subprice: float = 0.0, product_id: int = 0, tva_tx: float = 0.0, date_start: str = "", date_end: str = "", remise_percent: float = 0.0, price_base_type: str = "HT", ctx: Context = None) -> dict[str, Any]:
    """Create a contract line."""
    params = CreateContractLineParam(desc=desc, qty=qty, subprice=subprice, product_id=product_id, tva_tx=tva_tx, date_start=date_start, date_end=date_end, remise_percent=remise_percent, price_base_type=price_base_type)
    return await get_client().contracts_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def contracts_update_line(id: int, lineid: int, desc: Optional[str] = None, qty: Optional[float] = None, subprice: Optional[float] = None, product_id: Optional[int] = None, tva_tx: Optional[float] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, remise_percent: Optional[float] = None, price_base_type: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a contract line."""
    payload = {k: v for k, v in {"desc": desc, "qty": qty, "subprice": subprice, "product_id": product_id, "tva_tx": tva_tx, "date_start": date_start, "date_end": date_end, "remise_percent": remise_percent, "price_base_type": price_base_type}.items() if v is not None}
    return await get_client().contracts_update_line(id, lineid, payload, get_user_token())

@mcp.tool()
async def contracts_activate_line(id: int, lineid: int, datestart: str, dateend: str = "", comment: str = "", ctx: Context = None) -> dict[str, Any]:
    """Activate a contract line. Args: id: ID (required). lineid: Line ID (required). datestart: Start date (required)."""
    params = CreateContractActivateLineParam(datestart=datestart, dateend=dateend, comment=comment)
    return await get_client().contracts_activate_line(id, lineid, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def contracts_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a contract line."""
    return await get_client().contracts_delete_line(id, lineid, get_user_token())

@mcp.tool()
async def contracts_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a contract."""
    return await get_client().contracts_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def contracts_close(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Close a contract."""
    return await get_client().contracts_close(id, get_user_token(), notrigger=notrigger)

# ============================================================
# BOMs
# ============================================================
@mcp.tool()
async def boms_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List BOMs."""
    data = await get_client().boms_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def boms_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a BOM by ID."""
    return await get_client().boms_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def boms_create(ref: str, label: str, fk_product: int, qty: float, status: int = 0, description: str = "", note_public: str = "", note_private: str = "", duration: float = 0.0, efficiency: float = 0.0, warehouse_id: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a BOM. Args: ref: Reference (required). label: Label (required). fk_product: Product ID (required). qty: Quantity (required)."""
    params = CreateBomParam(ref=ref, label=label, fk_product=fk_product, qty=qty, status=status, description=description, note_public=note_public, note_private=note_private, duration=duration, efficiency=efficiency, warehouse_id=warehouse_id)
    return await get_client().boms_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def boms_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, fk_product: Optional[int] = None, qty: Optional[float] = None, status: Optional[int] = None, description: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, duration: Optional[float] = None, efficiency: Optional[float] = None, warehouse_id: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a BOM."""
    payload = {k: v for k, v in {"ref": ref, "label": label, "fk_product": fk_product, "qty": qty, "status": status, "description": description, "note_public": note_public, "note_private": note_private, "duration": duration, "efficiency": efficiency, "warehouse_id": warehouse_id}.items() if v is not None}
    return await get_client().boms_update(id, payload, get_user_token())

@mcp.tool()
async def boms_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a BOM."""
    return await get_client().boms_delete(id, get_user_token())

@mcp.tool()
async def boms_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get BOM lines."""
    data = await get_client().boms_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def boms_create_line(id: int, fk_product: int = 0, qty: float = 0.0, desc: str = "", warehouse_id: int = 0, position: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a BOM line."""
    params = CreateBomLineParam(fk_product=fk_product, qty=qty, desc=desc, warehouse_id=warehouse_id, position=position)
    return await get_client().boms_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def boms_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a BOM line."""
    return await get_client().boms_delete_line(id, lineid, get_user_token())

# ============================================================
# MOs (Manufacturing Orders)
# ============================================================
@mcp.tool()
async def mos_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List manufacturing orders."""
    data = await get_client().mos_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def mos_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a manufacturing order by ID."""
    return await get_client().mos_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def mos_create(ref: str, label: str, fk_product: int, qty: float, fk_warehouse: int, status: int = 0, note_public: str = "", note_private: str = "", date_planned: str = "", bom_id: int = 0, priority: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a manufacturing order. Args: ref: Ref (required). label: Label (required). fk_product: Product ID (required). qty: Qty (required). fk_warehouse: Warehouse ID (required)."""
    params = CreateMOParam(ref=ref, label=label, fk_product=fk_product, qty=qty, fk_warehouse=fk_warehouse, status=status, note_public=note_public, note_private=note_private, date_planned=date_planned, bom_id=bom_id, priority=priority)
    return await get_client().mos_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def mos_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, fk_product: Optional[int] = None, qty: Optional[float] = None, fk_warehouse: Optional[int] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, date_planned: Optional[str] = None, bom_id: Optional[int] = None, priority: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a manufacturing order."""
    payload = {k: v for k, v in {"ref": ref, "label": label, "fk_product": fk_product, "qty": qty, "fk_warehouse": fk_warehouse, "status": status, "note_public": note_public, "note_private": note_private, "date_planned": date_planned, "bom_id": bom_id, "priority": priority}.items() if v is not None}
    return await get_client().mos_update(id, payload, get_user_token())

@mcp.tool()
async def mos_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a manufacturing order."""
    return await get_client().mos_delete(id, get_user_token())

@mcp.tool()
async def mos_produce_and_consume(id: int, ctx: Context = None) -> dict[str, Any]:
    """Produce and consume for a manufacturing order."""
    return await get_client().mos_produce_and_consume(id, {}, get_user_token())

@mcp.tool()
async def mos_get_categories(id: int, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Get categories for a manufacturing order."""
    data = await get_client().mos_get_categories(id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page)
    return {"items": json_to_toon(data)}

# ============================================================
# Projects
# ============================================================
@mcp.tool()
async def projects_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", category: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List projects."""
    data = await get_client().projects_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, category=category, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def projects_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a project by ID."""
    return await get_client().projects_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def projects_create(ref: str, title: str, socid: int = 0, description: str = "", note_public: str = "", note_private: str = "", status: int = 0, date_start: str = "", date_end: str = "", budget_amount: float = 0.0, usage_opportunity: int = 0, usage_task: int = 0, usage_bill_time: int = 0, usage_organize_event: int = 0, public: int = 0, percent: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a project. Args: ref: Reference (required). title: Title (required)."""
    params = CreateProjectParam(ref=ref, title=title, socid=socid, description=description, note_public=note_public, note_private=note_private, status=status, date_start=date_start, date_end=date_end, budget_amount=budget_amount, usage_opportunity=usage_opportunity, usage_task=usage_task, usage_bill_time=usage_bill_time, usage_organize_event=usage_organize_event, public=public, percent=percent)
    return await get_client().projects_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def projects_update(id: int, ref: Optional[str] = None, title: Optional[str] = None, socid: Optional[int] = None, description: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, status: Optional[int] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, budget_amount: Optional[float] = None, usage_opportunity: Optional[int] = None, usage_task: Optional[int] = None, usage_bill_time: Optional[int] = None, usage_organize_event: Optional[int] = None, public: Optional[int] = None, percent: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a project."""
    payload = {k: v for k, v in {"ref": ref, "title": title, "socid": socid, "description": description, "note_public": note_public, "note_private": note_private, "status": status, "date_start": date_start, "date_end": date_end, "budget_amount": budget_amount, "usage_opportunity": usage_opportunity, "usage_task": usage_task, "usage_bill_time": usage_bill_time, "usage_organize_event": usage_organize_event, "public": public, "percent": percent}.items() if v is not None}
    return await get_client().projects_update(id, payload, get_user_token())

@mcp.tool()
async def projects_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a project."""
    return await get_client().projects_delete(id, get_user_token())

@mcp.tool()
async def projects_get_tasks(id: int, includetimespent: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Get project tasks."""
    data = await get_client().projects_get_tasks(id, get_user_token(), includetimespent=includetimespent)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def projects_create_task(id: int, ref: str, label: str, description: str = "", note_public: str = "", note_private: str = "", status: int = 0, date_start: str = "", date_end: str = "", planned_workload: float = 0.0, progress: int = 0, budget_amount: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Create a project task. Args: id: Project ID (required). ref: Ref (required). label: Label (required)."""
    params = CreateProjectTaskParam(ref=ref, label=label, description=description, note_public=note_public, note_private=note_private, status=status, date_start=date_start, date_end=date_end, planned_workload=planned_workload, progress=progress, budget_amount=budget_amount)
    return await get_client().projects_create_task(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def projects_get_timespent(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get timespent for a project."""
    data = await get_client().projects_get_timespent(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def projects_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a project."""
    return await get_client().projects_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def projects_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get project contacts."""
    data = await get_client().projects_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

# ============================================================
# Tasks
# ============================================================
@mcp.tool()
async def tasks_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List tasks."""
    data = await get_client().tasks_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def tasks_get(id: int, includetimespent: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a task by ID."""
    return await get_client().tasks_get(id, get_user_token(), includetimespent=includetimespent, include_all_fields=include_all_fields)

@mcp.tool()
async def tasks_create(ref: str, label: str, fk_project: int, description: str = "", note_public: str = "", note_private: str = "", status: int = 0, date_start: str = "", date_end: str = "", planned_workload: float = 0.0, progress: int = 0, budget_amount: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Create a task. Args: ref: Ref (required). label: Label (required). fk_project: Project ID (required)."""
    params = CreateTaskParam(ref=ref, label=label, fk_project=fk_project, description=description, note_public=note_public, note_private=note_private, status=status, date_start=date_start, date_end=date_end, planned_workload=planned_workload, progress=progress, budget_amount=budget_amount)
    return await get_client().tasks_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def tasks_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, fk_project: Optional[int] = None, description: Optional[str] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, status: Optional[int] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, planned_workload: Optional[float] = None, progress: Optional[int] = None, budget_amount: Optional[float] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a task."""
    payload = {k: v for k, v in {"ref": ref, "label": label, "fk_project": fk_project, "description": description, "note_public": note_public, "note_private": note_private, "status": status, "date_start": date_start, "date_end": date_end, "planned_workload": planned_workload, "progress": progress, "budget_amount": budget_amount}.items() if v is not None}
    return await get_client().tasks_update(id, payload, get_user_token())

@mcp.tool()
async def tasks_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a task."""
    return await get_client().tasks_delete(id, get_user_token())

@mcp.tool()
async def tasks_get_timespent(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get timespent for a task."""
    data = await get_client().tasks_get_timespent(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def tasks_add_timespent(id: int, date: str, duration: float, product_id: int = 0, user_id: int = 0, note: str = "", progress: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add timespent to a task. Args: id: Task ID (required). date: Date (required). duration: Duration (required)."""
    params = CreateTaskTimeSpentParam(date=date, duration=duration, product_id=product_id, user_id=user_id, note=note, progress=progress)
    return await get_client().tasks_add_timespent(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def tasks_update_timespent(id: int, timespent_id: int, date: Optional[str] = None, duration: Optional[float] = None, product_id: Optional[int] = None, user_id: Optional[int] = None, note: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update timespent entry. Args: id: Task ID (required). timespent_id: Timespent ID (required)."""
    payload = {k: v for k, v in {"date": date, "duration": duration, "product_id": product_id, "user_id": user_id, "note": note}.items() if v is not None}
    return await get_client().tasks_update_timespent(id, timespent_id, payload, get_user_token())

@mcp.tool()
async def tasks_delete_timespent(id: int, timespent_id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete timespent entry. Args: id: Task ID (required). timespent_id: Timespent ID (required)."""
    return await get_client().tasks_delete_timespent(id, timespent_id, get_user_token())

@mcp.tool()
async def tasks_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get task contacts."""
    data = await get_client().tasks_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

# ============================================================
# Shipments
# ============================================================
@mcp.tool()
async def shipments_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List shipments."""
    data = await get_client().shipments_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def shipments_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a shipment by ID."""
    return await get_client().shipments_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def shipments_create(socid: int, ref: str, status: int = 0, note_public: str = "", note_private: str = "", date_delivery: str = "", shipping_method_id: int = 0, warehouse_id: int = 0, total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, weight: float = 0.0, volume: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Create a shipment. Args: socid: Third party ID (required). ref: Reference (required)."""
    params = CreateShipmentParam(socid=socid, ref=ref, status=status, note_public=note_public, note_private=note_private, date_delivery=date_delivery, shipping_method_id=shipping_method_id, warehouse_id=warehouse_id, total_ht=total_ht, total_tva=total_tva, total_ttc=total_ttc, weight=weight, volume=volume)
    return await get_client().shipments_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def shipments_update(id: int, socid: Optional[int] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, date_delivery: Optional[str] = None, shipping_method_id: Optional[int] = None, warehouse_id: Optional[int] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, weight: Optional[float] = None, volume: Optional[float] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a shipment."""
    payload = {k: v for k, v in {"socid": socid, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "date_delivery": date_delivery, "shipping_method_id": shipping_method_id, "warehouse_id": warehouse_id, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "weight": weight, "volume": volume}.items() if v is not None}
    return await get_client().shipments_update(id, payload, get_user_token())

@mcp.tool()
async def shipments_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a shipment."""
    return await get_client().shipments_delete(id, get_user_token())

@mcp.tool()
async def shipments_create_from_order(orderid: int, ctx: Context = None) -> dict[str, Any]:
    """Create shipment from order."""
    return await get_client().shipments_create_from_order(orderid, get_user_token())

@mcp.tool()
async def shipments_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a shipment."""
    return await get_client().shipments_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def shipments_close(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Close a shipment."""
    return await get_client().shipments_close(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def shipments_setinvoiced(id: int, ctx: Context = None) -> dict[str, Any]:
    """Mark shipment as invoiced."""
    return await get_client().shipments_setinvoiced(id, get_user_token())

@mcp.tool()
async def shipments_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get shipment lines."""
    data = await get_client().shipments_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

# ============================================================
# Receptions
# ============================================================
@mcp.tool()
async def receptions_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List receptions."""
    data = await get_client().receptions_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def receptions_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a reception by ID."""
    return await get_client().receptions_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def receptions_create(socid: int, ref: str, status: int = 0, note_public: str = "", note_private: str = "", date_delivery: str = "", warehouse_id: int = 0, total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, ctx: Context = None) -> dict[str, Any]:
    """Create a reception. Args: socid: Supplier ID (required). ref: Ref (required)."""
    params = CreateReceptionParam(socid=socid, ref=ref, status=status, note_public=note_public, note_private=note_private, date_delivery=date_delivery, warehouse_id=warehouse_id, total_ht=total_ht, total_tva=total_tva, total_ttc=total_ttc)
    return await get_client().receptions_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def receptions_update(id: int, socid: Optional[int] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, date_delivery: Optional[str] = None, warehouse_id: Optional[int] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a reception."""
    payload = {k: v for k, v in {"socid": socid, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "date_delivery": date_delivery, "warehouse_id": warehouse_id, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc}.items() if v is not None}
    return await get_client().receptions_update(id, payload, get_user_token())

@mcp.tool()
async def receptions_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a reception."""
    return await get_client().receptions_delete(id, get_user_token())

@mcp.tool()
async def receptions_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a reception."""
    return await get_client().receptions_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def receptions_close(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Close a reception."""
    return await get_client().receptions_close(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def receptions_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get reception lines."""
    data = await get_client().receptions_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

# ============================================================
# Interventions
# ============================================================
@mcp.tool()
async def interventions_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List interventions."""
    data = await get_client().interventions_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, thirdparty_ids=thirdparty_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def interventions_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get an intervention by ID."""
    return await get_client().interventions_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def interventions_create(socid: int, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", date: str = "", description: str = "", fk_user_author: int = 0, fk_user_intervenant: int = 0, fk_project: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create an intervention. Args: socid: Third party ID (required)."""
    params = CreateInterventionParam(socid=socid, ref=ref, status=status, note_public=note_public, note_private=note_private, date=date, description=description, fk_user_author=fk_user_author, fk_user_intervenant=fk_user_intervenant, fk_project=fk_project)
    return await get_client().interventions_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def interventions_update(id: int, socid: Optional[int] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, date: Optional[str] = None, description: Optional[str] = None, fk_user_author: Optional[int] = None, fk_user_intervenant: Optional[int] = None, fk_project: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an intervention."""
    payload = {k: v for k, v in {"socid": socid, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "date": date, "description": description, "fk_user_author": fk_user_author, "fk_user_intervenant": fk_user_intervenant, "fk_project": fk_project}.items() if v is not None}
    return await get_client().interventions_update(id, payload, get_user_token())

@mcp.tool()
async def interventions_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an intervention."""
    return await get_client().interventions_delete(id, get_user_token())

@mcp.tool()
async def interventions_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get intervention lines."""
    data = await get_client().interventions_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def interventions_create_line(id: int, desc: str = "", duration: float = 0.0, product_id: int = 0, qty: float = 0.0, subprice: float = 0.0, tva_tx: float = 0.0, date: str = "", price_base_type: str = "HT", rang: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create an intervention line."""
    params = CreateInterventionLineParam(desc=desc, duration=duration, product_id=product_id, qty=qty, subprice=subprice, tva_tx=tva_tx, date=date, price_base_type=price_base_type, rang=rang)
    return await get_client().interventions_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def interventions_update_line(id: int, lineid: int, desc: Optional[str] = None, duration: Optional[float] = None, product_id: Optional[int] = None, qty: Optional[float] = None, subprice: Optional[float] = None, tva_tx: Optional[float] = None, date: Optional[str] = None, price_base_type: Optional[str] = None, rang: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an intervention line."""
    payload = {k: v for k, v in {"desc": desc, "duration": duration, "product_id": product_id, "qty": qty, "subprice": subprice, "tva_tx": tva_tx, "date": date, "price_base_type": price_base_type, "rang": rang}.items() if v is not None}
    return await get_client().interventions_update_line(id, lineid, payload, get_user_token())

@mcp.tool()
async def interventions_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an intervention line."""
    return await get_client().interventions_delete_line(id, lineid, get_user_token())

@mcp.tool()
async def interventions_settodraft(id: int, ctx: Context = None) -> dict[str, Any]:
    """Set intervention to draft."""
    return await get_client().interventions_settodraft(id, get_user_token())

@mcp.tool()
async def interventions_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate an intervention."""
    return await get_client().interventions_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def interventions_close(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Close an intervention."""
    return await get_client().interventions_close(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def interventions_get_contacts(id: int, type: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get intervention contacts."""
    data = await get_client().interventions_get_contacts(id, get_user_token(), type=type)
    return {"items": json_to_toon(data)}

# ============================================================
# Expense Reports
# ============================================================
@mcp.tool()
async def expense_reports_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List expense reports."""
    data = await get_client().expense_reports_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, user_ids=user_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def expense_reports_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get an expense report by ID."""
    return await get_client().expense_reports_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def expense_reports_create(fk_user: int, date_debut: str, date_fin: str, fk_user_author: int, ref: str = "", status: int = 0, note_public: str = "", note_private: str = "", total_ht: float = 0.0, total_tva: float = 0.0, total_ttc: float = 0.0, fk_project: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create an expense report. Args: fk_user: User ID (required). date_debut: Start date (required). date_fin: End date (required). fk_user_author: Author user ID (required)."""
    payload = {k: _normalize_datetime(v) if isinstance(v, str) else v for k, v in {"fk_user": fk_user, "date_debut": date_debut, "date_fin": date_fin, "fk_user_author": fk_user_author, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "fk_project": fk_project}.items()}
    return await get_client().expense_reports_create(payload, get_user_token())

@mcp.tool()
async def expense_reports_update(id: int, fk_user: Optional[int] = None, date_debut: Optional[str] = None, date_fin: Optional[str] = None, fk_user_author: Optional[int] = None, ref: Optional[str] = None, status: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, total_ht: Optional[float] = None, total_tva: Optional[float] = None, total_ttc: Optional[float] = None, fk_project: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an expense report."""
    payload = {k: v for k, v in {"fk_user": fk_user, "date_debut": date_debut, "date_fin": date_fin, "fk_user_author": fk_user_author, "ref": ref, "status": status, "note_public": note_public, "note_private": note_private, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ttc, "fk_project": fk_project}.items() if v is not None}
    return await get_client().expense_reports_update(id, payload, get_user_token())

@mcp.tool()
async def expense_reports_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an expense report."""
    return await get_client().expense_reports_delete(id, get_user_token())

@mcp.tool()
async def expense_reports_get_lines(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get expense report lines."""
    data = await get_client().expense_reports_get_lines(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def expense_reports_create_line(id: int, date: str, fk_c_type_fees: int, qty: float, value_unit: float, product_id: int = 0, comment: str = "", tva_tx: float = 0.0, localtax1_tx: float = 0.0, localtax2_tx: float = 0.0, fk_project: int = 0, fk_soc: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create expense report line. Args: id: Report ID (required). date: Date (required). fk_c_type_fees: Fee type (required). qty: Qty (required). value_unit: Unit value (required)."""
    params = CreateExpenseReportLineParam(date=date, fk_c_type_fees=fk_c_type_fees, qty=qty, value_unit=value_unit, product_id=product_id, comment=comment, tva_tx=tva_tx, localtax1_tx=localtax1_tx, localtax2_tx=localtax2_tx, fk_project=fk_project, fk_soc=fk_soc)
    return await get_client().expense_reports_create_line(id, params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def expense_reports_update_line(id: int, lineid: int, date: Optional[str] = None, fk_c_type_fees: Optional[int] = None, qty: Optional[float] = None, value_unit: Optional[float] = None, product_id: Optional[int] = None, comment: Optional[str] = None, tva_tx: Optional[float] = None, localtax1_tx: Optional[float] = None, localtax2_tx: Optional[float] = None, fk_project: Optional[int] = None, fk_soc: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update expense report line."""
    payload = {k: v for k, v in {"date": date, "fk_c_type_fees": fk_c_type_fees, "qty": qty, "value_unit": value_unit, "product_id": product_id, "comment": comment, "tva_tx": tva_tx, "localtax1_tx": localtax1_tx, "localtax2_tx": localtax2_tx, "fk_project": fk_project, "fk_soc": fk_soc}.items() if v is not None}
    return await get_client().expense_reports_update_line(id, lineid, payload, get_user_token())

@mcp.tool()
async def expense_reports_delete_line(id: int, lineid: int, ctx: Context = None) -> dict[str, Any]:
    """Delete expense report line."""
    return await get_client().expense_reports_delete_line(id, lineid, get_user_token())

@mcp.tool()
async def expense_reports_settodraft(id: int, ctx: Context = None) -> dict[str, Any]:
    """Set expense report to draft."""
    return await get_client().expense_reports_settodraft(id, get_user_token())

@mcp.tool()
async def expense_reports_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate an expense report."""
    return await get_client().expense_reports_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def expense_reports_approve(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Approve an expense report."""
    return await get_client().expense_reports_approve(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def expense_reports_deny(id: int, details: str = "", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Deny an expense report."""
    return await get_client().expense_reports_deny(id, get_user_token(), details=details, notrigger=notrigger)

@mcp.tool()
async def expense_reports_setpaid(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Mark expense report as paid."""
    return await get_client().expense_reports_setpaid(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def expense_reports_cancel(id: int, detail: str = "", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Cancel an expense report."""
    return await get_client().expense_reports_cancel(id, get_user_token(), detail=detail, notrigger=notrigger)

# ============================================================
# Holidays
# ============================================================
@mcp.tool()
async def holidays_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List holidays."""
    data = await get_client().holidays_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, user_ids=user_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def holidays_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a holiday by ID."""
    return await get_client().holidays_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def holidays_create(fk_user: int, date_debut: str, date_fin: str, halfday: int, fk_type: int, note: str = "", status: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create a holiday request. Args: fk_user: User ID (required). date_debut: Start date (required). date_fin: End date (required). halfday: Half day flag (required). fk_type: Leave type (required)."""
    params = CreateHolidayParam(fk_user=fk_user, date_debut=date_debut, date_fin=date_fin, halfday=halfday, fk_type=fk_type, note=note, status=status)
    return await get_client().holidays_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def holidays_update(id: int, fk_user: Optional[int] = None, date_debut: Optional[str] = None, date_fin: Optional[str] = None, halfday: Optional[int] = None, fk_type: Optional[int] = None, note: Optional[str] = None, status: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a holiday."""
    payload = {k: v for k, v in {"fk_user": fk_user, "date_debut": date_debut, "date_fin": date_fin, "halfday": halfday, "fk_type": fk_type, "note": note, "status": status}.items() if v is not None}
    return await get_client().holidays_update(id, payload, get_user_token())

@mcp.tool()
async def holidays_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a holiday."""
    return await get_client().holidays_delete(id, get_user_token())

@mcp.tool()
async def holidays_validate(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Validate a holiday request."""
    return await get_client().holidays_validate(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def holidays_approve(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Approve a holiday request."""
    return await get_client().holidays_approve(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def holidays_cancel(id: int, notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Cancel a holiday request."""
    return await get_client().holidays_cancel(id, get_user_token(), notrigger=notrigger)

@mcp.tool()
async def holidays_refuse(id: int, detail_refuse: str = "", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Refuse a holiday request."""
    return await get_client().holidays_refuse(id, get_user_token(), detail_refuse=detail_refuse, notrigger=notrigger)

# ============================================================
# Agenda Events
# ============================================================
@mcp.tool()
async def agenda_events_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List agenda events."""
    data = await get_client().agenda_events_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, user_ids=user_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def agenda_events_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get an agenda event by ID."""
    return await get_client().agenda_events_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def agenda_events_create(type_code: str, datep: str, label: str, note: str = "", author_user_id: int = 0, userownerid: int = 0, socid: int = 0, fk_project: int = 0, datep2: str = "", duration: int = 0, location: str = "", percent: int = 0, fulldayevent: int = 0, punctual: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Create an agenda event. Args: type_code: Event type code (required). datep: Start date (required). label: Label (required)."""
    params = CreateAgendaEventParam(type_code=type_code, datep=datep, label=label, note=note, author_user_id=author_user_id, userownerid=userownerid, socid=socid, fk_project=fk_project, datep2=datep2, duration=duration, location=location, percent=percent, fulldayevent=fulldayevent, punctual=punctual)
    return await get_client().agenda_events_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def agenda_events_update(id: int, type_code: Optional[str] = None, datep: Optional[str] = None, label: Optional[str] = None, note: Optional[str] = None, author_user_id: Optional[int] = None, userownerid: Optional[int] = None, socid: Optional[int] = None, fk_project: Optional[int] = None, datep2: Optional[str] = None, duration: Optional[int] = None, location: Optional[str] = None, percent: Optional[int] = None, fulldayevent: Optional[int] = None, punctual: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update an agenda event."""
    payload = {k: v for k, v in {"type_code": type_code, "datep": datep, "label": label, "note": note, "author_user_id": author_user_id, "userownerid": userownerid, "socid": socid, "fk_project": fk_project, "datep2": datep2, "duration": duration, "location": location, "percent": percent, "fulldayevent": fulldayevent, "punctual": punctual}.items() if v is not None}
    return await get_client().agenda_events_update(id, payload, get_user_token())

@mcp.tool()
async def agenda_events_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an agenda event."""
    return await get_client().agenda_events_delete(id, get_user_token())

# ============================================================
# Categories
# ============================================================
@mcp.tool()
async def categories_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, type: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List categories."""
    data = await get_client().categories_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, type=type, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def categories_get(id: int, include_childs: bool = False, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a category by ID."""
    return await get_client().categories_get(id, get_user_token(), include_childs=include_childs, include_all_fields=include_all_fields)

@mcp.tool()
async def categories_create(ref: str, label: str, type: str, description: str = "", color: str = "", parent: int = 0, note_public: str = "", note_private: str = "", status: int = 1, ctx: Context = None) -> dict[str, Any]:
    """Create a category. Args: ref: Reference (required). label: Label (required). type: Type (required)."""
    params = CreateCategoryParam(ref=ref, label=label, type=type, description=description, color=color, parent=parent, note_public=note_public, note_private=note_private, status=status)
    return await get_client().categories_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def categories_update(id: int, ref: Optional[str] = None, label: Optional[str] = None, type: Optional[str] = None, description: Optional[str] = None, color: Optional[str] = None, parent: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, status: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a category."""
    payload = {k: v for k, v in {"ref": ref, "label": label, "type": type, "description": description, "color": color, "parent": parent, "note_public": note_public, "note_private": note_private, "status": status}.items() if v is not None}
    return await get_client().categories_update(id, payload, get_user_token())

@mcp.tool()
async def categories_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a category."""
    return await get_client().categories_delete(id, get_user_token())

@mcp.tool()
async def categories_get_types(ctx: Context = None) -> dict[str, Any]:
    """Get category types."""
    data = await get_client().categories_get_types(get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def categories_get_for_object(type: str, id: int, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Get categories for an object. Args: type: Object type (required). id: Object ID (required)."""
    data = await get_client().categories_get_for_object(type, id, get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def categories_link_object_by_id(id: int, type: str, object_id: int, ctx: Context = None) -> dict[str, Any]:
    """Link an object to a category by ID. Args: id: Category ID (required). type: Object type (required). object_id: Object ID (required)."""
    return await get_client().categories_link_object_by_id(id, type, object_id, get_user_token())

@mcp.tool()
async def categories_link_object_by_ref(id: int, type: str, object_ref: str, ctx: Context = None) -> dict[str, Any]:
    """Link an object to a category by ref. Args: id: Category ID (required). type: Object type (required). object_ref: Object ref (required)."""
    return await get_client().categories_link_object_by_ref(id, type, object_ref, get_user_token())

@mcp.tool()
async def categories_unlink_object(id: int, type: str, object_id: int, ctx: Context = None) -> dict[str, Any]:
    """Unlink an object from a category."""
    return await get_client().categories_unlink_object(id, type, object_id, get_user_token())

# ============================================================
# Mailings
# ============================================================
@mcp.tool()
async def mailings_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List mailings."""
    data = await get_client().mailings_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def mailings_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a mailing by ID."""
    return await get_client().mailings_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def mailings_create(title: str, mail_template_id: int, mail_subject: str, note: str = "", status: int = 0, sujet: str = "", body: str = "", email_from: str = "", email_to: str = "", email_cc: str = "", email_bcc: str = "", lang: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a mailing. Args: title: Title (required). mail_template_id: Template ID (required). mail_subject: Subject (required)."""
    params = CreateMailingParam(title=title, mail_template_id=mail_template_id, mail_subject=mail_subject, note=note, status=status, sujet=sujet, body=body, email_from=email_from, email_to=email_to, email_cc=email_cc, email_bcc=email_bcc, lang=lang)
    return await get_client().mailings_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def mailings_update(id: int, title: Optional[str] = None, mail_template_id: Optional[int] = None, mail_subject: Optional[str] = None, note: Optional[str] = None, status: Optional[int] = None, sujet: Optional[str] = None, body: Optional[str] = None, email_from: Optional[str] = None, email_to: Optional[str] = None, email_cc: Optional[str] = None, email_bcc: Optional[str] = None, lang: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a mailing."""
    payload = {k: v for k, v in {"title": title, "mail_template_id": mail_template_id, "mail_subject": mail_subject, "note": note, "status": status, "sujet": sujet, "body": body, "email_from": email_from, "email_to": email_to, "email_cc": email_cc, "email_bcc": email_bcc, "lang": lang}.items() if v is not None}
    return await get_client().mailings_update(id, payload, get_user_token())

@mcp.tool()
async def mailings_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a mailing."""
    return await get_client().mailings_delete(id, get_user_token())

@mcp.tool()
async def mailings_validate(id: int, ctx: Context = None) -> dict[str, Any]:
    """Validate a mailing."""
    return await get_client().mailings_validate(id, get_user_token())

# ============================================================
# Multi Currencies
# ============================================================
@mcp.tool()
async def multi_currencies_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List multi currencies."""
    data = await get_client().multi_currencies_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def multi_currencies_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a multi currency by ID."""
    return await get_client().multi_currencies_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def multi_currencies_create(code: str, name: str, rate: float = 1.0, status: int = 1, note: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a multi currency. Args: code: Currency code (required). name: Currency name (required)."""
    params = CreateMultiCurrencyParam(code=code, name=name, rate=rate, status=status, note=note)
    return await get_client().multi_currencies_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def multi_currencies_update(id: int, code: Optional[str] = None, name: Optional[str] = None, rate: Optional[float] = None, status: Optional[int] = None, note: Optional[str] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a multi currency."""
    payload = {k: v for k, v in {"code": code, "name": name, "rate": rate, "status": status, "note": note}.items() if v is not None}
    return await get_client().multi_currencies_update(id, payload, get_user_token())

@mcp.tool()
async def multi_currencies_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a multi currency."""
    return await get_client().multi_currencies_delete(id, get_user_token())

@mcp.tool()
async def multi_currencies_get_rates(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get exchange rates for a currency. Args: id: Currency ID (required)."""
    data = await get_client().multi_currencies_get_rates(id, get_user_token())
    return {"items": json_to_toon(data)}

# ============================================================
# Tickets
# ============================================================
@mcp.tool()
async def tickets_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, socid: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List tickets."""
    data = await get_client().tickets_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, socid=socid, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def tickets_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a ticket by ID."""
    return await get_client().tickets_get(id, get_user_token(), include_all_fields=include_all_fields)

@mcp.tool()
async def tickets_create(subject: str, type_code: str, severity_code: str, category_code: str, socid: int = 0, note_public: str = "", note_private: str = "", track_id: str = "", fk_user_assign: int = 0, email: str = "", origin: str = "", origin_id: int = 0, message: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a ticket. Args: subject: Subject (required). type_code: Type code (required). severity_code: Severity code (required). category_code: Category code (required)."""
    params = CreateTicketParam(subject=subject, type_code=type_code, severity_code=severity_code, category_code=category_code, socid=socid, note_public=note_public, note_private=note_private, track_id=track_id, fk_user_assign=fk_user_assign, email=email, origin=origin, origin_id=origin_id, message=message)
    return await get_client().tickets_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def tickets_update(id: int, subject: Optional[str] = None, type_code: Optional[str] = None, severity_code: Optional[str] = None, category_code: Optional[str] = None, socid: Optional[int] = None, note_public: Optional[str] = None, note_private: Optional[str] = None, track_id: Optional[str] = None, fk_user_assign: Optional[int] = None, email: Optional[str] = None, origin: Optional[str] = None, origin_id: Optional[int] = None, ctx: Context = None) -> dict[str, Any]:
    """Update a ticket."""
    payload = {k: v for k, v in {"subject": subject, "type_code": type_code, "severity_code": severity_code, "category_code": category_code, "socid": socid, "note_public": note_public, "note_private": note_private, "track_id": track_id, "fk_user_assign": fk_user_assign, "email": email, "origin": origin, "origin_id": origin_id}.items() if v is not None}
    return await get_client().tickets_update(id, payload, get_user_token())

@mcp.tool()
async def tickets_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete a ticket."""
    return await get_client().tickets_delete(id, get_user_token())

@mcp.tool()
async def tickets_create_message(ticket_id: int, message: str, fk_user_author: int = 0, note_public: str = "", note_private: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create a ticket message. Args: ticket_id: Ticket ID (required). message: Message text (required)."""
    params = CreateTicketMessageParam(ticket_id=ticket_id, message=message, fk_user_author=fk_user_author, note_public=note_public, note_private=note_private)
    return await get_client().tickets_create_message(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def tickets_add_contact(id: int, contactid: int, type: str, source: str = "external", notrigger: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Add contact to ticket. Args: id: Ticket ID (required). contactid: Contact ID (required). type: Contact type (required)."""
    return await get_client().tickets_add_contact(id, contactid, type, get_user_token(), source=source, notrigger=notrigger)

@mcp.tool()
async def tickets_delete_contact(id: int, contactid: int, type: str, ctx: Context = None) -> dict[str, Any]:
    """Delete contact from ticket. Args: id: Ticket ID (required). contactid: Contact ID (required). type: Type (required)."""
    return await get_client().tickets_delete_contact(id, contactid, type, get_user_token())

# ============================================================
# Workstations
# ============================================================
@mcp.tool()
async def workstations_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List workstations."""
    data = await get_client().workstations_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def workstations_get(id: int, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a workstation by ID."""
    return await get_client().workstations_get(id, get_user_token(), include_all_fields=include_all_fields)

# ============================================================
# Object Links
# ============================================================
@mcp.tool()
async def object_links_get(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get object links for an object. Args: id: Object ID (required)."""
    data = await get_client().object_links_get(id, get_user_token())
    return {"items": json_to_toon(data)}

@mcp.tool()
async def object_links_create(fk_source: int, sourcetype: str, fk_target: int, targettype: str, relationtype: str = "", ctx: Context = None) -> dict[str, Any]:
    """Create an object link. Args: fk_source: Source ID (required). sourcetype: Source type (required). fk_target: Target ID (required). targettype: Target type (required)."""
    params = CreateObjectLinkParam(fk_source=fk_source, sourcetype=sourcetype, fk_target=fk_target, targettype=targettype, relationtype=relationtype)
    return await get_client().object_links_create(params.model_dump(exclude_unset=True), get_user_token())

@mcp.tool()
async def object_links_get_by_values(fk_source: int = 0, sourcetype: str = "", fk_target: int = 0, targettype: str = "", relationtype: str = "", ctx: Context = None) -> dict[str, Any]:
    """Get object links by values."""
    return await get_client().object_links_get_by_values(get_user_token(), fk_source=fk_source, sourcetype=sourcetype, fk_target=fk_target, targettype=targettype, relationtype=relationtype)

@mcp.tool()
async def object_links_delete(id: int, ctx: Context = None) -> dict[str, Any]:
    """Delete an object link."""
    return await get_client().object_links_delete(id, get_user_token())

# ============================================================
# Users
# ============================================================
@mcp.tool()
async def users_list(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", category: int = 0, sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List users."""
    data = await get_client().users_list(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, user_ids=user_ids, category=category, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def users_get(id: int, includepermissions: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a user by ID."""
    return await get_client().users_get(id, get_user_token(), includepermissions=includepermissions, include_all_fields=include_all_fields)

@mcp.tool()
async def users_get_by_login(login: str, includepermissions: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a user by login. Args: login: User login (required)."""
    return await get_client().users_get_by_login(login, get_user_token(), includepermissions=includepermissions, include_all_fields=include_all_fields)

@mcp.tool()
async def users_get_by_email(email: str, includepermissions: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a user by email. Args: email: User email (required)."""
    return await get_client().users_get_by_email(email, get_user_token(), includepermissions=includepermissions, include_all_fields=include_all_fields)

@mcp.tool()
async def users_get_info(includepermissions: int = 0, ctx: Context = None) -> dict[str, Any]:
    """Get current user info."""
    return await get_client().users_get_info(get_user_token(), includepermissions=includepermissions)

@mcp.tool()
async def users_list_groups(sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, group_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """List user groups."""
    data = await get_client().users_list_groups(get_user_token(), sortfield=sortfield, sortorder=sortorder, limit=limit, page=page, group_ids=group_ids, sqlfilters=sqlfilters, include_all_fields=include_all_fields)
    return {"items": json_to_toon(data)}

@mcp.tool()
async def users_get_group(group: int, load_members: int = 0, includepermissions: int = 0, include_all_fields: bool = False, ctx: Context = None) -> dict[str, Any]:
    """Get a user group by ID. Args: group: Group ID (required)."""
    return await get_client().users_get_group(group, get_user_token(), load_members=load_members, includepermissions=includepermissions, include_all_fields=include_all_fields)

@mcp.tool()
async def users_get_user_groups(id: int, ctx: Context = None) -> dict[str, Any]:
    """Get groups for a user. Args: id: User ID (required)."""
    data = await get_client().users_get_user_groups(id, get_user_token())
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
    if not base_url:
        print("ERROR: DOLIBARR_BASE_URL environment variable is required.")
        sys.exit(1)
    app = AuthMiddleware(mcp.http_app(json_response=True))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
