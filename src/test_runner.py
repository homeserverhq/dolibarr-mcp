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
    """Check if an MCP tool response contains an error. Returns error string or None."""
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
    """Extract the parsed JSON content from an MCP tool response."""
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


async def run_test(
    session: MCPSession,
    label: str,
    tool: str,
    params: dict[str, Any] = None,
    prereq: Optional[str] = None,
) -> bool:
    """Run a single MCP tool test with optional prerequisite check."""
    if params is None:
        params = {}
    if prereq and prereq not in created:
        results.append({
            "label": label, "tool": tool, "status": "SKIPPED",
            "reason": f"Missing prerequisite: {prereq}"
        })
        log(f"  SKIP {label}: missing {prereq}")
        return False
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
    """Like run_test but stores the parsed response in the global store dict."""
    ok = await run_test(session, label, tool, params, prereq)
    if ok and store_key:
        for r in results:
            if r["label"] == label and r["status"] == "PASSED":
                store[store_key] = r.get("data")
                break
    return ok


def pick_id(key: str) -> Optional[str]:
    """Extract the 'id' field from a stored tool response."""
    entry = store.get(key, {})
    if isinstance(entry, dict):
        return entry.get("id")
    return None


def make_name(base: str) -> str:
    """Generate a unique test resource name using the run ID prefix."""
    return f"t{rid}-{base}"


async def run_verify_delete(
    session: MCPSession,
    label: str,
    get_tool: str,
    params: dict[str, Any] = None,
) -> bool:
    """Verify a resource was deleted by calling the GET tool and expecting 'not found'."""
    if params is None:
        params = {}
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
    ("ThirdParty", "thirdparties_create",
     {"name": make_name("TP"), "client": 1, "fournisseur": 1, "code_client": f"CU{time.strftime('%y%m')}-{rid[-4:]}", "code_fournisseur": f"SU{time.strftime('%y%m')}-{rid[-4:]}"},
     "thirdparties_list", "thirdparties_get",
     "thirdparties_update", {"phone": "555-0000"},
     "thirdparties_delete"),
    ("Contact", "contacts_create",
     {"lastname": make_name("L"), "socid": 1, "firstname": "Test"},
     "contacts_list", "contacts_get",
     "contacts_update", {"firstname": "Updated"},
     "contacts_delete"),
    ("Order", "orders_create",
     {"socid": 1, "date": "2026-06-21T12:00:00+00:00"},
     "orders_list", "orders_get",
     "orders_update", {"note_public": "Updated"},
     "orders_delete"),
    ("Invoice", "invoices_create",
     {"socid": 1, "date": "2026-06-21T12:00:00+00:00", "type": 0},
     "invoices_list", "invoices_get",
     "invoices_update", {"note_public": "Updated"},
     "invoices_delete"),
    ("BankAccount", "bankaccounts_create",
     {"ref": make_name("BA"), "label": make_name("Bank"), "type": 0, "currency_code": "EUR", "account_number": "FR7630001007941234567890185", "country_id": 1},
     "bankaccounts_list", "bankaccounts_get",
     "bankaccounts_update", {"label": "Updated Bank"},
     "bankaccounts_delete"),
    ("Intervention", "interventions_create",
     {"socid": 1, "ref": make_name("IN")},
     "interventions_list", "interventions_get",
     "interventions_update", {"note_public": "Updated"},
     "interventions_delete"),
    ("ExpenseReport", "expense_reports_create",
     {"fk_user": 1, "date_debut": "2026-06-21T12:00:00+00:00", "date_fin": "2026-06-22T12:00:00+00:00", "fk_user_author": 1},
     "expense_reports_list", "expense_reports_get",
     "expense_reports_update", {"note_public": "Updated"},
     "expense_reports_delete"),
    ("AgendaEvent", "agenda_events_create",
     {"type_code": "AC_OTH", "datep": "2026-06-21T14:00:00+00:00", "label": make_name("Event")},
     "agenda_events_list", "agenda_events_get",
     "agenda_events_update", {"label": "Updated Event"},
     "agenda_events_delete"),
    ("Ticket", "tickets_create",
     {"subject": make_name("Ticket"), "type_code": "COM", "severity_code": "MINOR", "category_code": "OTH"},
     "tickets_list", "tickets_get",
     "tickets_update", {"subject": "Updated Ticket"},
     "tickets_delete"),
]

