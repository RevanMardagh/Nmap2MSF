import json
from typing import Dict, List, Any
from pathlib import Path

DEFAULT_LOOKUP_PATH = Path('module_lookup.json')


def load_lookup(path: str = None) -> Dict[str, List[Dict[str, Any]]]:
    p = Path(path) if path else DEFAULT_LOOKUP_PATH
    if p.exists():
        try:
            with p.open('r', encoding='utf-8') as fh:
                data = json.load(fh)
                # normalize keys to lowercase
                return {k.lower(): v for k, v in data.items()}
        except Exception as e:
            raise RuntimeError(f"Failed loading lookup from {p}: {e}")
    # fallback default (minimal)
    return {
        'ftp': [
            {'module': 'auxiliary/scanner/ftp/anonymous', 'action': 'run', 'use_setg': True, 'rhost_param': 'RHOSTS', 'extra_options': {}},
        ]
    }


def find_modules_for_service(lookup: Dict[str, List[Dict[str, Any]]], service_name: str) -> List[Dict[str, Any]]:
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
