"""
Lightweight local cache for VC fund UUIDs.

If the cache file doesn’t exist or lacks a VC name,
`UuidCache.get_uuid(vc_name)` performs an Autocomplete
call to Crunchbase v4 and stores the mapping.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import requests

from .config import CRUNCHBASE_KEY, CACHE_PATH

_log = logging.getLogger(__name__)

class UuidCache:
    def __init__(self, path: Path = CACHE_PATH):
        self.path = path
        self._store: Dict[str, str] = {}
        if path.exists():
            self._store.update(json.loads(path.read_text()))

    def save(self) -> None:
        self.path.write_text(json.dumps(self._store, indent=2))

    def get_uuid(self, vc_name: str) -> Optional[str]:
        if vc_name in self._store:
            return self._store[vc_name]

        # Attempt to resolve the UUID in both the "organizations" and "people" collections.
        collections = ("organizations", "people")
        for collection in collections:
            url = "https://api.crunchbase.com/v4/data/autocompletes"
            params = {
                "user_key": CRUNCHBASE_KEY,
                "query": vc_name.lower(),
                "collection_ids": collection,
            }
            try:
                resp = requests.get(url, params=params, timeout=20)
                resp.raise_for_status()
            except requests.HTTPError as exc:
                _log.debug("Autocomplete request for %s failed against collection %s: %s", vc_name, collection, exc)
                continue

            hits = resp.json().get("entities", [])
            if not hits:
                continue

            # Entities in people autocomplete may not have nested "identifier" key.
            top_hit = hits[0]
            uuid = (
                top_hit.get("identifier", {}).get("uuid")
                or top_hit.get("uuid")
            )

            if uuid:
                self._store[vc_name] = uuid
                self.save()
                return uuid

        _log.warning("No UUID found for %s", vc_name)
        return None
