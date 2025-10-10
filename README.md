# ReconPipe
Generate Metasploit scripts to automate enumeration from Nmap XML outputs


---

## Features

- Parse Nmap XML and extract hosts, open ports, and service details.
- Map services to Metasploit modules using a configurable lookup.
- Generate `.rc` scripts for automatic execution.
- Optional interactive mode to approve modules before adding them.
- Optional AI-assisted suggestions (generate candidate modules as JSON).
- Colorized console output and clear logs for easy review.
- Small, modular database meant for scalability and customizability.

---

## Usage

```bash
python main.py -i nmap_out.xml -o msf_file.rc 
```

---

## Options

- `-h, --help` Display help information
- `-i, --input <xml file>` 
- `-o, --output <file>`
- `-s, --ai-support` Grab more modules from Gemini
- `-c, --interactive` Choose each module manually

- `--lookup <json file>` Manually select the JSON database of modules

---

~ Ravan 