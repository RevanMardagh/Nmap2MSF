import argparse
import os
from libs.nmap_parser import parse_nmap_xml
from libs.module_lookup import load_lookup
from libs.rc_writer import write_rc


def main():
    p = argparse.ArgumentParser(description='Generate Metasploit .rc from Nmap XML (modular)')
    p.add_argument('-i', '--input', required=True, help='Nmap XML file')
    p.add_argument('-o', '--output', required=False, help='Output .rc file')
    p.add_argument('--lookup', help='Path to module_lookup.json (optional)')
    args = p.parse_args()


    if args.output:
        output = args.output
    else:
        output = f"{os.path.splitext(os.path.basename(args.input))[0]}.rc"
        print(output)

    print(args.input)

    # Determine lookup path: use provided one if given, otherwise default to module_lookup.json
    default_lookup = 'libs/module_lookup.json'
    lookup_path = args.lookup if args.lookup else default_lookup

    # If user provided a path but it doesn't exist, fall back to the default and inform the user
    if args.lookup and not os.path.exists(args.lookup):
        print(f"[i] Provided lookup file '{args.lookup}' not found — falling back to default: {default_lookup}")
        lookup_path = default_lookup

    # Load the lookup; load_lookup returns None when file is missing or empty
    lookup = load_lookup(lookup_path)
    if lookup is None:
        print(f"[!] No modules found in lookup file: {lookup_path}. Please create or populate '{default_lookup}' and try again.")
        return

    hosts = list(parse_nmap_xml(args.input))
    if not hosts:
        print('No hosts with open ports found in the Nmap XML.')
        return
    out = write_rc(hosts, lookup, output)
    print(f'Wrote .rc to: {out}')



if __name__ == '__main__':
    # print('hi')
    main()

