import argparse
from libs.nmap_parser import parse_nmap_xml
from libs.module_lookup import load_lookup
from libs.rc_writer import write_rc


def main():
    p = argparse.ArgumentParser(description='Generate Metasploit .rc from Nmap XML (modular)')
    p.add_argument('-i', '--input', required=True, help='Nmap XML file')
    p.add_argument('-o', '--output', required=True, help='Output .rc file')
    p.add_argument('--lookup', help='Path to module_lookup.json (optional)')
    args = p.parse_args()

    lookup = load_lookup(args.lookup)
    hosts = list(parse_nmap_xml(args.input))
    if not hosts:
        print('No hosts with open ports found in the Nmap XML.')
        return
    out = write_rc(hosts, lookup, args.output)
    print(f'Wrote .rc to: {out}')


if __name__ == '__main__':
    # print('hi')
    main()

