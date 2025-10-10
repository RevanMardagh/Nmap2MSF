from typing import Dict, List, Generator
import xml.etree.ElementTree as ET


def parse_nmap_xml(xml_path: str) -> Generator[Dict, None, None]:
    """Parse Nmap XML and yield host dicts:
    {"ip": "x.x.x.x", "ports": [{"port": int, "protocol": "tcp", "service": "ftp", "product": "..."}, ...]}
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    for host in root.findall('host'):
        # prefer ipv4/v6 address elements with addrtype
        ip = None
        for addr in host.findall('address'):
            addrtype = addr.get('addrtype', '')
            if addrtype in ('ipv4', 'ipv6'):
                ip = addr.get('addr')
                break
        if not ip:
            continue

        ports_node = host.find('ports')
        if ports_node is None:
            continue

        ports = []
        for port in ports_node.findall('port'):
            state = port.find('state')
            if state is None or state.get('state') != 'open':
                continue
            try:
                portid = int(port.get('portid'))
            except Exception:
                continue
            protocol = port.get('protocol', 'tcp')
            svc = port.find('service')
            service = svc.get('name') if svc is not None and svc.get('name') else ''
            product = svc.get('product') if svc is not None and svc.get('product') else ''
            version = svc.get('version') if svc is not None and svc.get('version') else ''
            ports.append({'port': portid, 'protocol': protocol, 'service': service.lower(), 'product': product, 'version': version})

        if ports:
            yield {'ip': ip, 'ports': ports}


if __name__ == '__main__':
    hosts = list(parse_nmap_xml('../test xml files/out2.xml'))
    print(hosts, "\n\n\r\r")

    import pprint
    pprint.pprint(hosts)