"""CSV/JSON file cache implementation."""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

from stock_analyst.cache.base import Cache


class CsvCache(Cache):
    def __init__(self, cache_dir: str, default_ttl: int = 3600) -> None:
        self._dir = Path(cache_dir).expanduser()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._default_ttl = default_ttl

    def _path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace(":", "_")
        return self._dir / f"{safe_key}.json"

    def _is_expired(self, path: Path) -> bool:
        if not path.exists():
            return True
        age = time.time() - path.stat().st_mtime
        return age > self._default_ttl

    def get(self, key: str) -> Optional[Any]:
        path = self._path(key)
        if self._is_expired(path):
            return None
        return json.loads(path.read_text())

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        path = self._path(key)
        path.write_text(json.dumps(value, default=str))

    def exists(self, key: str) -> bool:
        return not self._is_expired(self._path(key))