LIST_ONLY_TOOLS = [
    ("User", "users_list"),
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
            label = entry[0]
            list_tool_name = entry[3]
            await run_test(session, f"B2 list_{label.lower()}", list_tool_name)
        for label, list_tool in LIST_ONLY_TOOLS:
            await run_test(session, f"B2 list_{label.lower()}", list_tool)

        # ------------------------------------------------------------------
        # Phase 3: CRUD Cycle (data-driven from RESOURCE_TESTS)
        # ------------------------------------------------------------------
        log("\n=== Phase 3: Resource CRUD Cycle ===")
        for entry in RESOURCE_TESTS:
            label, create_tool, create_params, _, get_tool, update_tool, \
                update_params, delete_tool = entry
            key = label.lower()

            ok = await run_test_with_store(
                session, f"C1 create_{key}", create_tool, create_params,
                store_key=f"create_{key}"
            )
            cid = pick_id(f"create_{key}") if ok else None
            if cid:
                created[f"create_{key}"] = cid

            if cid:
                await run_test_with_store(
                    session, f"C2 get_{key}_by_id", get_tool,
                    {"id": cid}, store_key=f"get_{key}"
                )

                upd = dict(update_params)
                upd["id"] = cid
                await run_test(
                    session, f"C3 update_{key}", update_tool, upd
                )

                await run_test(
                    session, f"C4 delete_{key}_by_id", delete_tool,
                    {"id": cid}
                )

                await run_verify_delete(
                    session, f"C5 verify_delete_{key}", get_tool,
                    {"id": cid}
                )
            else:
                for phase in ("C2", "C3", "C4", "C5"):
                    results.append({
                        "label": f"{phase}_{key}", "tool": get_tool,
                        "status": "SKIPPED",
                        "reason": "No ID from create — prerequisite failed"
                    })

        # ------------------------------------------------------------------
        # Phase 4: Extended Tool Tests (TOON, categories, contacts, etc.)
        # ------------------------------------------------------------------
        log("\n=== Phase 4: Domain-Specific Tools ===")

        await run_test(session, "D2 thirdparties_outstanding_proposals",
                        "thirdparties_get_outstanding_proposals", {"id": 1})
        await run_test(session, "D3 thirdparties_outstanding_orders",
                        "thirdparties_get_outstanding_orders", {"id": 1})
        await run_test(session, "D4 thirdparties_outstanding_invoices",
                        "thirdparties_get_outstanding_invoices", {"id": 1})

        await run_test(session, "D19 orders_get_lines",
                        "orders_get_lines", {"id": 1})
        await run_test(session, "D20 orders_get_contacts",
                        "orders_get_contacts", {"id": 1})

        await run_test(session, "D42 interventions_get_contacts",
                        "interventions_get_contacts", {"id": 1})

        await run_test(session, "D43 expense_reports_get_lines",
                        "expense_reports_get_lines", {"id": 1})

        await run_test(session, "D45 categories_get_for_object",
                        "categories_get_for_object", {"type": "product", "id": 1})

        await run_test(session, "D48 users_get",
                        "users_get", {"id": 1})
        await run_test(session, "D49 users_get_by_login",
                        "users_get_by_login", {"login": "admin"})
        await run_test(session, "D50 users_get_info",
                        "users_get_info")
        await run_test(session, "D51 users_list_groups",
                        "users_list_groups")
        await run_test(session, "D52 users_get_user_groups",
                        "users_get_user_groups", {"id": 1})

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
