import logging
import requests
import pendulum
from typing import List, Optional

from .config import CRUNCHBASE_KEY
from .models import InvestmentDeal
from .uuid_cache import UuidCache

_log = logging.getLogger(__name__)

class CrunchbaseClient:
    BASE = "https://api.crunchbase.com/v4/data/searches/funding_rounds"

    def __init__(self, uuid_cache: UuidCache):
        self.cache = uuid_cache

    def _search_body(self, investor_id: str, since_iso: str | None = None) -> dict:
        """Return the JSON body for the Search API POST.

        If ``since_iso`` is provided, we add a predicate to fetch deals announced
        on or after that date (inclusive). When ``since_iso`` is *None* we omit
        the date filter altogether, effectively requesting all historical
        rounds associated with the investor.
        """

        query = [
            {
                "type": "predicate",
                "field_id": "investor_identifiers",
                "operator_id": "includes",
                "values": [investor_id],
            },
        ]

        if since_iso:
            query.append(
                {
                    "type": "predicate",
                    "field_id": "announced_on",
                    "operator_id": "gte",
                    "values": [since_iso],
                }
            )

        return {
            "field_ids": [
                "identifier",
                "announced_on",
                "funded_organization_identifier",
                "money_raised",
                "investment_type",
                "investor_identifiers",
            ],
            "order": [{"field_id": "announced_on", "sort": "desc"}],
            "query": query,
        }

    def get_recent_deals(
        self, vc_name: str, days_back: Optional[int] = 7
    ) -> List[InvestmentDeal]:
        vc_uuid = self.cache.get_uuid(vc_name)
        if not vc_uuid:
            return []

        since_iso = (
            None
            if not days_back or days_back <= 0
            else pendulum.now().subtract(days=days_back).to_date_string()
        )
        body = self._search_body(vc_uuid, since_iso)
        params = {"user_key": CRUNCHBASE_KEY}

        resp = requests.post(self.BASE, params=params, json=body, timeout=30)
        resp.raise_for_status()
        rows = resp.json().get("entities", [])

        deals: List[InvestmentDeal] = []
        for row in rows:
            props = row["properties"]
            org = (
                props.get("funded_organization_identifier")
                or props.get("organization_identifier")
            )
            if org is None:
                _log.debug("Skipping row without organization identifier: %s", row)
                continue
            deals.append(
                InvestmentDeal(
                    vc_name=vc_name,
                    company_name=org["value"],
                    announced_date=row["properties"]["announced_on"],
                    round_type=row["properties"]["investment_type"],
                    amount_usd=row["properties"].get("money_raised", {"value": None})["value"],
                    crunchbase_url=f'https://www.crunchbase.com/organization/{org["permalink"]}',
                )
            )
        _log.info("%s – fetched %d deals", vc_name, len(deals))
        return deals
