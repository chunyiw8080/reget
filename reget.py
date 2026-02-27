#!/usr/bin/env python3
import sys
import argparse

from utils import Colors, DEFAULT_TIMEOUT, list_patterns
from config import load_config
from patterns import compile_patterns_from_config, compile_custom_patterns
from output import format_summary_output, format_json_output
from processor import process_input

def disable_other_args(args, allowed_args):
    for arg in vars(args):
        if arg not in allowed_args:
            value = getattr(args, arg)
            if isinstance(value, bool):
                setattr(args, arg, False)
            elif value is not None:
                setattr(args, arg, None)

def main():
    Colors.disable()

    parser = argparse.ArgumentParser(
        description='''
reget - A secure, pattern-based text extraction tool.

Extract structured data from logs, configs, or streams using predefined or custom regex patterns.

Features:
  • Predefined patterns for common formats (IP, email, datetime, etc.)
  • ReDoS-safe: automatic timeout protection for regex matching
  • Multiple output formats: human-readable summary or JSON
  • CI/CD ready: --exit-on-match for pipeline gating
  • Configurable via /etc/reget/reget.yaml

Repository: https://github.com/chunyiw8080/reget
Config Path: 
  • Linux: /etc/reget/reget.yaml
  • Windows: ./reget.yaml (same directory as executable)

exit codes:
  0   Success, no matches found (or matches found without --exit-on-match)
  1   Match found with --exit-on-match enabled
  2   Configuration or runtime error
  130 User interrupted (Ctrl+C)
        ''',
        prog="reget",
        add_help=True,
        usage=argparse.SUPPRESS,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''
examples:
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
'''
    )
    parser.add_argument('file', nargs='?', type=argparse.FileType('r', encoding='utf-8'), 
                        default=sys.stdin, help='input file (file path or stdin)')
    parser.add_argument('--pattern', '-p', default='',
                        help='''Comma-separated list of predefined pattern names to match.
Available patterns:
    • Network: ipv4, ipv6, mac, url
    • Contact: email, phone
    • Time: date, datetime, time
    • Path: posix_path, windows_path
    • Key-Value: kve (key=value), kvc (key:value)
Example: --pattern ipv4,email,url
                        ''')
    parser.add_argument('--custom', '-c', 
                        action='append', 
                        default=[],
                        help='''Temporary custom regex pattern without modifying config. Can be specified multiple times.
Format: --custom name:"regex_pattern"
                        ''')
    parser.add_argument('--highlight', '-H', 
                        action='store_true',
                        help='''Highlight matched text with ANSI colors while preserving original context. 
Only available with --output=summary.
                        ''')
    parser.add_argument('--large', '-l', 
                        action='store_true',
                        help='''Use memory-mapped I/O (mmap) for reading large files. 
Reduces memory usage when processing GB-scale logs.
                        ''')
    parser.add_argument('--output', '-o', 
                        choices=['summary', 'json'], 
                        default='summary',
                        help='''Format for matched results
Default: summary (human-readable). Available options: json
Note: --highlight is auto-disabled for json/yaml output.
                        ''')
    parser.add_argument('--unique', '-u', 
                        action='store_true',
                        help='''Output each matched value only once (deduplicate results).
                        ''')
    parser.add_argument('--stat', '-s', 
                        action='store_true',
                        help='''Print match statistics after processing. 
Only available with --output=summary. Mutually exclusive with --exit-on-match.
                        ''')
    parser.add_argument('--exit-on-match', '-e', 
                        action='store_true',
                        help='''Exit immediately with status code 1 when any match is found.
Mutually exclusive with --stat.
                        ''')
    parser.add_argument('--timeout', '-t', 
                        type=float, 
                        default=DEFAULT_TIMEOUT, 
                        help='''Maximum time in seconds for a single regex match operation. 
Range: 0.1-30.0.
                        ''')
    parser.add_argument('--list-patterns', action='store_true',
                    help='List all available pattern names and descriptions')
    
    args = parser.parse_args()

    # args conflicts handling
    if args.output == 'json' and args.highlight:
        print("Note: --highlight only supports summary output format, automatically disabled.", file=sys.stderr)
        args.highlight = False
    
    if args.exit_on_match and args.stat:
        print("Note: --exit-on-match and --stat are mutually exclusive, --stat automatically disabled.", file=sys.stderr)
        args.stat = False

    config = load_config()

    if args.list_patterns:
        config_paterns = list_patterns(config)
        disable_other_args(args, allowed_args=['list-patterns'])
        if config_paterns:
            print(f"Available patterns\n{config_paterns}")
            sys.exit(0)
        else:
            print("No patterns found in configuration", file=sys.stderr)
            sys.exit(2)
    
    # collect all patterns to apply
    all_patterns = []
    
    if args.pattern:
        if not config:
            print("Error: --pattern specified but no config file found.", file=sys.stderr)
            sys.exit(2)
        pattern_names = [name.strip() for name in args.pattern.split(',') if name.strip()]
        all_patterns.extend(compile_patterns_from_config(config, pattern_names))
    
    if args.custom:
        all_patterns.extend(compile_custom_patterns(args.custom, args.timeout))
        
    if not all_patterns:
        print("Error: No matching patterns specified (use --pattern or --custom)", file=sys.stderr)
        sys.exit(2)

    # 3. process input
    input_source = args.file
    if args.large:
        # mmap only used for real file paths, not stdin or pipes
        if args.file is sys.stdin or getattr(args.file, 'name', '').startswith('<'):
            print("Note: --large only supports direct file paths (not stdin), automatically disabled.", file=sys.stderr)
            args.large = False
        else:
            path = args.file.name
            try:
                args.file.close()
            except Exception:
                pass
            from utils import mmap_lines
            input_source = mmap_lines(path)

    results = process_input(
        input_source,
        all_patterns,
        args.timeout,
        args.output,
        args.unique,
        args.highlight,
        args.exit_on_match
    )

    # 4. 格式化并输出结果
    # 如果存在hightlight参数，禁用格式化输出
    if args.output == 'summary' and not args.highlight:
        output_text = format_summary_output(results)
        if output_text:
            print(output_text)
        
        if args.stat:
            print("\n--- statistics ---", file=sys.stderr)
            for name, matches in results.items():
                if matches:
                    print(f"{name}: {len(matches)}", file=sys.stderr)
                    
    elif args.output == 'json':
        print(format_json_output(results, args.unique))
        

    sys.exit(0)


if __name__ == '__main__':
    main()
