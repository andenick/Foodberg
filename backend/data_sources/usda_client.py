"""USDA AMS Market News client (MARS API v3.1).

Daily wholesale fruit & vegetable prices from the USDA Agricultural Marketing
Service terminal markets.

WHY THIS FILE WAS REWRITTEN
---------------------------
The previous implementation failed for two independent reasons:

1. It imported through a package-relative path that broke when the module was
   loaded standalone ("attempted relative import beyond top-level package" —
   the error still recorded against 'USDA Market News' in data_source_sync).
   This module now has NO relative imports and no package-relative side
   effects: it is importable as ``data_sources.usda_client``, as
   ``backend.data_sources.usda_client``, and as a standalone script.

2. It addressed reports by SLUG NAME and used a hardcoded slug dictionary of
   which 6 of 9 entries were simply wrong (Chicago was 'GX_FV020', the real
   slug is 'HX_FV020'; New York was 'JO_FV020', the real slug is 'NX_FV020').
   MARS v3.1 addresses reports by NUMERIC ``slug_id``::

       GET /reports/NX_FV020   -> HTTP 500
       GET /reports/2315       -> HTTP 200

   There is therefore no slug dictionary in this module at all. The market
   list is derived from the LIVE CATALOG (``GET /reports``, ~1055 records) and
   the city / state / market names come from each record's ``markets``,
   ``offices``, ``states`` and ``report_title`` fields. Discontinued markets
   are detected from the catalog's ``status`` field, never hardcoded.

ENDPOINTS
---------
    GET {BASE}/reports
        Report catalog. slug_id, slug_name, report_title, report_date,
        published_date, status, hasData, markets, offices, states,
        sectionNames.

    GET {BASE}/reports/{slug_id}
        Report envelopes (metadata only — NO price line items).

    GET {BASE}/reports/{slug_id}/Report%20Details?q=report_begin_date=MM/DD/YYYY
        The price line items. A date RANGE is supported with a colon:
        ``report_begin_date=07/01/2026:07/23/2026``.

CREDENTIAL
----------
HTTP Basic with the API key as the USERNAME and a BLANK password. The key is
read from the OS credential vault at call time and is never written to disk,
never logged, and never interpolated into a printed URL.

    keyring.get_password("usda-ams-mars", "andenick")

An environment variable (USDA_AMS_API_KEY / USDA_API_KEY) is accepted as a
fallback for container deployments where no OS vault exists.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence

import requests

__all__ = [
    "BASE_URL",
    "TERMINAL_FAMILIES",
    "USDAMarketNewsClient",
    "load_api_key",
]

BASE_URL = "https://marsapi.ams.usda.gov/services/v3.1"

KEYRING_SERVICE = "usda-ams-mars"
KEYRING_USERNAME = "andenick"
ENV_KEY_NAMES = ("USDA_AMS_API_KEY", "USDA_API_KEY", "USDA_MARS_API_KEY")

# Report families published for TERMINAL markets. Each was verified to return
# Report Details line items before being included here; shipping-point families
# (FV110 / FV120) are a different market type and are deliberately excluded.
TERMINAL_FAMILIES: Dict[str, str] = {
    "FV010": "Fruit",
    "FV020": "Vegetables",
    "FV030": "Onions and Potatoes",
    "FV040": "Nuts",
}

# Public landing page for the terminal-market programme (used for provenance).
PROGRAMME_LANDING = (
    "https://www.ams.usda.gov/market-news/fruit-and-vegetable-truck-rate-report"
)
MARS_LANDING = "https://marsapi.ams.usda.gov/"

_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_SLUG_RE = re.compile(r"^([A-Z]{2})_(FV\d{3})$")


class USDAApiKeyMissing(ValueError):
    """Raised when no AMS MARS credential can be located."""


def load_api_key() -> str:
    """Return the MARS API key from the OS credential vault (or env fallback).

    The key is returned, never printed and never persisted. Callers must not
    log the return value.
    """
    try:
        import keyring  # imported lazily: absent in some container images

        key = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if key:
            return key.strip()
    except Exception:  # noqa: BLE001 - vault unavailable is a normal fallback
        pass

    for name in ENV_KEY_NAMES:
        value = os.environ.get(name, "").strip()
        if value:
            return value

    raise USDAApiKeyMissing(
        "No USDA AMS Market News credential found. Store one in the OS vault "
        f"under service {KEYRING_SERVICE!r} / user {KEYRING_USERNAME!r}, or set "
        f"one of {', '.join(ENV_KEY_NAMES)}."
    )


def _as_mmddyyyy(value: Any) -> str:
    """Normalise a date to the MM/DD/YYYY form MARS expects."""
    if value is None:
        raise ValueError("a date is required")
    if isinstance(value, _dt.datetime):
        value = value.date()
    if isinstance(value, _dt.date):
        return value.strftime("%m/%d/%Y")
    text = str(value).strip()
    if _DATE_RE.match(text):
        return text
    # Accept ISO input (YYYY-MM-DD) for convenience.
    try:
        return _dt.date.fromisoformat(text).strftime("%m/%d/%Y")
    except ValueError as exc:
        raise ValueError(
            f"unrecognised date {value!r}; use MM/DD/YYYY or YYYY-MM-DD"
        ) from exc


def mmddyyyy_to_iso(value: Any) -> Optional[str]:
    """MM/DD/YYYY -> YYYY-MM-DD. Returns None when unparseable."""
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if _DATE_RE.match(text):
        month, day, year = text.split("/")
        return f"{year}-{month}-{day}"
    try:
        return _dt.date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        return None


def _clean(value: Any) -> Optional[str]:
    """Collapse AMS 'absent' sentinels to None; never invent a value."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.upper() in {"N/A", "NA", "NULL", "NONE"}:
        return None
    return text


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _market_key(label: str) -> str:
    """'New York Terminal Market' -> 'new_york'."""
    label = re.sub(r"\s*terminal market\s*$", "", label, flags=re.I).strip()
    label = re.sub(r"[^0-9A-Za-z]+", "_", label).strip("_").lower()
    return label


