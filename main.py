#!/usr/bin/python3

import argparse
import os
import fontstyle
from libs.nmap_parser import parse_nmap_xml
from libs.module_lookup import load_lookup
from libs.rc_writer import write_rc
from libs.ask_ai import generate_ai_modules
from libs.interactive import interactive_select_modules


def main():
    p = argparse.ArgumentParser(description='Generate Metasploit .rc from Nmap XML (modular)')
    p.add_argument('-i', '--input', required=True, help='Nmap XML file')
    p.add_argument('-o', '--output', required=False, help='Output .rc file')
    p.add_argument('--lookup', help='Path to module_lookup.json (optional)')
    p.add_argument('-s','--ai-support', help='Enable AI-provided modules', action='store_true')
    p.add_argument('-c','--interactive', help='Interactive mode to manually select modules', action='store_true')
    args = p.parse_args()



    # helper to print in orange using fontstyle
    def o(text: str):
        # use fontstyle to apply orange — keep as small wrapper so it's easy to change later
        try:
            print(fontstyle.apply(text, 'yellow'))
        except Exception:
            # fallback to plain print if fontstyle doesn't support 'orange' on this system
            print(text)

    # ---- basic path handling ----
    default_lookup = 'database/module_lookup.json'
    lookup_path = args.lookup if args.lookup else default_lookup
    used_default_lookup = False
    if args.lookup and not os.path.exists(args.lookup):
        print(f"[i] Provided lookup file '{args.lookup}' not found — falling back to default: {default_lookup}")
        lookup_path = default_lookup
        used_default_lookup = True
    elif not args.lookup:
        used_default_lookup = True

    # determine output filename (so we can print it now)
    computed_output = args.output if args.output else f"{os.path.splitext(os.path.basename(args.input))[0]}.rc"

    # --- print requested lines in orange ---
    o(f"[*] Input file: {args.input}")
    o(f"[*] Output file: {computed_output}")
    o(f"[*] Using default lookup file: {'yes' if used_default_lookup else 'no'}")
    o(f"[*] AI support enabled: {'yes' if args.ai_support else 'no'}\n\r")

    # parse nmap xml
    hosts = list(parse_nmap_xml(args.input))
    if not hosts:
        print('No hosts with open ports found in the Nmap XML.')
        return

    all_services = {p['service'] for h in hosts for p in h['ports'] if p['service']}

    # ---- Option: generate AI modules first (your moved sequence) ----
    ai_modules = None
    if args.ai_support:
        # DO NOT keep real keys in code. Replace with env var or config.
        ai_modules = generate_ai_modules(all_services, 'AIzaSyBfIbqkLpHsxZdubj-_IVk-t2OOPKw47r4')
        # import pprint
        # pprint.pprint(ai_modules)

    # ---- load lookup from disk (will include ai_lookup.json if it exists) ----
    lookup = load_lookup(lookup_path, ai_support=args.ai_support)

    # If we have freshly returned ai_modules, merge them into the in-memory lookup
    if ai_modules:
        if lookup is None:
            # no module_lookup.json on disk — start from AI results (normalize)
            lookup = {}
        # Normalize AI keys and merge (lowercase)
        for svc, mods in ai_modules.items():
            svc_lower = svc.lower()
            existing = lookup.get(svc_lower, [])
            # append modules from AI if they're not already present
            for mod in mods:
                if mod not in existing:
                    existing.append(mod)
            lookup[svc_lower] = existing

    if lookup is None:
        print(f"[!] No modules found in lookup file: {lookup_path}. Please create or populate '{default_lookup}' and try again.")
        return


    if args.interactive:
        interactive_select_modules(hosts,lookup)


    # ---- proceed to write .rc ----
    out = write_rc(hosts, lookup, computed_output)
    print(f'Wrote .rc to: {out}')


if __name__ == '__main__':
    main()
