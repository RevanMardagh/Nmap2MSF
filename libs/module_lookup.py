"""module_lookup.py
Load the module lookup table from JSON (editable) and provide lookup helpers.
"""
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

DEFAULT_LOOKUP_PATH = Path('../database/module_lookup.json')
AI_LOOKUP_PATH = Path('../database/ai_lookup.json')


def _load_json_file(path: Path) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """Internal helper to load a JSON file safely and normalize keys."""
    if not path.exists():
        return None
    try:
        with path.open('r', encoding='utf-8') as fh:
            data = json.load(fh)
            if not data:
                return None
            return {k.lower(): v for k, v in data.items()}
    except Exception as e:
        raise RuntimeError(f"Failed loading lookup from {path}: {e}")


def load_lookup(path: str = None, ai_support: bool = False) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """Load the lookup JSON(s) and return a dict mapping service -> module descriptors.

    Behavior:
    - Always loads module_lookup.json
    - If ai_support=True, also loads ai_lookup.json
    - When merging, module_lookup.json entries take priority
    """
    main_path = Path(path) if path else DEFAULT_LOOKUP_PATH
    main_lookup = _load_json_file(main_path)
    if not ai_support:
        # Only standard lookup
        return main_lookup

    ai_lookup = _load_json_file(AI_LOOKUP_PATH)

    if not ai_lookup and not main_lookup:
        return None
    if not ai_lookup:
        return main_lookup
    if not main_lookup:
        return ai_lookup

    # Merge with module_lookup.json taking priority
    merged = ai_lookup.copy()
    merged.update(main_lookup)
    print(merged)
    return merged


def find_modules_for_service(
    lookup: Optional[Dict[str, List[Dict[str, Any]]]],
    service_name: str
) -> List[Dict[str, Any]]:
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
    # Example manual test
    lookup = load_lookup(ai_support=False)
    import pprint
    pprint.pprint(find_modules_for_service(lookup, 'netbios-ssn'))
