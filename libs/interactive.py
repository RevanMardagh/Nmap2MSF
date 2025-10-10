"""
libs/interactive.py

Interactive module selection for nmap2msf.

Shows only service and module name during prompts and summary.
"""
from typing import List, Dict, Callable, Optional
import fontstyle

ResponseFn = Callable[[str], str]

def _print_red(text: str):
    """Print in orange using fontstyle, fallback to plain print."""
    try:
        print(fontstyle.apply(text, 'bold//purple'))
    except Exception:
        print(text)


def interactive_select_modules(
    hosts: List[Dict],
    lookup: Dict[str, List[Dict]],
    prompt_fn: Optional[ResponseFn] = None
) -> Dict[str, List[Dict]]:
    """
    Walk hosts -> ports -> candidate modules and ask the user whether to include each module.

    Returns:
        selected_lookup: dict mapping service -> list of module dicts the user approved.

    Prompt responses:
        y / yes  => include this module
        n / no   => do not include
        a        => yes to all remaining
        s        => no to all remaining
        q        => quit interactive selection and proceed with current selections
    """
    if prompt_fn is None:
        prompt_fn = input

    _print_red("\nInteractive mode: confirm modules to include.")
    _print_red("Respond with: y = yes, n = no, a = yes to all remaining, s = no to all remaining, q = quit interactive\n")

    selected_lookup: Dict[str, List[Dict]] = {}
    seen_modules = set()  # will store id(mod)
    yes_all = False
    no_all = False
    quit_early = False

    for host in hosts:
        if quit_early:
            break
        host_ip = host.get('ip') or host.get('hostname') or "<unknown>"
        for port in host.get('ports', []):
            if quit_early:
                break
            service = (port.get('service') or "").lower()
            if not service:
                continue
            modules = lookup.get(service, [])
            if not modules:
                continue

            for mod in modules:
                mod_id = id(mod)
                if mod_id in seen_modules:
                    if mod in selected_lookup.get(service, []):
                        pass
                    seen_modules.add(mod_id)
                    continue

                if yes_all:
                    selected_lookup.setdefault(service, []).append(mod)
                    seen_modules.add(mod_id)
                    continue
                if no_all:
                    seen_modules.add(mod_id)
                    continue

                # module name only
                module_name = mod.get("module", str(mod))
                prompt = f"service={service}\tcandidate module: {module_name} — include? (y/n/a/s/q) "
                try:
                    resp = prompt_fn(prompt).strip().lower()
                except (KeyboardInterrupt, EOFError):
                    _print_red("\nInteractive input cancelled — proceeding with selected modules so far.")
                    no_all = True
                    break

                if resp in ('y', 'yes'):
                    selected_lookup.setdefault(service, []).append(mod)
                elif resp in ('n', 'no', ''):
                    pass
                elif resp == 'a':
                    selected_lookup.setdefault(service, []).append(mod)
                    yes_all = True
                elif resp == 's':
                    no_all = True
                elif resp == 'q':
                    _print_red("Quitting interactive selection and proceeding with current selections.")
                    quit_early = True
                    break
                else:
                    _print_red("Unrecognized response — skipping (treated as 'no').")

                seen_modules.add(mod_id)

    # dedupe lists (preserve order)
    for svc, mods in list(selected_lookup.items()):
        seen = set()
        deduped = []
        for m in mods:
            mid = id(m)
            if mid not in seen:
                deduped.append(m)
                seen.add(mid)
        selected_lookup[svc] = deduped

    if not selected_lookup:
        _print_red("[i] No modules were selected in interactive mode. The .rc will be generated without modules.")
    else:
        _print_red("[i] Interactive selection complete. Modules selected for inclusion:")
        for svc, mods in selected_lookup.items():
            names = [m.get("module", str(m)) for m in mods]
            _print_red(f"  {svc}: {', '.join(names)}")

    return selected_lookup