class USDAMarketNewsClient:
    """Thin, catalog-driven client for AMS MARS v3.1 terminal-market reports."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: int = 180,
        max_retries: int = 5,
        request_delay: float = 0.25,
        base_url: str = BASE_URL,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.request_delay = request_delay
        # Read the credential at construction; it lives only in memory.
        self._api_key = api_key or load_api_key()
        self.session = session or requests.Session()
        self.session.auth = (self._api_key, "")
        self.session.headers.update({"Accept": "application/json"})
        self._catalog: Optional[List[Dict[str, Any]]] = None
        self._markets: Optional[List[Dict[str, Any]]] = None
        self._last_request_at = 0.0

    # -- plumbing ---------------------------------------------------------

    def _throttle(self) -> None:
        if self.request_delay <= 0:
            return
        wait = self.request_delay - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)

    def _get(self, path: str, params: Optional[Dict[str, str]] = None) -> Any:
        """GET with backoff on 429 / 5xx. Never logs the URL (it carries auth)."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_error: Optional[str] = None
        for attempt in range(self.max_retries):
            self._throttle()
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                self._last_request_at = time.monotonic()
            except requests.RequestException as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                time.sleep(min(2 ** attempt, 30))
                continue

            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as exc:
                    last_error = f"non-JSON response: {exc}"
                    time.sleep(min(2 ** attempt, 30))
                    continue

            if response.status_code in (429, 500, 502, 503, 504):
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if (retry_after or "").isdigit() else min(2 ** attempt, 30)
                last_error = f"HTTP {response.status_code}"
                time.sleep(delay)
                continue

            if response.status_code in (401, 403):
                raise USDAApiKeyMissing(
                    f"AMS MARS rejected the credential (HTTP {response.status_code}). "
                    "Check the stored key."
                )

            raise requests.HTTPError(
                f"AMS MARS returned HTTP {response.status_code} for /{path.lstrip('/')}"
            )

        raise requests.HTTPError(
            f"AMS MARS request to /{path.lstrip('/')} failed after "
            f"{self.max_retries} attempts ({last_error})"
        )

    # -- catalog ----------------------------------------------------------

    def list_reports(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """The full MARS report catalog (~1055 records)."""
        if self._catalog is None or refresh:
            payload = self._get("reports")
            if not isinstance(payload, list):
                raise ValueError("unexpected /reports payload shape")
            self._catalog = payload
        return self._catalog

    def list_terminal_markets(
        self,
        families: Optional[Sequence[str]] = None,
        include_discontinued: bool = False,
        refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """Terminal-market report streams, derived from the live catalog.

        Returns one record per (city, report family) with the NUMERIC slug_id
        that the Report Details endpoint actually needs. Nothing here is
        hardcoded: the city, state, market name and discontinuation status all
        come from the catalog record.
        """
        wanted = tuple(families) if families else tuple(TERMINAL_FAMILIES)
        cache_key = (wanted, include_discontinued)
        if self._markets is None or refresh or getattr(self, "_markets_key", None) != cache_key:
            records: List[Dict[str, Any]] = []
            for rec in self.list_reports(refresh=refresh):
                slug_name = (rec.get("slug_name") or "").strip()
                match = _SLUG_RE.match(slug_name)
                if not match or match.group(2) not in wanted:
                    continue

                title = (rec.get("report_title") or "").strip()
                markets = [m for m in (rec.get("markets") or []) if m]
                offices = [o for o in (rec.get("offices") or []) if o]
                states = [s for s in (rec.get("states") or []) if s]

                # A terminal-market report always names a "... Terminal Market".
                market_name = markets[0] if markets else None
                if not market_name or "terminal market" not in market_name.lower():
                    continue

                status = (rec.get("status") or "").strip()
                discontinued = (
                    status.lower() == "discontinued"
                    or "(discontinued)" in title.lower()
                )
                if discontinued and not include_discontinued:
                    continue

                # Domestic terminal markets carry a US state; the retired
                # foreign ones (Tokyo, Rotterdam, ...) carry none.
                state = states[0] if states else None

                city = re.sub(
                    r"\s*terminal market\s*$", "", market_name, flags=re.I
                ).strip()
                # 'New York (Bronx), New York - SC' -> office city, when useful.
                office = offices[0] if offices else None

                records.append(
                    {
                        "slug_id": str(rec.get("slug_id")),
                        "slug_name": slug_name,
                        "family": match.group(2),
                        "family_label": TERMINAL_FAMILIES.get(match.group(2), match.group(2)),
                        "key": _market_key(market_name),
                        "market": market_name,
                        "city": city,
                        "state": state,
                        "office": office,
                        "report_title": title,
                        "status": status or None,
                        "discontinued": discontinued,
                        "has_data": bool(rec.get("hasData")),
                        "latest_report_date": rec.get("report_date"),
                        "published_date": rec.get("published_date"),
                        "sections": rec.get("sectionNames") or [],
                        "detail_url": self.report_details_url(rec.get("slug_id")),
                    }
                )
            records.sort(key=lambda r: (r["key"], r["family"]))
            self._markets = records
            self._markets_key = cache_key
        return list(self._markets)

    def market_keys(self, **kwargs: Any) -> List[str]:
        """Sorted distinct city keys ('new_york', 'chicago', ...)."""
        return sorted({m["key"] for m in self.list_terminal_markets(**kwargs)})

    def resolve_market(
        self, market: str, families: Optional[Sequence[str]] = None
    ) -> List[Dict[str, Any]]:
        """Resolve a user-supplied market token to catalog records.

        Accepts a city key ('new_york', 'new york'), a slug name ('NX_FV020'),
        or a numeric slug_id ('2315'). Returns every matching report family,
        or [] when nothing matches.
        """
        token = (market or "").strip()
        if not token:
            return []
        records = self.list_terminal_markets(families=families)
        norm = _market_key(token)

        exact = [r for r in records if r["slug_name"].upper() == token.upper()]
        if exact:
            return exact
        by_id = [r for r in records if r["slug_id"] == token]
        if by_id:
            return by_id
        by_key = [r for r in records if r["key"] == norm]
        if by_key:
            return by_key
        return [r for r in records if norm and norm in r["key"]]

    # -- report details ---------------------------------------------------

    def report_details_url(self, slug_id: Any) -> str:
        """Public, credential-free URL of a report's Report Details section."""
        return f"{self.base_url}/reports/{slug_id}/Report%20Details"

    def fetch_report_details(
        self,
        slug_id: Any,
        begin_date: Any,
        end_date: Any = None,
    ) -> List[Dict[str, Any]]:
        """Price line items for one report between two dates (inclusive).

        ``begin_date``/``end_date`` accept MM/DD/YYYY, YYYY-MM-DD or date
        objects. MARS accepts a colon-delimited range in the same field.
        Returns [] when the report published nothing in the window — an empty
        window is stored as nothing, never as a placeholder row.
        """
        begin = _as_mmddyyyy(begin_date)
        query = f"report_begin_date={begin}"
        if end_date is not None:
            end = _as_mmddyyyy(end_date)
            if end != begin:
                query = f"report_begin_date={begin}:{end}"

        payload = self._get(f"reports/{slug_id}/Report%20Details", {"q": query})
        if isinstance(payload, dict):
            payload = payload.get("results") or payload.get("report") or []
        if not isinstance(payload, list):
            return []
        return payload

    @staticmethod
    def normalize_detail_row(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten one MARS detail record into the ams_wholesale_prices shape.

        Every value is either the publisher's own value or None. Nothing is
        defaulted, inferred or filled in.
        """
        package = _clean(raw.get("package"))
        city = _clean(raw.get("market_location_city")) or _clean(raw.get("office_city"))
        state = _clean(raw.get("market_location_state")) or _clean(raw.get("office_state"))
        geography = ", ".join(p for p in (city, state) if p) or None

        return {
            "report_date": mmddyyyy_to_iso(raw.get("report_date")),
            "published_date": raw.get("published_date"),
            "slug_id": str(raw.get("slug_id")) if raw.get("slug_id") is not None else None,
            "slug_name": _clean(raw.get("slug_name")),
            "report_title": _clean(raw.get("report_title")),
            "market": _clean(raw.get("market_location_name")),
            "city": city,
            "state": state,
            "geography": geography,
            "category": _clean(raw.get("category")),
            "commodity": _clean(raw.get("commodity")),
            "variety": _clean(raw.get("variety")),
            "package": package,
            "grade": _clean(raw.get("grade")),
            "item_size": _clean(raw.get("item_size")),
            "organic": _clean(raw.get("organic")),
            "origin": _clean(raw.get("origin")),
            # 'origin_detail' is not emitted by every MARS report family; it is
            # read when present and left NULL when the publisher omits it.
            "origin_detail": _clean(raw.get("origin_detail")),
            "repack": _clean(raw.get("repack")),
            "storage": _clean(raw.get("storage")),
            "quality": _clean(raw.get("quality")),
            "condition": _clean(raw.get("condition")),
            "appearance": _clean(raw.get("appearance")),
            "crop": _clean(raw.get("crop")),
            "district": _clean(raw.get("district")),
            "environment": _clean(raw.get("environment")),
            "transportation_mode": _clean(raw.get("transportation_mode")),
            # MARS names this field 'unit_sales'; older docs say 'unit_of_sale'.
            "unit_of_sale": _clean(raw.get("unit_sales")) or _clean(raw.get("unit_of_sale")),
            "low_price": _to_float(raw.get("low_price")),
            "high_price": _to_float(raw.get("high_price")),
            "mostly_low_price": _to_float(raw.get("mostly_low_price")),
            "mostly_high_price": _to_float(raw.get("mostly_high_price")),
            "market_tone_comments": _clean(raw.get("market_tone_comments")),
            # The price is quoted for the package, so the package IS the unit.
            "unit": f"USD per {package}" if package else None,
        }

    # -- convenience / backwards-compatible surface -----------------------

    def get_terminal_market_prices(
        self,
        market: str = "new_york",
        report_date: Any = None,
        families: Optional[Sequence[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Latest (or dated) wholesale prices for one terminal-market city.

        Kept under this name because ``backend/main.py`` calls it. Returns None
        when the market cannot be resolved; returns a payload with an empty
        ``commodities`` map when the market published nothing that day.
        """
        records = self.resolve_market(market, families=families)
        if not records:
            return None

        commodities: Dict[str, List[Dict[str, Any]]] = {}
        reports: List[Dict[str, Any]] = []
        retrieved_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
        row_total = 0

        for rec in records:
            day = report_date or rec.get("latest_report_date")
            if not day:
                continue
            try:
                rows = self.fetch_report_details(rec["slug_id"], day)
            except (requests.HTTPError, ValueError):
                continue

            reports.append(
                {
                    "slug_id": rec["slug_id"],
                    "slug_name": rec["slug_name"],
                    "family": rec["family"],
                    "family_label": rec["family_label"],
                    "report_title": rec["report_title"],
                    "report_date": mmddyyyy_to_iso(day),
                    "rows": len(rows),
                    "retrieval_url": rec["detail_url"],
                }
            )
            row_total += len(rows)

            for raw in rows:
                item = self.normalize_detail_row(raw)
                name = (item["commodity"] or "unknown").lower()
                commodities.setdefault(name, []).append(
                    {
                        "commodity": item["commodity"],
                        "variety": item["variety"],
                        "package": item["package"],
                        "grade": item["grade"],
                        "itemSize": item["item_size"],
                        "organic": item["organic"],
                        "origin": item["origin"],
                        "repack": item["repack"],
                        "storage": item["storage"],
                        "quality": item["quality"],
                        "condition": item["condition"],
                        "environment": item["environment"],
                        "unitOfSale": item["unit_of_sale"],
                        "unit": item["unit"],
                        "lowPrice": item["low_price"],
                        "highPrice": item["high_price"],
                        "mostlyLowPrice": item["mostly_low_price"],
                        "mostlyHighPrice": item["mostly_high_price"],
                        "marketTone": item["market_tone_comments"],
                        "reportDate": item["report_date"],
                        "slugName": item["slug_name"],
                    }
                )

        head = records[0]
        return {
            "timestamp": retrieved_at,
            "retrieved_at": retrieved_at,
            "market": head["market"],
            "marketKey": head["key"],
            "city": head["city"],
            "state": head["state"],
            "reportDate": mmddyyyy_to_iso(report_date or head.get("latest_report_date")),
            "source": "USDA AMS Market News",
            "reports": reports,
            "rowCount": row_total,
            "commodities": commodities,
        }

    def iter_report_details(
        self,
        slug_id: Any,
        start_date: Any,
        end_date: Any,
        chunk_days: int = 31,
    ) -> Iterable[List[Dict[str, Any]]]:
        """Yield Report Details in date chunks so no single response is huge."""
        start = _dt.datetime.strptime(_as_mmddyyyy(start_date), "%m/%d/%Y").date()
        stop = _dt.datetime.strptime(_as_mmddyyyy(end_date), "%m/%d/%Y").date()
        cursor = start
        while cursor <= stop:
            window_end = min(cursor + _dt.timedelta(days=chunk_days - 1), stop)
            yield self.fetch_report_details(slug_id, cursor, window_end)
            cursor = window_end + _dt.timedelta(days=1)


def _selftest() -> int:
    """Catalog + one live Report Details fetch. Prints no credential."""
    client = USDAMarketNewsClient()
    markets = client.list_terminal_markets()
    print(f"catalog records          : {len(client.list_reports())}")
    print(f"active terminal streams  : {len(markets)}")
    print(f"active terminal cities   : {len(client.market_keys())}")
    for rec in markets[:8]:
        print(
            f"  {rec['slug_id']:>5}  {rec['slug_name']:<10} {rec['family_label']:<20}"
            f" {rec['city']}, {rec['state']}"
        )
    ny = [m for m in markets if m["key"] == "new_york" and m["family"] == "FV020"]
    if ny:
        rows = client.fetch_report_details(ny[0]["slug_id"], ny[0]["latest_report_date"])
        print(f"\nNY vegetables {ny[0]['latest_report_date']}: {len(rows)} line items")
        if rows:
            sample = client.normalize_detail_row(rows[0])
            print(f"  sample: {sample['commodity']} / {sample['package']} / "
                  f"{sample['origin']} / {sample['low_price']}-{sample['high_price']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
