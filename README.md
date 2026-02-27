## Introduction
reget - A secure, pattern-based text extraction tool for DevOps and security workflows.

Detect IPs, emails, secrets, timestamps, and more from logs or streams.
Built-in ReDoS protection and CI-friendly exit modes.

## Why reget?

Unlike grep:
- Pattern groups are predefined and semantically named
- Supports structured JSON output
- Built-in ReDoS protection (timeout per match)
- CI/CD friendly (--exit-on-match)

Unlike ad-hoc regex scripts:
- YAML-based rule management
- Multiple patterns in a single run
- Safe for untrusted input

## Features
- Predefined semantic patterns (IP, email, datetime, URL, key-value, etc.)
- Unlimited patterns can be added in the config file
- Multiple pattern matching in a single run
- ReDoS-safe: per-regex timeout protection
- CI/CD ready: fail pipelines on sensitive matches
- Human-readable or structured JSON output
- Stream-friendly: works with stdin (e.g., tail -f)

## Environment
- Python: >=3.10.9
- GLIBC: >=2.14
Prebuilt binary is compiled on CentOS 7 for maximum glibc compatibility.

For Fedora 30+, install libxcrypt-compat to get libcrypt.so.1:
  ``sudo dnf install libxcrypt-compat``

## Config file
- Windows: `base_dir / 'reget.yaml'`
- Linux: `/etc/reget/reget.yaml`

## Build
```bash
pyinstaller --onefile --clean --strip --add-data "reget.yaml:." --name reget reget.py
```

## Arguments
```text
positional arguments:
  file                  Input file to process (default: stdin)


pattern selection:
  --list-patterns       List all available pattern names and descriptions

  --init-config         Copy the built-in configuration file to the specified path.

  --pattern, -p PATTERN
                        Comma-separated list of predefined pattern names to match.
                        Built-in patterns:
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
                        original context. Only available with --output=summary.

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
  $ reget --pattern kvc --exit-on-match ./src/

  # Output matched URLs as JSON for further processing
  $ reget --pattern url --output json app.log | jq '.url[]'

  # Highlight matched IPs in real-time log stream
  $ tail -f /var/log/nginx/access.log | reget --pattern ipv4 --highlight

  # Use custom regex to match AWS keys temporarily
  $ reget --custom aws_key:"AKIA[0-9A-Z]{16}" --exit-on-match .

  # Process large log file with memory mapping
  $ reget --pattern datetime --large --stat huge.log
```