"""module_lookup.py
Load the module lookup table from JSON (editable) and provide lookup helpers.
"""
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

DEFAULT_LOOKUP_PATH = Path('../database/module_lookup.json')


def load_lookup(path: str = None) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """Load the lookup JSON and return a dict mapping service -> module descriptors.

    If the lookup file does not exist or contains no mappings, return None.
    This avoids silently falling back to a built-in default; the caller should
    handle the missing lookup explicitly.
    """
    p = Path(path) if path else DEFAULT_LOOKUP_PATH
    if not p.exists():
        return None

    try:
        with p.open('r', encoding='utf-8') as fh:
            data = json.load(fh)
            if not data:
                return None
            # normalize keys to lowercase
            return {k.lower(): v for k, v in data.items()}
    except Exception as e:
        raise RuntimeError(f"Failed loading lookup from {p}: {e}")


def find_modules_for_service(lookup: Optional[Dict[str, List[Dict[str, Any]]]], service_name: str) -> List[Dict[str, Any]]:
    """Return modules for the given service_name. If lookup is None or empty,
    return an empty list (no modules found).
    """
    if not lookup:
        return []
    sn = (service_name or '').lower()
    if not sn:
        return []
    if sn in lookup:
        return lookup[sn]
    # simple fuzzy match: substring in keys
    for key in lookup:
        if key in sn or sn in key:
            return lookup[key]
    return []


if __name__ == '__main__':
    lookup = load_lookup('')
    # print(find_modules_for_service(lookup, 'ftp'), "\n\n\r\r")

    import pprint
    pprint.pprint(find_modules_for_service(lookup, 'netbios-ssn'))