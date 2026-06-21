import datetime as dt
import os
import re
from typing import Any, Optional

import httpx


def _normalize_datetime(value: str) -> str:
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$', value):
        parsed = dt.datetime.fromisoformat(value)
        parsed = parsed.astimezone(dt.timezone.utc)
        return parsed.strftime('%Y-%m-%d %H:%M:%S')
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
        raise ValueError(
            f"Invalid datetime: {value}. Timezone offset is required. "
            "Must use format: 2026-06-22T15:00:00-04:00"
        )
    return value


TP_COMMON = "id,ref,nom,client,fournisseur,code_client,code_fournisseur,address,zip,town,country_id,country_code,phone,email,status,tva_intra,date_creation,date_modification"
PROD_COMMON = "id,ref,label,type,status,price,price_ttc,tva_tx,stock,barcode,weight,date_creation"
INV_COMMON = "id,ref,socid,socname,total_ht,total_tva,total_ttc,status,date_creation,date_validation"
CONTACT_COMMON = "id,lastname,firstname,socid,socname,email,phone,phone_mobile,status"
BASE_COMMON = "id,ref,label,status,date_creation,date_modification"


class DolibarrClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or os.getenv("DOLIBARR_BASE_URL", "")).rstrip("/")
        if not self.base_url:
            raise ValueError(
                "Dolibarr URL required. Set DOLIBARR_BASE_URL env var or pass base_url."
            )

    def _get_headers(self, api_key: Optional[str] = None) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    async def request(self, method: str, path: str, api_key: Optional[str] = None, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        headers = self._get_headers(api_key)
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                return {}
            if response.headers.get("content-type", "").startswith("application/json"):
                data = response.json()
                if isinstance(data, int):
                    return {"id": data}
                return data
            return {"text": response.text}

    async def get(self, path: str, api_key: Optional[str] = None, **kwargs: Any) -> Any:
        return await self.request("GET", path, api_key, **kwargs)

    async def post(self, path: str, api_key: Optional[str] = None, **kwargs: Any) -> Any:
        return await self.request("POST", path, api_key, **kwargs)

    async def put(self, path: str, api_key: Optional[str] = None, **kwargs: Any) -> Any:
        return await self.request("PUT", path, api_key, **kwargs)

    async def delete(self, path: str, api_key: Optional[str] = None, **kwargs: Any) -> Any:
        return await self.request("DELETE", path, api_key, **kwargs)

    async def status_get(self, api_key: Optional[str] = None) -> Any:
        return await self.get("/status/", api_key)

    async def documents_list(self, api_key: Optional[str] = None, modulepart: str = "", id: int = 0, ref: str = "", include_all_fields: bool = False, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0) -> Any:
        params = {}
        if modulepart:
            params["modulepart"] = modulepart
        if id:
            params["id"] = id
        if ref:
            params["ref"] = ref
        if sortfield:
            params["sortfield"] = sortfield
        if sortorder != "ASC":
            params["sortorder"] = sortorder
        if limit != 100:
            params["limit"] = limit
        if page != 0:
            params["page"] = page
        if not include_all_fields:
            params["properties"] = BASE_COMMON
        return await self.get("/documents/", api_key, params=params)

    # ============================================================
    # Third Parties
    # ============================================================
    async def thirdparties_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, mode: str = "", category: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if mode: params["mode"] = mode
        if category: params["category"] = category
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = TP_COMMON
        return await self.get("/thirdparties/", api_key, params=params)

    async def thirdparties_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = TP_COMMON
        return await self.get(f"/thirdparties/{id}", api_key, params=params or None)

    async def thirdparties_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/thirdparties/", api_key, json=payload)

    async def thirdparties_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/thirdparties/{id}", api_key, json=payload)

    async def thirdparties_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/thirdparties/{id}", api_key)

    async def thirdparties_get_outstanding_proposals(self, id: int, api_key: Optional[str] = None, mode: str = "") -> Any:
        params = {}
        if mode: params["mode"] = mode
        return await self.get(f"/thirdparties/{id}/outstandingproposals", api_key, params=params or None)

    async def thirdparties_get_outstanding_orders(self, id: int, api_key: Optional[str] = None, mode: str = "") -> Any:
        params = {}
        if mode: params["mode"] = mode
        return await self.get(f"/thirdparties/{id}/outstandingorders", api_key, params=params or None)

    async def thirdparties_get_outstanding_invoices(self, id: int, api_key: Optional[str] = None, mode: str = "") -> Any:
        params = {}
        if mode: params["mode"] = mode
        return await self.get(f"/thirdparties/{id}/outstandinginvoices", api_key, params=params or None)

    async def thirdparties_get_representatives(self, id: int, api_key: Optional[str] = None, mode: int = 0) -> Any:
        params = {}
        if mode: params["mode"] = mode
        return await self.get(f"/thirdparties/{id}/representatives", api_key, params=params or None)

    async def thirdparties_get_categories(self, id: int, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        return await self.get(f"/thirdparties/{id}/categories", api_key, params=params or None)

    # ============================================================
    # Contacts
    # ============================================================
    async def contacts_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", category: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if category: params["category"] = category
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = CONTACT_COMMON
        return await self.get("/contacts/", api_key, params=params)

    async def contacts_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = CONTACT_COMMON
        return await self.get(f"/contacts/{id}", api_key, params=params or None)

    async def contacts_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/contacts/", api_key, json=payload)

    async def contacts_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/contacts/{id}", api_key, json=payload)

    async def contacts_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/contacts/{id}", api_key)

    async def contacts_get_categories(self, id: int, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        return await self.get(f"/contacts/{id}/categories", api_key, params=params or None)

    # ============================================================
    # Products
    # ============================================================
    async def products_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, mode: int = 0, category: int = 0, sqlfilters: str = "", variant_filter: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if mode: params["mode"] = mode
        if category: params["category"] = category
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if variant_filter: params["variant_filter"] = variant_filter
        if not include_all_fields: params["properties"] = PROD_COMMON
        return await self.get("/products/", api_key, params=params)

    async def products_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = PROD_COMMON
        return await self.get(f"/products/{id}", api_key, params=params or None)

    async def products_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/products/", api_key, json=payload)

    async def products_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/products/{id}", api_key, json=payload)

    async def products_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/products/{id}", api_key)

    async def products_get_subproducts(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/products/{id}/subproducts", api_key)

    async def products_get_categories(self, id: int, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        return await self.get(f"/products/{id}/categories", api_key, params=params or None)

    async def products_get_stock(self, id: int, api_key: Optional[str] = None, selected_warehouse_id: int = 0) -> Any:
        params = {}
        if selected_warehouse_id: params["selected_warehouse_id"] = selected_warehouse_id
        return await self.get(f"/products/{id}/stock", api_key, params=params or None)

    async def products_get_contacts(self, id: int, api_key: Optional[str] = None, type: str = "") -> Any:
        params = {}
        if type: params["type"] = type
        return await self.get(f"/products/{id}/contacts", api_key, params=params or None)

    # ============================================================
    # Warehouses
    # ============================================================
    async def warehouses_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, category: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if category: params["category"] = category
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/warehouses/", api_key, params=params)

    async def warehouses_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/warehouses/{id}", api_key, params=params or None)

    async def warehouses_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/warehouses/", api_key, json=payload)

    async def warehouses_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/warehouses/{id}", api_key, json=payload)

    async def warehouses_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/warehouses/{id}", api_key)

    async def warehouses_list_products(self, id: int, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if not include_all_fields: params["properties"] = PROD_COMMON
        return await self.get(f"/warehouses/{id}/products", api_key, params=params)

    # ============================================================
    # Stock Movements
    # ============================================================
    async def stockmovements_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/stockmovements/", api_key, params=params)

    async def stockmovements_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/stockmovements/{id}", api_key, params=params or None)

    async def stockmovements_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/stockmovements/", api_key, json=payload)

    async def stockmovements_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/stockmovements/{id}", api_key, json=payload)

    async def stockmovements_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/stockmovements/{id}", api_key)

    # ============================================================
    # Product Lots
    # ============================================================
    async def productlots_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/productlots/", api_key, params=params)

    async def productlots_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/productlots/{id}", api_key, params=params or None)

    async def productlots_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/productlots/", api_key, json=payload)

    async def productlots_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/productlots/{id}", api_key, json=payload)

    async def productlots_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/productlots/{id}", api_key)

    # ============================================================
    # Proposals
    # ============================================================
    async def proposals_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get("/proposals/", api_key, params=params)

    async def proposals_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get(f"/proposals/{id}", api_key, params=params or None)

    async def proposals_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/proposals/", api_key, json=payload)

    async def proposals_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/proposals/{id}", api_key, json=payload)

    async def proposals_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/proposals/{id}", api_key)

    async def proposals_get_lines(self, id: int, api_key: Optional[str] = None, sqlfilters: str = "") -> Any:
        params = {}
        if sqlfilters: params["sqlfilters"] = sqlfilters
        return await self.get(f"/proposals/{id}/lines", api_key, params=params or None)

    async def proposals_create_line(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/proposals/{id}/lines", api_key, json=payload)

    async def proposals_update_line(self, id: int, lineid: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/proposals/{id}/lines/{lineid}", api_key, json=payload)

    async def proposals_delete_line(self, id: int, lineid: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/proposals/{id}/lines/{lineid}", api_key)

    async def proposals_settodraft(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/proposals/{id}/settodraft", api_key)

    async def proposals_validate(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/proposals/{id}/validate", api_key, params=params or None)

    async def proposals_close(self, id: int, api_key: Optional[str] = None, status: int = 0, note_private: str = "", note_public: str = "", notrigger: int = 0) -> Any:
        payload = {}
        if status: payload["status"] = status
        if note_private: payload["note_private"] = note_private
        if note_public: payload["note_public"] = note_public
        if notrigger: payload["notrigger"] = notrigger
        payload = {k: _normalize_datetime(v) if isinstance(v, str) else v for k, v in payload.items()}
        return await self.post(f"/proposals/{id}/close", api_key, json=payload or None)

    async def proposals_setinvoiced(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/proposals/{id}/setinvoiced", api_key)

    async def proposals_get_contacts(self, id: int, api_key: Optional[str] = None, type: str = "") -> Any:
        params = {}
        if type: params["type"] = type
        return await self.get(f"/proposals/{id}/contacts", api_key, params=params or None)

    async def proposals_add_contact(self, id: int, contactid: int, type: str, api_key: Optional[str] = None, source: str = "external", notrigger: int = 0) -> Any:
        payload = {"source": source}
        if notrigger: payload["notrigger"] = notrigger
        return await self.post(f"/proposals/{id}/contact/{contactid}/{type}", api_key, json=payload)

    # ============================================================
    # Orders
    # ============================================================
    async def orders_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get("/orders/", api_key, params=params)

    async def orders_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get(f"/orders/{id}", api_key, params=params or None)

    async def orders_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/orders/", api_key, json=payload)

    async def orders_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/orders/{id}", api_key, json=payload)

    async def orders_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/orders/{id}", api_key)

    async def orders_get_lines(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/orders/{id}/lines", api_key)

    async def orders_get_line(self, id: int, lineid: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/orders/{id}/lines/{lineid}", api_key, params=params or None)

    async def orders_create_line(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/orders/{id}/lines", api_key, json=payload)

    async def orders_update_line(self, id: int, lineid: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/orders/{id}/lines/{lineid}", api_key, json=payload)

    async def orders_delete_line(self, id: int, lineid: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/orders/{id}/lines/{lineid}", api_key)

    async def orders_settodraft(self, id: int, api_key: Optional[str] = None, idwarehouse: int = 0) -> Any:
        params = {}
        if idwarehouse: params["idwarehouse"] = idwarehouse
        return await self.post(f"/orders/{id}/settodraft", api_key, params=params or None)

    async def orders_validate(self, id: int, api_key: Optional[str] = None, idwarehouse: int = 0, notrigger: int = 0) -> Any:
        params = {}
        if idwarehouse: params["idwarehouse"] = idwarehouse
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/orders/{id}/validate", api_key, params=params or None)

    async def orders_close(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/orders/{id}/close", api_key, params=params or None)

    async def orders_reopen(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/orders/{id}/reopen", api_key)

    async def orders_setinvoiced(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/orders/{id}/setinvoiced", api_key)

    async def orders_create_from_proposal(self, proposalid: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/orders/createfromproposal/{proposalid}", api_key)

    async def orders_get_shipments(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/orders/{id}/shipment", api_key)

    async def orders_create_shipment(self, id: int, warehouse_id: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/orders/{id}/shipment/{warehouse_id}", api_key)

    async def orders_get_contacts(self, id: int, api_key: Optional[str] = None, type: str = "") -> Any:
        params = {}
        if type: params["type"] = type
        return await self.get(f"/orders/{id}/contacts", api_key, params=params or None)

    # ============================================================
    # Invoices
    # ============================================================
    async def invoices_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", status: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if status: params["status"] = status
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get("/invoices/", api_key, params=params)

    async def invoices_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get(f"/invoices/{id}", api_key, params=params or None)

    async def invoices_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/invoices/", api_key, json=payload)

    async def invoices_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/invoices/{id}", api_key, json=payload)

    async def invoices_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/invoices/{id}", api_key)

    async def invoices_get_lines(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/invoices/{id}/lines", api_key)

    async def invoices_create_line(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/invoices/{id}/lines", api_key, json=payload)

    async def invoices_update_line(self, id: int, lineid: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/invoices/{id}/lines/{lineid}", api_key, json=payload)

    async def invoices_delete_line(self, id: int, lineid: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/invoices/{id}/lines/{lineid}", api_key)

    async def invoices_create_from_order(self, orderid: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/invoices/createfromorder/{orderid}", api_key)

    async def invoices_settodraft(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/invoices/{id}/settodraft", api_key)

    async def invoices_validate(self, id: int, api_key: Optional[str] = None, force_number: int = 0, idwarehouse: int = 0, notrigger: int = 0) -> Any:
        params = {}
        if force_number: params["force_number"] = force_number
        if idwarehouse: params["idwarehouse"] = idwarehouse
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/invoices/{id}/validate", api_key, params=params or None)

    async def invoices_settopaid(self, id: int, api_key: Optional[str] = None, close_code: str = "", close_note: str = "") -> Any:
        params = {}
        if close_code: params["close_code"] = close_code
        if close_note: params["close_note"] = close_note
        return await self.post(f"/invoices/{id}/settopaid", api_key, params=params or None)

    async def invoices_settounpaid(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/invoices/{id}/settounpaid", api_key)

    async def invoices_get_payments(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/invoices/{id}/payments", api_key)

    async def invoices_add_payment(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/invoices/{id}/payments", api_key, json=payload)

    async def invoices_get_contacts(self, id: int, api_key: Optional[str] = None, type: str = "") -> Any:
        params = {}
        if type: params["type"] = type
        return await self.get(f"/invoices/{id}/contacts", api_key, params=params or None)

    async def invoices_add_contact(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/invoices/{id}/contacts", api_key, json=payload)

    async def invoices_delete_contact(self, id: int, contactid: int, type: str, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/invoices/{id}/contact/{contactid}/{type}", api_key)

    async def invoices_get_discount(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/invoices/{id}/discount", api_key)

    async def invoices_use_discount(self, id: int, discountid: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/invoices/{id}/usediscount/{discountid}", api_key)

    # ============================================================
    # Payments
    # ============================================================
    async def payments_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/paiements/", api_key, params=params)

    async def payments_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/paiements/{id}", api_key, params=params or None)

    async def payments_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/paiements/{id}", api_key, json=payload)

    async def payments_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/paiements/{id}", api_key)

    # ============================================================
    # Bank Accounts
    # ============================================================
    async def bankaccounts_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, category: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if category: params["category"] = category
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/bankaccounts/", api_key, params=params)

    async def bankaccounts_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/bankaccounts/{id}", api_key, params=params or None)

    async def bankaccounts_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/bankaccounts/", api_key, json=payload)

    async def bankaccounts_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/bankaccounts/{id}", api_key, json=payload)

    async def bankaccounts_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/bankaccounts/{id}", api_key)

    async def bankaccounts_transfer(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/bankaccounts/transfer", api_key, json=payload)

    async def bankaccounts_get_lines(self, id: int, api_key: Optional[str] = None, sqlfilters: str = "") -> Any:
        params = {}
        if sqlfilters: params["sqlfilters"] = sqlfilters
        return await self.get(f"/bankaccounts/{id}/lines", api_key, params=params or None)

    async def bankaccounts_create_line(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/bankaccounts/{id}/lines", api_key, json=payload)

    async def bankaccounts_get_line(self, line_id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/bankaccounts/lines/{line_id}", api_key)

    async def bankaccounts_update_line(self, id: int, line_id: int, label: str, api_key: Optional[str] = None) -> Any:
        payload = {"label": label}
        return await self.put(f"/bankaccounts/{id}/lines/{line_id}", api_key, json=payload)

    async def bankaccounts_delete_line(self, id: int, line_id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/bankaccounts/{id}/lines/{line_id}", api_key)

    async def bankaccounts_get_balance(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/bankaccounts/{id}/balance", api_key)

    # ============================================================
    # Supplier Orders
    # ============================================================
    async def supplier_orders_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", product_ids: str = "", status: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if product_ids: params["product_ids"] = product_ids
        if status: params["status"] = status
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get("/supplierorders/", api_key, params=params)

    async def supplier_orders_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get(f"/supplierorders/{id}", api_key, params=params or None)

    async def supplier_orders_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/supplierorders/", api_key, json=payload)

    async def supplier_orders_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/supplierorders/{id}", api_key, json=payload)

    async def supplier_orders_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/supplierorders/{id}", api_key)

    async def supplier_orders_create_line(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/supplierorders/{id}/lines", api_key, json=payload)

    async def supplier_orders_get_contacts(self, id: int, api_key: Optional[str] = None, type: str = "") -> Any:
        params = {}
        if type: params["type"] = type
        return await self.get(f"/supplierorders/{id}/contacts", api_key, params=params or None)

    async def supplier_orders_add_contact(self, id: int, contactid: int, type: str, source: str, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/supplierorders/{id}/contact/{contactid}/{type}/{source}", api_key)

    async def supplier_orders_delete_contact(self, id: int, contactid: int, type: str, source: str, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/supplierorders/{id}/contact/{contactid}/{type}/{source}", api_key)

    async def supplier_orders_validate(self, id: int, api_key: Optional[str] = None, idwarehouse: int = 0, notrigger: int = 0) -> Any:
        params = {}
        if idwarehouse: params["idwarehouse"] = idwarehouse
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/supplierorders/{id}/validate", api_key, params=params or None)

    async def supplier_orders_approve(self, id: int, api_key: Optional[str] = None, idwarehouse: int = 0, secondlevel: int = 0) -> Any:
        params = {}
        if idwarehouse: params["idwarehouse"] = idwarehouse
        if secondlevel: params["secondlevel"] = secondlevel
        return await self.post(f"/supplierorders/{id}/approve", api_key, params=params or None)

    async def supplier_orders_receive(self, id: int, api_key: Optional[str] = None, closeopenorder: int = 0, comment: str = "") -> Any:
        params = {}
        if closeopenorder: params["closeopenorder"] = closeopenorder
        if comment: params["comment"] = comment
        return await self.post(f"/supplierorders/{id}/receive", api_key, params=params or None)

    # ============================================================
    # Supplier Invoices
    # ============================================================
    async def supplier_invoices_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", status: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if status: params["status"] = status
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get("/supplierinvoices/", api_key, params=params)

    async def supplier_invoices_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get(f"/supplierinvoices/{id}", api_key, params=params or None)

    async def supplier_invoices_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/supplierinvoices/", api_key, json=payload)

    async def supplier_invoices_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/supplierinvoices/{id}", api_key, json=payload)

    async def supplier_invoices_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/supplierinvoices/{id}", api_key)

    async def supplier_invoices_get_lines(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/supplierinvoices/{id}/lines", api_key)

    async def supplier_invoices_create_line(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/supplierinvoices/{id}/lines", api_key, json=payload)

    async def supplier_invoices_update_line(self, id: int, lineid: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/supplierinvoices/{id}/lines/{lineid}", api_key, json=payload)

    async def supplier_invoices_delete_line(self, id: int, lineid: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/supplierinvoices/{id}/lines/{lineid}", api_key)

    async def supplier_invoices_validate(self, id: int, api_key: Optional[str] = None, idwarehouse: int = 0, notrigger: int = 0) -> Any:
        params = {}
        if idwarehouse: params["idwarehouse"] = idwarehouse
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/supplierinvoices/{id}/validate", api_key, params=params or None)

    async def supplier_invoices_settopaid(self, id: int, api_key: Optional[str] = None, close_code: str = "", close_note: str = "") -> Any:
        params = {}
        if close_code: params["close_code"] = close_code
        if close_note: params["close_note"] = close_note
        return await self.post(f"/supplierinvoices/{id}/settopaid", api_key, params=params or None)

    async def supplier_invoices_get_payments(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/supplierinvoices/{id}/payments", api_key)

    async def supplier_invoices_add_payment(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/supplierinvoices/{id}/payments", api_key, json=payload)

    # ============================================================
    # Supplier Proposals
    # ============================================================
    async def supplier_proposals_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get("/supplierproposals/", api_key, params=params)

    async def supplier_proposals_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get(f"/supplierproposals/{id}", api_key, params=params or None)

    async def supplier_proposals_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/supplierproposals/", api_key, json=payload)

    async def supplier_proposals_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/supplierproposals/{id}", api_key, json=payload)

    async def supplier_proposals_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/supplierproposals/{id}", api_key)

    # ============================================================
    # Contracts
    # ============================================================
    async def contracts_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get("/contracts/", api_key, params=params)

    async def contracts_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = INV_COMMON
        return await self.get(f"/contracts/{id}", api_key, params=params or None)

    async def contracts_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/contracts/", api_key, json=payload)

    async def contracts_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/contracts/{id}", api_key, json=payload)

    async def contracts_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/contracts/{id}", api_key)

    async def contracts_get_lines(self, id: int, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/contracts/{id}/lines", api_key, params=params or None)

    async def contracts_create_line(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/contracts/{id}/lines", api_key, json=payload)

    async def contracts_update_line(self, id: int, lineid: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/contracts/{id}/lines/{lineid}", api_key, json=payload)

    async def contracts_activate_line(self, id: int, lineid: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/contracts/{id}/lines/{lineid}/activate", api_key, json=payload)

    async def contracts_delete_line(self, id: int, lineid: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/contracts/{id}/lines/{lineid}", api_key)

    async def contracts_validate(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/contracts/{id}/validate", api_key, params=params or None)

    async def contracts_close(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/contracts/{id}/close", api_key, params=params or None)

    # ============================================================
    # BOMs
    # ============================================================
    async def boms_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/boms/", api_key, params=params)

    async def boms_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/boms/{id}", api_key, params=params or None)

    async def boms_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/boms/", api_key, json=payload)

    async def boms_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/boms/{id}", api_key, json=payload)

    async def boms_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/boms/{id}", api_key)

    async def boms_get_lines(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/boms/{id}/lines", api_key)

    async def boms_create_line(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/boms/{id}/lines", api_key, json=payload)

    async def boms_delete_line(self, id: int, lineid: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/boms/{id}/lines/{lineid}", api_key)

    # ============================================================
    # MOs (Manufacturing Orders)
    # ============================================================
    async def mos_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/mos/", api_key, params=params)

    async def mos_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/mos/{id}", api_key, params=params or None)

    async def mos_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/mos/", api_key, json=payload)

    async def mos_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/mos/{id}", api_key, json=payload)

    async def mos_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/mos/{id}", api_key)

    async def mos_produce_and_consume(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/mos/{id}/produceandconsume", api_key, json=payload)

    # ============================================================
    # Projects
    # ============================================================
    async def projects_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", category: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if category: params["category"] = category
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/projects/", api_key, params=params)

    async def projects_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/projects/{id}", api_key, params=params or None)

    async def projects_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/projects/", api_key, json=payload)

    async def projects_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/projects/{id}", api_key, json=payload)

    async def projects_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/projects/{id}", api_key)

    async def projects_get_tasks(self, id: int, api_key: Optional[str] = None, includetimespent: int = 0) -> Any:
        params = {}
        if includetimespent: params["includetimespent"] = includetimespent
        return await self.get(f"/projects/{id}/tasks", api_key, params=params or None)

    async def projects_get_timespent(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/projects/{id}/timespent", api_key)

    async def projects_validate(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/projects/{id}/validate", api_key, params=params or None)

    async def projects_get_contacts(self, id: int, api_key: Optional[str] = None, type: str = "") -> Any:
        params = {}
        if type: params["type"] = type
        return await self.get(f"/projects/{id}/contacts", api_key, params=params or None)

    # ============================================================
    # Tasks
    # ============================================================
    async def tasks_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/tasks/", api_key, params=params)

    async def tasks_get(self, id: int, api_key: Optional[str] = None, includetimespent: int = 0, include_all_fields: bool = False) -> Any:
        params = {}
        if includetimespent: params["includetimespent"] = includetimespent
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/tasks/{id}", api_key, params=params or None)

    async def tasks_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/tasks/", api_key, json=payload)

    async def tasks_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/tasks/{id}", api_key, json=payload)

    async def tasks_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/tasks/{id}", api_key)

    async def tasks_get_timespent(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/tasks/{id}/timespent", api_key)

    async def tasks_add_timespent(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/tasks/{id}/addtimespent", api_key, json=payload)

    async def tasks_update_timespent(self, id: int, timespent_id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/tasks/{id}/timespent/{timespent_id}", api_key, json=payload)

    async def tasks_delete_timespent(self, id: int, timespent_id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/tasks/{id}/timespent/{timespent_id}", api_key)

    async def tasks_get_contacts(self, id: int, api_key: Optional[str] = None, type: str = "") -> Any:
        params = {}
        if type: params["type"] = type
        return await self.get(f"/tasks/{id}/contacts", api_key, params=params or None)

    # ============================================================
    # Shipments
    # ============================================================
    async def shipments_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/shipments/", api_key, params=params)

    async def shipments_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/shipments/{id}", api_key, params=params or None)

    async def shipments_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/shipments/", api_key, json=payload)

    async def shipments_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/shipments/{id}", api_key, json=payload)

    async def shipments_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/shipments/{id}", api_key)

    async def shipments_validate(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/shipments/{id}/validate", api_key, params=params or None)

    async def shipments_close(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/shipments/{id}/close", api_key, params=params or None)

    # ============================================================
    # Receptions
    # ============================================================
    async def receptions_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/receptions/", api_key, params=params)

    async def receptions_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/receptions/{id}", api_key, params=params or None)

    async def receptions_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/receptions/", api_key, json=payload)

    async def receptions_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/receptions/{id}", api_key, json=payload)

    async def receptions_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/receptions/{id}", api_key)

    async def receptions_validate(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/receptions/{id}/validate", api_key, params=params or None)

    async def receptions_close(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/receptions/{id}/close", api_key, params=params or None)

    # ============================================================
    # Interventions
    # ============================================================
    async def interventions_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, thirdparty_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if thirdparty_ids: params["thirdparty_ids"] = thirdparty_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/interventions/", api_key, params=params)

    async def interventions_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/interventions/{id}", api_key, params=params or None)

    async def interventions_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/interventions/", api_key, json=payload)

    async def interventions_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/interventions/{id}", api_key, json=payload)

    async def interventions_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/interventions/{id}", api_key)

    async def interventions_get_lines(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/interventions/{id}/lines", api_key)

    async def interventions_create_line(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/interventions/{id}/lines", api_key, json=payload)

    async def interventions_update_line(self, id: int, lineid: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/interventions/{id}/lines/{lineid}", api_key, json=payload)

    async def interventions_delete_line(self, id: int, lineid: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/interventions/{id}/lines/{lineid}", api_key)

    async def interventions_settodraft(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/interventions/{id}/settodraft", api_key)

    async def interventions_validate(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/interventions/{id}/validate", api_key, params=params or None)

    async def interventions_close(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/interventions/{id}/close", api_key, params=params or None)

    async def interventions_get_contacts(self, id: int, api_key: Optional[str] = None, type: str = "") -> Any:
        params = {}
        if type: params["type"] = type
        return await self.get(f"/interventions/{id}/contacts", api_key, params=params or None)

    # ============================================================
    # Expense Reports
    # ============================================================
    async def expense_reports_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if user_ids: params["user_ids"] = user_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/expensereports/", api_key, params=params)

    async def expense_reports_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/expensereports/{id}", api_key, params=params or None)

    async def expense_reports_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/expensereports/", api_key, json=payload)

    async def expense_reports_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/expensereports/{id}", api_key, json=payload)

    async def expense_reports_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/expensereports/{id}", api_key)

    async def expense_reports_get_lines(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/expensereports/{id}/lines", api_key)

    async def expense_reports_create_line(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post(f"/expensereports/{id}/line", api_key, json=payload)

    async def expense_reports_update_line(self, id: int, lineid: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/expensereports/{id}/lines/{lineid}", api_key, json=payload)

    async def expense_reports_delete_line(self, id: int, lineid: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/expensereports/{id}/lines/{lineid}", api_key)

    async def expense_reports_settodraft(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/expensereports/{id}/settodraft", api_key)

    async def expense_reports_validate(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/expensereports/{id}/validate", api_key, params=params or None)

    async def expense_reports_approve(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/expensereports/{id}/approve", api_key, params=params or None)

    async def expense_reports_deny(self, id: int, api_key: Optional[str] = None, details: str = "", notrigger: int = 0) -> Any:
        params = {}
        if details: params["details"] = details
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/expensereports/{id}/deny", api_key, params=params or None)

    async def expense_reports_cancel(self, id: int, api_key: Optional[str] = None, detail: str = "", notrigger: int = 0) -> Any:
        params = {}
        if detail: params["detail"] = detail
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/expensereports/{id}/cancel", api_key, params=params or None)

    # ============================================================
    # Holidays
    # ============================================================
    async def holidays_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if user_ids: params["user_ids"] = user_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/holidays/", api_key, params=params)

    async def holidays_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/holidays/{id}", api_key, params=params or None)

    async def holidays_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/holidays/", api_key, json=payload)

    async def holidays_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/holidays/{id}", api_key, json=payload)

    async def holidays_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/holidays/{id}", api_key)

    async def holidays_validate(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/holidays/{id}/validate", api_key, params=params or None)

    async def holidays_approve(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/holidays/{id}/approve", api_key, params=params or None)

    async def holidays_cancel(self, id: int, api_key: Optional[str] = None, notrigger: int = 0) -> Any:
        params = {}
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/holidays/{id}/cancel", api_key, params=params or None)

    async def holidays_refuse(self, id: int, api_key: Optional[str] = None, detail_refuse: str = "", notrigger: int = 0) -> Any:
        params = {}
        if detail_refuse: params["detail_refuse"] = detail_refuse
        if notrigger: params["notrigger"] = notrigger
        return await self.post(f"/holidays/{id}/refuse", api_key, params=params or None)

    # ============================================================
    # Agenda Events
    # ============================================================
    async def agenda_events_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if user_ids: params["user_ids"] = user_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/agendaevents/", api_key, params=params)

    async def agenda_events_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/agendaevents/{id}", api_key, params=params or None)

    async def agenda_events_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/agendaevents/", api_key, json=payload)

    async def agenda_events_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/agendaevents/{id}", api_key, json=payload)

    async def agenda_events_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/agendaevents/{id}", api_key)

    # ============================================================
    # Categories
    # ============================================================
    async def categories_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, type: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if type: params["type"] = type
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/categories/", api_key, params=params)

    async def categories_get(self, id: int, api_key: Optional[str] = None, include_childs: bool = False, include_all_fields: bool = False) -> Any:
        params = {}
        if include_childs: params["include_childs"] = "true"
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/categories/{id}", api_key, params=params or None)

    async def categories_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/categories/", api_key, json=payload)

    async def categories_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/categories/{id}", api_key, json=payload)

    async def categories_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/categories/{id}", api_key)

    async def categories_get_types(self, api_key: Optional[str] = None) -> Any:
        return await self.get("/categories/types", api_key)

    async def categories_get_for_object(self, type: str, id: int, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        return await self.get(f"/categories/object/{type}/{id}", api_key, params=params or None)

    async def categories_link_object_by_id(self, id: int, type: str, object_id: int, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/categories/{id}/objects/{type}/{object_id}", api_key)

    async def categories_link_object_by_ref(self, id: int, type: str, object_ref: str, api_key: Optional[str] = None) -> Any:
        return await self.post(f"/categories/{id}/objects/{type}/ref/{object_ref}", api_key)

    async def categories_unlink_object(self, id: int, type: str, object_id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/categories/{id}/objects/{type}/{object_id}", api_key)

    # ============================================================
    # Mailings
    # ============================================================
    async def mailings_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/mailings/", api_key, params=params)

    async def mailings_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/mailings/{id}", api_key, params=params or None)

    async def mailings_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/mailings/", api_key, json=payload)

    async def mailings_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/mailings/{id}", api_key, json=payload)

    async def mailings_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/mailings/{id}", api_key)

    async def mailings_validate(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.put(f"/mailings/{id}/validate", api_key)

    # ============================================================
    # Multi Currencies
    # ============================================================
    async def multi_currencies_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/multicurrencies/", api_key, params=params)

    async def multi_currencies_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/multicurrencies/{id}", api_key, params=params or None)

    async def multi_currencies_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/multicurrencies/", api_key, json=payload)

    async def multi_currencies_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/multicurrencies/{id}", api_key, json=payload)

    async def multi_currencies_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/multicurrencies/{id}", api_key)

    async def multi_currencies_get_rates(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/multicurrencies/{id}/rates", api_key)

    # ============================================================
    # Tickets
    # ============================================================
    async def tickets_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, socid: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if socid: params["socid"] = socid
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/tickets/", api_key, params=params)

    async def tickets_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/tickets/{id}", api_key, params=params or None)

    async def tickets_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/tickets/", api_key, json=payload)

    async def tickets_update(self, id: int, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.put(f"/tickets/{id}", api_key, json=payload)

    async def tickets_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/tickets/{id}", api_key)

    # ============================================================
    # Workstations
    # ============================================================
    async def workstations_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/workstations/", api_key, params=params)

    async def workstations_get(self, id: int, api_key: Optional[str] = None, include_all_fields: bool = False) -> Any:
        params = {}
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/workstations/{id}", api_key, params=params or None)

    # ============================================================
    # Object Links
    # ============================================================
    async def object_links_get(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/objectlinks/{id}", api_key)

    async def object_links_create(self, payload: dict[str, Any], api_key: Optional[str] = None) -> Any:
        return await self.post("/objectlinks/", api_key, json=payload)

    async def object_links_get_by_values(self, api_key: Optional[str] = None, fk_source: int = 0, sourcetype: str = "", fk_target: int = 0, targettype: str = "", relationtype: str = "") -> Any:
        params = {}
        if fk_source: params["fk_source"] = fk_source
        if sourcetype: params["sourcetype"] = sourcetype
        if fk_target: params["fk_target"] = fk_target
        if targettype: params["targettype"] = targettype
        if relationtype: params["relationtype"] = relationtype
        return await self.get("/objectlinks/", api_key, params=params or None)

    async def object_links_delete(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.delete(f"/objectlinks/{id}", api_key)

    # ============================================================
    # Users
    # ============================================================
    async def users_list(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, user_ids: str = "", category: int = 0, sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if user_ids: params["user_ids"] = user_ids
        if category: params["category"] = category
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/users/", api_key, params=params)

    async def users_get(self, id: int, api_key: Optional[str] = None, includepermissions: int = 0, include_all_fields: bool = False) -> Any:
        params = {}
        if includepermissions: params["includepermissions"] = includepermissions
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/users/{id}", api_key, params=params or None)

    async def users_get_by_login(self, login: str, api_key: Optional[str] = None, includepermissions: int = 0, include_all_fields: bool = False) -> Any:
        params = {}
        if includepermissions: params["includepermissions"] = includepermissions
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/users/login/{login}", api_key, params=params or None)

    async def users_get_by_email(self, email: str, api_key: Optional[str] = None, includepermissions: int = 0, include_all_fields: bool = False) -> Any:
        params = {}
        if includepermissions: params["includepermissions"] = includepermissions
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/users/email/{email}", api_key, params=params or None)

    async def users_get_info(self, api_key: Optional[str] = None, includepermissions: int = 0) -> Any:
        params = {}
        if includepermissions: params["includepermissions"] = includepermissions
        return await self.get("/users/info", api_key, params=params or None)

    async def users_list_groups(self, api_key: Optional[str] = None, sortfield: str = "", sortorder: str = "ASC", limit: int = 100, page: int = 0, group_ids: str = "", sqlfilters: str = "", include_all_fields: bool = False) -> Any:
        params = {}
        if sortfield: params["sortfield"] = sortfield
        if sortorder != "ASC": params["sortorder"] = sortorder
        if limit != 100: params["limit"] = limit
        if page != 0: params["page"] = page
        if group_ids: params["group_ids"] = group_ids
        if sqlfilters: params["sqlfilters"] = sqlfilters
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get("/users/groups", api_key, params=params)

    async def users_get_group(self, group: int, api_key: Optional[str] = None, load_members: int = 0, includepermissions: int = 0, include_all_fields: bool = False) -> Any:
        params = {}
        if load_members: params["load_members"] = load_members
        if includepermissions: params["includepermissions"] = includepermissions
        if not include_all_fields: params["properties"] = BASE_COMMON
        return await self.get(f"/users/groups/{group}", api_key, params=params or None)

    async def users_get_user_groups(self, id: int, api_key: Optional[str] = None) -> Any:
        return await self.get(f"/users/{id}/groups", api_key)
