## Introduction
reget - A secure, pattern-based text extraction tool for DevOps and security workflows.

Extract structured data from logs, configs, or streams using predefined or custom regex patterns.
Built with ReDoS protection (configurable timeout) and YAML-based pattern management.

### Features
- Predefined patterns for common formats (IP, email, datetime, etc.)
- ReDoS-safe: automatic timeout protection for regex matching
- Multiple output formats: human-readable summary, JSON, or YAML
- CI/CD ready: --exit-on-match for pipeline gating
- Configurable via /etc/reget/reget.yaml or ./default.yaml

### Environment
- Python: 3.12.2
- GLIBC: 2.14+

## Build
```bash
pyinstaller --onefile --clean --strip --add-data "default.yaml:." --name reget reget.py
```

## Usage
```text
usage: reget [-h] [--pattern PATTERN] [--custom CUSTOM] [--highlight]
             [--stat] [--unique] [--output {summary,json,yaml}]
             [--timeout TIMEOUT] [--large] [--exit-on-match]
             [file]
```

## Arguments
```text
positional arguments:
  file                  Input file to process (default: stdin)


pattern selection:
  --pattern, -p PATTERN
                        Comma-separated list of predefined pattern names to match.
                        Available patterns:
                          -> Network: ipv4, ipv6, mac, url
                          -> Contact: email, phone
                          -> Time: date, datetime, time
                          -> Path: posix_path, windows_path
                          -> Key-Value: kve (key=value), kvc (key:value)
                        Example: --pattern ipv4,email,url

  --custom, -c CUSTOM   Temporary custom regex pattern without modifying config.
                        Format: --custom name:"regex_pattern"
                        Can be specified multiple times.
                        Example: --custom aws_key:"AKIA[0-9A-Z]{16}"

output control:
  --highlight, -H       Highlight matched text with ANSI colors while preserving
                        original line context. Only available with --output=summary.

  --stat, -s            Print match statistics after processing.
                        Only available with --output=summary. Mutually exclusive with --exit-on-match.

  --unique, -u          Output each matched value only once (deduplicate results).

  --output, -o {summary,json}
                        Format for matched results (default: summary).
                          -> summary: Human-readable grouped output (default)
                          -> json: Machine-readable JSON object
                        Note: --highlight is auto-disabled for json output.


performance & safety:
  --timeout, -t TIMEOUT
                        Maximum time in seconds for a single regex match operation
                        to prevent ReDoS attacks (default: 0.5). Range: 0.1-30.0.

  --large, -l           Use memory-mapped I/O (mmap) for reading large files.
                        Reduces memory usage when processing GB-scale logs.

  --exit-on-match, -e   Exit immediately with status code 1 when any match is found.
                        Designed for CI/CD security gates (e.g., block commits with secrets).
                        Mutually exclusive with --stat.


general:
  -h, --help            Show this help message and exit.
```

## Example
```bash
  # Extract IPv4 and email addresses from a log file
  $ reget --pattern ipv4,email access.log

  # Scan for secrets in codebase, fail CI if found
  $ reget --pattern secret_kv --exit-on-match ./src/

  # Output matched URLs as JSON for further processing
  $ reget --pattern url --output json app.log | jq '.url[]'

  # Highlight matched IPs in real-time log stream
  $ tail -f /var/log/nginx/access.log | reget --pattern ipv4 --highlight

  # Use custom regex to match AWS keys temporarily
  $ reget --custom aws_key:"AKIA[0-9A-Z]{16}" --exit-on-match .

  # Process large log file with memory mapping
  $ reget --pattern datetime --large --stat huge.log
```